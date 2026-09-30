"""Apply the agreed California wildfire cleaning rules.

This script never modifies the source CSV or the notebook. It writes a typed
Parquet analysis table, a CSV audit log, and a JSON validation report in the
same ``outputs`` directory.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "raw" / "wildfire_raw.csv"
OUTPUT_DIR = ROOT / "outputs"
CLEAN_PATH = OUTPUT_DIR / "fires_clean.parquet"
AUDIT_PATH = OUTPUT_DIR / "cleaning_audit.csv"
REPORT_PATH = OUTPUT_DIR / "cleaning_validation.json"

EXPECTED_COLUMNS = [
    "OBJECTID", "FOD_ID", "FPA_ID", "SOURCE_SYSTEM_TYPE", "SOURCE_SYSTEM",
    "NWCG_REPORTING_AGENCY", "NWCG_REPORTING_UNIT_ID",
    "NWCG_REPORTING_UNIT_NAME", "SOURCE_REPORTING_UNIT",
    "SOURCE_REPORTING_UNIT_NAME", "LOCAL_FIRE_REPORT_ID",
    "LOCAL_INCIDENT_ID", "FIRE_CODE", "FIRE_NAME",
    "ICS_209_PLUS_INCIDENT_JOIN_ID", "ICS_209_PLUS_COMPLEX_JOIN_ID",
    "MTBS_ID", "MTBS_FIRE_NAME", "COMPLEX_NAME", "FIRE_YEAR",
    "DISCOVERY_DATE", "DISCOVERY_DOY", "DISCOVERY_TIME",
    "NWCG_CAUSE_CLASSIFICATION", "NWCG_GENERAL_CAUSE",
    "NWCG_CAUSE_AGE_CATEGORY", "CONT_DATE", "CONT_DOY", "CONT_TIME",
    "FIRE_SIZE", "FIRE_SIZE_CLASS", "LATITUDE", "LONGITUDE",
    "OWNER_DESCR", "STATE", "COUNTY", "FIPS_CODE", "FIPS_NAME",
    "GLOBALID",
]

IDENTIFIER_COLUMNS = [
    "OBJECTID", "FOD_ID", "FPA_ID", "NWCG_REPORTING_UNIT_ID",
    "SOURCE_REPORTING_UNIT", "LOCAL_FIRE_REPORT_ID", "LOCAL_INCIDENT_ID",
    "FIRE_CODE", "ICS_209_PLUS_INCIDENT_JOIN_ID",
    "ICS_209_PLUS_COMPLEX_JOIN_ID", "MTBS_ID", "FIPS_CODE", "GLOBALID",
]


def scalar_text(value: object) -> object:
    """Return an audit-friendly scalar while preserving missing values."""
    if pd.isna(value):
        return pd.NA
    if isinstance(value, pd.Timestamp):
        return value.isoformat(sep=" ")
    return str(value)


def expected_size_class(size: pd.Series) -> pd.Series:
    result = pd.Series(pd.NA, index=size.index, dtype="string")
    rules = [
        ((size > 0) & (size <= 0.25), "A"),
        ((size > 0.25) & (size < 10), "B"),
        ((size >= 10) & (size < 100), "C"),
        ((size >= 100) & (size < 300), "D"),
        ((size >= 300) & (size < 1_000), "E"),
        ((size >= 1_000) & (size < 5_000), "F"),
        (size >= 5_000, "G"),
    ]
    for mask, label in rules:
        result.loc[mask.fillna(False)] = label
    return result


def parse_timestamp_without_date_shift(values: pd.Series) -> pd.Series:
    # The export uses offsets such as +00:00. Converting to UTC and then
    # dropping the timezone preserves the displayed source calendar date.
    parsed = pd.to_datetime(values, format="mixed", errors="coerce", utc=True)
    return parsed.dt.tz_localize(None)


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Missing source file: {SOURCE}")

    parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(
        SOURCE,
        chunksize=100_000,
        dtype="string",
        keep_default_na=False,
        na_values=[""],
    ):
        parts.append(chunk.loc[chunk["STATE"] == "CA"].copy())

    fires = pd.concat(parts, ignore_index=True)
    if fires.columns.tolist() != EXPECTED_COLUMNS:
        raise ValueError("Source columns do not match the expected 39-column schema")

    source_missing_counts = {column: int(count) for column, count in fires.isna().sum().items()}
    source_whitespace_only_counts = {
        column: int((fires[column].notna() & fires[column].str.strip().eq("").fillna(False)).sum())
        for column in fires.columns
    }
    source_fips_trimmed = fires["FIPS_CODE"].str.strip().copy()
    original_ids = fires["FOD_ID"].copy()
    audit_frames: list[pd.DataFrame] = []

    def add_audit(
        mask: pd.Series | np.ndarray,
        column: str,
        original: pd.Series,
        cleaned: pd.Series,
        rule: str,
        issue: str | pd.Series = "",
    ) -> None:
        selected = pd.Series(mask, index=fires.index).fillna(False).astype(bool)
        if not selected.any():
            return
        if isinstance(issue, pd.Series):
            issue_values = issue.loc[selected].astype("string")
        else:
            issue_values = pd.Series(issue, index=fires.index, dtype="string").loc[selected]
        audit_frames.append(
            pd.DataFrame(
                {
                    "FOD_ID": fires.loc[selected, "FOD_ID"].astype("string"),
                    "column": column,
                    "original_value": original.loc[selected].map(scalar_text).astype("string"),
                    "cleaned_value": cleaned.loc[selected].map(scalar_text).astype("string"),
                    "rule": rule,
                    "unresolved_issue": issue_values,
                }
            )
        )

    # Normalize external padding only. Internal spelling, punctuation, and case
    # stay unchanged except for the single agreed OWNER_DESCR correction.
    for column in fires.columns:
        before = fires[column].copy()
        after = before.str.strip().mask(before.str.strip().eq(""), pd.NA)
        changed = before.notna() & ~before.eq(after).fillna(False)
        fires[column] = after
        add_audit(changed, column, before, after, "trim_outer_whitespace")

    owner_before = fires["OWNER_DESCR"].copy()
    owner_mask = owner_before.eq("Private")
    fires.loc[owner_mask, "OWNER_DESCR"] = "PRIVATE"
    add_audit(
        owner_mask,
        "OWNER_DESCR",
        owner_before,
        fires["OWNER_DESCR"],
        "normalize_private_category",
    )

    # Explicit typed conversions. Failed conversions are retained as audit
    # issues rather than causing rows to be dropped.
    integer_columns = ["FIRE_YEAR", "DISCOVERY_DOY", "CONT_DOY"]
    raw_integer: dict[str, pd.Series] = {}
    for column in integer_columns:
        before = fires[column].copy()
        raw_integer[column] = before
        numeric = pd.to_numeric(before, errors="coerce")
        non_integral = numeric.notna() & numeric.mod(1).ne(0)
        converted = numeric.mask(non_integral).astype("Int64")
        failure = before.notna() & converted.isna()
        fires[column] = converted
        add_audit(
            failure,
            column,
            before,
            fires[column],
            "convert_nullable_integer",
            "conversion failed; original value retained in audit",
        )

    raw_numeric: dict[str, pd.Series] = {}
    for column in ["FIRE_SIZE", "LATITUDE", "LONGITUDE"]:
        before = fires[column].copy()
        raw_numeric[column] = before
        converted = pd.to_numeric(before, errors="coerce")
        failure = before.notna() & converted.isna()
        fires[column] = converted
        add_audit(
            failure,
            column,
            before,
            fires[column],
            "convert_numeric",
            "conversion failed; original value retained in audit",
        )

    raw_dates: dict[str, pd.Series] = {}
    for column in ["DISCOVERY_DATE", "CONT_DATE"]:
        before = fires[column].copy()
        raw_dates[column] = before
        converted = parse_timestamp_without_date_shift(before)
        failure = before.notna() & converted.isna()
        fires[column] = converted
        add_audit(
            failure,
            column,
            before,
            fires[column],
            "parse_timestamp_without_calendar_shift",
            "date conversion failed; original value retained in audit",
        )

    # Exact recovery rules. They only fill genuinely missing values and never
    # overwrite a contradictory populated value.
    discovery_date = fires["DISCOVERY_DATE"]
    year_before = fires["FIRE_YEAR"].copy()
    year_fill = year_before.isna() & discovery_date.notna()
    fires.loc[year_fill, "FIRE_YEAR"] = discovery_date.loc[year_fill].dt.year.astype("Int64")
    add_audit(year_fill, "FIRE_YEAR", year_before, fires["FIRE_YEAR"], "recover_year_from_discovery_date")

    doy_before = fires["DISCOVERY_DOY"].copy()
    doy_fill = doy_before.isna() & discovery_date.notna()
    fires.loc[doy_fill, "DISCOVERY_DOY"] = discovery_date.loc[doy_fill].dt.dayofyear.astype("Int64")
    add_audit(doy_fill, "DISCOVERY_DOY", doy_before, fires["DISCOVERY_DOY"], "recover_doy_from_discovery_date")

    date_before = fires["DISCOVERY_DATE"].copy()
    date_missing_in_source = raw_dates["DISCOVERY_DATE"].isna()
    components_ready = fires["FIRE_YEAR"].notna() & fires["DISCOVERY_DOY"].notna()
    candidate_text = (
        fires["FIRE_YEAR"].astype("string")
        + fires["DISCOVERY_DOY"].astype("string").str.zfill(3)
    )
    recovered_date = pd.to_datetime(candidate_text, format="%Y%j", errors="coerce")
    date_fill = date_missing_in_source & date_before.isna() & components_ready & recovered_date.notna()
    fires.loc[date_fill, "DISCOVERY_DATE"] = recovered_date.loc[date_fill]
    add_audit(date_fill, "DISCOVERY_DATE", date_before, fires["DISCOVERY_DATE"], "recover_date_from_year_and_doy")

    cont_doy_before = fires["CONT_DOY"].copy()
    cont_doy_fill = cont_doy_before.isna() & fires["CONT_DATE"].notna()
    fires.loc[cont_doy_fill, "CONT_DOY"] = fires.loc[cont_doy_fill, "CONT_DATE"].dt.dayofyear.astype("Int64")
    add_audit(cont_doy_fill, "CONT_DOY", cont_doy_before, fires["CONT_DOY"], "recover_doy_from_containment_date")

    size_class_before = fires["FIRE_SIZE_CLASS"].copy()
    expected_class = expected_size_class(fires["FIRE_SIZE"])
    class_fill = size_class_before.isna() & expected_class.notna()
    fires.loc[class_fill, "FIRE_SIZE_CLASS"] = expected_class.loc[class_fill]
    add_audit(class_fill, "FIRE_SIZE_CLASS", size_class_before, fires["FIRE_SIZE_CLASS"], "recover_size_class_from_acres")

    county_pairs = fires[["FIPS_CODE", "FIPS_NAME"]].dropna().drop_duplicates()
    code_counts = county_pairs.groupby("FIPS_CODE")["FIPS_NAME"].nunique()
    verified_code_map = (
        county_pairs[county_pairs["FIPS_CODE"].isin(code_counts[code_counts.eq(1)].index)]
        .set_index("FIPS_CODE")["FIPS_NAME"]
        .to_dict()
    )
    fips_name_before = fires["FIPS_NAME"].copy()
    mapped_name = fires["FIPS_CODE"].map(verified_code_map).astype("string")
    fips_name_fill = fips_name_before.isna() & mapped_name.notna()
    fires.loc[fips_name_fill, "FIPS_NAME"] = mapped_name.loc[fips_name_fill]
    add_audit(fips_name_fill, "FIPS_NAME", fips_name_before, fires["FIPS_NAME"], "recover_fips_name_from_verified_code")

    # Review flags and contradiction checks.
    for column, original in raw_integer.items():
        conversion_failure = original.notna() & fires[column].isna()
        # Already recorded above; this branch intentionally adds no duplicate.
        del conversion_failure

    year_issue = fires["FIRE_YEAR"].notna() & ~fires["FIRE_YEAR"].between(1992, 2024)
    add_audit(year_issue, "FIRE_YEAR", raw_integer["FIRE_YEAR"], fires["FIRE_YEAR"], "validate_year_range", "outside 1992-2024")

    discovery_year_mismatch = (
        fires["DISCOVERY_DATE"].notna()
        & fires["FIRE_YEAR"].notna()
        & fires["DISCOVERY_DATE"].dt.year.ne(fires["FIRE_YEAR"])
    )
    add_audit(discovery_year_mismatch, "DISCOVERY_DATE", raw_dates["DISCOVERY_DATE"], fires["DISCOVERY_DATE"], "validate_discovery_year", "discovery date year conflicts with FIRE_YEAR")

    discovery_doy_mismatch = (
        fires["DISCOVERY_DATE"].notna()
        & fires["DISCOVERY_DOY"].notna()
        & fires["DISCOVERY_DATE"].dt.dayofyear.ne(fires["DISCOVERY_DOY"])
    )
    add_audit(discovery_doy_mismatch, "DISCOVERY_DOY", raw_integer["DISCOVERY_DOY"], fires["DISCOVERY_DOY"], "validate_discovery_doy", "DISCOVERY_DOY conflicts with discovery date")

    cont_doy_mismatch = (
        fires["CONT_DATE"].notna()
        & fires["CONT_DOY"].notna()
        & fires["CONT_DATE"].dt.dayofyear.ne(fires["CONT_DOY"])
    )
    add_audit(cont_doy_mismatch, "CONT_DOY", raw_integer["CONT_DOY"], fires["CONT_DOY"], "validate_containment_doy", "CONT_DOY conflicts with containment date")

    containment_before_discovery = (
        fires["CONT_DATE"].notna()
        & fires["DISCOVERY_DATE"].notna()
        & fires["CONT_DATE"].dt.normalize().lt(fires["DISCOVERY_DATE"].dt.normalize())
    )
    add_audit(containment_before_discovery, "CONT_DATE", raw_dates["CONT_DATE"], fires["CONT_DATE"], "validate_date_order", "containment date is before discovery date")

    invalid_time_counts: dict[str, int] = {}
    for column in ["DISCOVERY_TIME", "CONT_TIME"]:
        values = fires[column].astype("string")
        valid = (
            values.str.fullmatch(r"\d{4}", na=False)
            & pd.to_numeric(values.str[:2], errors="coerce").lt(24)
            & pd.to_numeric(values.str[2:], errors="coerce").lt(60)
        )
        invalid = values.notna() & ~valid
        invalid_time_counts[column] = int(invalid.sum())
        add_audit(invalid, column, values, values, "validate_local_hhmm", "invalid four-digit local time")

    non_midnight_discovery = (
        fires["DISCOVERY_DATE"].notna()
        & (
            fires["DISCOVERY_DATE"].dt.hour.ne(0)
            | fires["DISCOVERY_DATE"].dt.minute.ne(0)
            | fires["DISCOVERY_DATE"].dt.second.ne(0)
        )
    )
    add_audit(non_midnight_discovery, "DISCOVERY_DATE", raw_dates["DISCOVERY_DATE"], fires["DISCOVERY_DATE"], "preserve_non_midnight_timestamp", "timestamp contains clock information; do not infer local DISCOVERY_TIME")

    invalid_size = fires["FIRE_SIZE"].isna() | ~np.isfinite(fires["FIRE_SIZE"]) | fires["FIRE_SIZE"].le(0)
    add_audit(invalid_size, "FIRE_SIZE", raw_numeric["FIRE_SIZE"], fires["FIRE_SIZE"], "validate_positive_acres", "acreage is missing, non-finite, or non-positive")

    class_mismatch = expected_class.notna() & fires["FIRE_SIZE_CLASS"].notna() & expected_class.ne(fires["FIRE_SIZE_CLASS"])
    add_audit(class_mismatch, "FIRE_SIZE_CLASS", size_class_before, fires["FIRE_SIZE_CLASS"], "validate_size_class", "size class conflicts with reported acreage")

    lat_invalid = fires["LATITUDE"].isna() | ~np.isfinite(fires["LATITUDE"]) | ~fires["LATITUDE"].between(-90, 90)
    lon_invalid = fires["LONGITUDE"].isna() | ~np.isfinite(fires["LONGITUDE"]) | ~fires["LONGITUDE"].between(-180, 180)
    add_audit(lat_invalid, "LATITUDE", raw_numeric["LATITUDE"], fires["LATITUDE"], "validate_latitude", "latitude is missing, non-finite, or outside -90..90")
    add_audit(lon_invalid, "LONGITUDE", raw_numeric["LONGITUDE"], fires["LONGITUDE"], "validate_longitude", "longitude is missing, non-finite, or outside -180..180")

    coordinate_review = (
        ~lat_invalid
        & ~lon_invalid
        & (~fires["LATITUDE"].between(32.5, 42.01) | ~fires["LONGITUDE"].between(-124.5, -114))
    )
    coordinate_text = raw_numeric["LATITUDE"].astype("string") + ", " + raw_numeric["LONGITUDE"].astype("string")
    add_audit(coordinate_review, "LATITUDE,LONGITUDE", coordinate_text, coordinate_text, "broad_california_coordinate_screen", "coordinates fall outside the review box; no reassignment or deletion made")

    state_issue = fires["STATE"].ne("CA") | fires["STATE"].isna()
    add_audit(state_issue, "STATE", fires["STATE"], fires["STATE"], "validate_california_scope", "STATE is not CA")

    county_normalized = (
        fires["COUNTY"].astype("string").str.strip().str.replace(r"\s+County$", "", regex=True, case=False).str.casefold()
    )
    fips_name_normalized = (
        fires["FIPS_NAME"].astype("string").str.strip().str.replace(r"\s+County$", "", regex=True, case=False).str.casefold()
    )
    county_numeric = pd.to_numeric(fires["COUNTY"], errors="coerce")
    fips_suffix = pd.to_numeric(fires["FIPS_CODE"].astype("string").str[-3:], errors="coerce")
    county_match = county_normalized.eq(fips_name_normalized) | (
        county_numeric.notna() & fips_suffix.notna() & county_numeric.eq(fips_suffix)
    )
    county_discrepancy = fires["COUNTY"].notna() & fires["FIPS_NAME"].notna() & ~county_match.fillna(False)
    county_compare = fires["COUNTY"].astype("string") + " | " + fires["FIPS_NAME"].astype("string")
    add_audit(county_discrepancy, "COUNTY,FIPS_NAME", county_compare, county_compare, "compare_reported_county_to_fips", "reported county label conflicts with source FIPS name")

    duplicate_key = ["DISCOVERY_DATE", "LATITUDE", "LONGITUDE", "FIRE_SIZE"]
    possible_duplicate = fires.duplicated(duplicate_key, keep=False)
    duplicate_values = fires[duplicate_key].astype("string").agg(" | ".join, axis=1)
    add_audit(possible_duplicate, ",".join(duplicate_key), duplicate_values, duplicate_values, "possible_duplicate_review", "shared date, coordinates, and acreage do not prove duplicate reporting")

    placeholders = {"NA", "N/A", "UNNAMED"}
    for column in fires.select_dtypes(include=["string"]).columns:
        placeholder_mask = fires[column].str.upper().isin(placeholders)
        add_audit(placeholder_mask, column, fires[column], fires[column], "preserve_ambiguous_placeholder", "literal placeholder retained for review")

    globalid_valid = fires["GLOBALID"].str.fullmatch(
        r"\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}",
        na=False,
    )
    add_audit(~globalid_valid, "GLOBALID", fires["GLOBALID"], fires["GLOBALID"], "validate_globalid", "missing or invalid braced UUID")

    objectid_valid = fires["OBJECTID"].str.fullmatch(r"\d+", na=False)
    add_audit(~objectid_valid, "OBJECTID", fires["OBJECTID"], fires["OBJECTID"], "validate_objectid", "missing or non-digit OBJECTID")

    source_type_issue = ~fires["SOURCE_SYSTEM_TYPE"].isin(["FED", "NONFED", "INTERAGCY"])
    add_audit(source_type_issue, "SOURCE_SYSTEM_TYPE", fires["SOURCE_SYSTEM_TYPE"], fires["SOURCE_SYSTEM_TYPE"], "validate_source_system_type", "unexpected source-system type")

    # Stable ordering makes the outputs reproducible and easy to compare.
    audit = (
        pd.concat(audit_frames, ignore_index=True)
        if audit_frames
        else pd.DataFrame(columns=["FOD_ID", "column", "original_value", "cleaned_value", "rule", "unresolved_issue"])
    )
    audit = audit.sort_values(["FOD_ID", "column", "rule"], kind="stable", ignore_index=True)

    duplicate_id_counts = {
        column: int(fires[column].duplicated(keep=False).sum())
        for column in ["OBJECTID", "FOD_ID", "FPA_ID", "GLOBALID"]
    }
    missing_id_counts = {column: int(fires[column].isna().sum()) for column in IDENTIFIER_COLUMNS[:3] + ["GLOBALID"]}
    fips_pair_count = int(fires[["FIPS_CODE", "FIPS_NAME"]].dropna().drop_duplicates().shape[0])
    unresolved = audit["unresolved_issue"].fillna("").ne("")
    changes = audit["unresolved_issue"].fillna("").eq("") & ~audit["original_value"].eq(audit["cleaned_value"]).fillna(False)

    expected_total = 25_622_806.7449
    acreage_total = float(fires["FIRE_SIZE"].sum())
    missing_county_total = float(fires.loc[fires["FIPS_CODE"].isna(), "FIRE_SIZE"].sum())
    reported_county_total = float(fires.loc[fires["FIPS_CODE"].notna(), "FIRE_SIZE"].sum())
    output_missing_counts = {column: int(count) for column, count in fires.isna().sum().items()}
    missingness_changes = {
        column: output_missing_counts[column] - source_missing_counts[column]
        for column in fires.columns
        if output_missing_counts[column] != source_missing_counts[column]
    }

    unit_agency_counts = fires.groupby("NWCG_REPORTING_UNIT_ID")["NWCG_REPORTING_AGENCY"].nunique()
    source_unit_name_counts = fires.groupby(
        ["SOURCE_SYSTEM", "SOURCE_REPORTING_UNIT"], dropna=False
    )["SOURCE_REPORTING_UNIT_NAME"].nunique()
    mtbs_name_counts = (
        fires.dropna(subset=["MTBS_ID"])
        .groupby("MTBS_ID")["MTBS_FIRE_NAME"]
        .nunique(dropna=True)
    )
    fips_name_counts = county_pairs.groupby("FIPS_NAME")["FIPS_CODE"].nunique()

    boundary_sizes = pd.Series(
        [0.0001, 0.25, 0.250001, 9.999999, 10, 99.999999, 100, 299.999999,
         300, 999.999999, 1_000, 4_999.999999, 5_000],
        dtype="Float64",
    )
    boundary_expected = pd.Series(
        ["A", "A", "B", "B", "C", "C", "D", "D", "E", "E", "F", "F", "G"],
        dtype="string",
    )
    boundary_checks_pass = bool(expected_size_class(boundary_sizes).equals(boundary_expected))

    report = {
        "source": str(SOURCE),
        "clean_table": str(CLEAN_PATH),
        "audit_log": str(AUDIT_PATH),
        "rows": int(len(fires)),
        "columns": int(fires.shape[1]),
        "same_fod_ids_and_order": bool(original_ids.equals(fires["FOD_ID"])),
        "acreage_total": acreage_total,
        "acreage_expected": expected_total,
        "acreage_within_tolerance": math.isclose(acreage_total, expected_total, rel_tol=0, abs_tol=1e-6),
        "missing_county_acreage_total": missing_county_total,
        "reported_county_acreage_total": reported_county_total,
        "county_totals_reconcile_to_statewide": math.isclose(
            missing_county_total + reported_county_total,
            acreage_total,
            rel_tol=0,
            abs_tol=1e-6,
        ),
        "duplicate_identifier_row_counts": duplicate_id_counts,
        "missing_identifier_counts": missing_id_counts,
        "missingness": {
            "source_empty_field_counts": source_missing_counts,
            "source_whitespace_only_counts": source_whitespace_only_counts,
            "clean_table_counts": output_missing_counts,
            "net_changes_clean_minus_source": missingness_changes,
            "all_missingness_reductions_match_recoveries": bool(
                all(
                    source_missing_counts[column] - output_missing_counts[column]
                    == {
                        "FIRE_YEAR": int(year_fill.sum()),
                        "DISCOVERY_DOY": int(doy_fill.sum()),
                        "DISCOVERY_DATE": int(date_fill.sum()),
                        "CONT_DOY": int(cont_doy_fill.sum()),
                        "FIRE_SIZE_CLASS": int(class_fill.sum()),
                        "FIPS_NAME": int(fips_name_fill.sum()),
                    }.get(column, 0)
                    for column in fires.columns
                    if output_missing_counts[column] < source_missing_counts[column]
                )
            ),
        },
        "source_system_count": int(fires["SOURCE_SYSTEM"].nunique(dropna=True)),
        "reporting_unit_ids_with_multiple_names": int(
            (fires.groupby("NWCG_REPORTING_UNIT_ID")["NWCG_REPORTING_UNIT_NAME"].nunique() > 1).sum()
        ),
        "reporting_unit_ids_with_multiple_agencies": int(unit_agency_counts.gt(1).sum()),
        "source_system_unit_pairs_with_multiple_names": int(source_unit_name_counts.gt(1).sum()),
        "mtbs_ids_with_multiple_populated_names": int(mtbs_name_counts.gt(1).sum()),
        "missing_fire_names_with_mtbs_name": int(
            (fires["FIRE_NAME"].isna() & fires["MTBS_FIRE_NAME"].notna()).sum()
        ),
        "fips_code_name_pair_count": fips_pair_count,
        "fips_names_with_multiple_codes": int(fips_name_counts.gt(1).sum()),
        "fips_codes_unchanged_except_outer_whitespace": bool(
            source_fips_trimmed.equals(fires["FIPS_CODE"])
        ),
        "populated_fips_codes_are_five_digits": bool(
            fires["FIPS_CODE"].dropna().str.fullmatch(r"\d{5}").all()
        ),
        "county_discrepancy_rows": int(county_discrepancy.sum()),
        "possible_duplicate_rows": int(possible_duplicate.sum()),
        "non_midnight_discovery_rows": int(non_midnight_discovery.sum()),
        "discovery_year_mismatch_rows": int(discovery_year_mismatch.sum()),
        "discovery_doy_mismatch_rows": int(discovery_doy_mismatch.sum()),
        "containment_doy_mismatch_rows": int(cont_doy_mismatch.sum()),
        "containment_before_discovery_rows": int(containment_before_discovery.sum()),
        "invalid_time_rows": invalid_time_counts,
        "invalid_or_nonpositive_fire_size_rows": int(invalid_size.sum()),
        "size_class_mismatch_rows": int(class_mismatch.sum()),
        "size_class_boundary_tests_pass": boundary_checks_pass,
        "coordinate_review_rows": int(coordinate_review.sum()),
        "invalid_latitude_rows": int(lat_invalid.sum()),
        "invalid_longitude_rows": int(lon_invalid.sum()),
        "unexpected_source_system_type_rows": int(source_type_issue.sum()),
        "invalid_globalid_rows": int((~globalid_valid).sum()),
        "invalid_objectid_rows": int((~objectid_valid).sum()),
        "value_change_audit_rows": int(changes.sum()),
        "unresolved_issue_audit_rows": int(unresolved.sum()),
        "audit_rows": int(len(audit)),
        "recovery_counts": {
            "FIRE_YEAR": int(year_fill.sum()),
            "DISCOVERY_DOY": int(doy_fill.sum()),
            "DISCOVERY_DATE": int(date_fill.sum()),
            "CONT_DOY": int(cont_doy_fill.sum()),
            "FIRE_SIZE_CLASS": int(class_fill.sum()),
            "FIPS_NAME": int(fips_name_fill.sum()),
        },
        "dtype_summary": {column: str(dtype) for column, dtype in fires.dtypes.items()},
        "repeatability_checks": {
            "no_remaining_outer_whitespace": bool(
                all(
                    fires[column].dropna().eq(fires[column].dropna().str.strip()).all()
                    for column in fires.select_dtypes(include=["string"]).columns
                )
            ),
            "no_remaining_owner_private_variant": bool(not fires["OWNER_DESCR"].eq("Private").any()),
            "no_remaining_approved_recovery_opportunities": bool(
                not (
                    (fires["FIRE_YEAR"].isna() & fires["DISCOVERY_DATE"].notna()).any()
                    or (fires["DISCOVERY_DOY"].isna() & fires["DISCOVERY_DATE"].notna()).any()
                    or (fires["CONT_DOY"].isna() & fires["CONT_DATE"].notna()).any()
                    or (fires["FIRE_SIZE_CLASS"].isna() & expected_size_class(fires["FIRE_SIZE"]).notna()).any()
                    or (fires["FIPS_NAME"].isna() & fires["FIPS_CODE"].map(verified_code_map).notna()).any()
                )
            ),
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fires.to_parquet(CLEAN_PATH, index=False)
    audit.to_csv(AUDIT_PATH, index=False)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({key: report[key] for key in [
        "rows", "columns", "acreage_total", "acreage_within_tolerance",
        "value_change_audit_rows", "unresolved_issue_audit_rows", "audit_rows",
    ]}, indent=2))


if __name__ == "__main__":
    main()
