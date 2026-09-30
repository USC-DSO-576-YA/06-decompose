# California wildfire cleaning plan

## Goal and confirmed decisions

Prepare the **California wildfire occurrence records** for analysis of reported fire acreage, covering all **39 columns**.

Confirmed choices:

- Use California records.
- Recover missing values only when existing information determines the answer unambiguously.
- Use the source’s `FIPS_CODE` and `FIPS_NAME` for county comparisons, retaining and flagging conflicting original county labels.
- Preserve the original CSV and notebook’s `ca` table.


## Findings and overall rules

The core acreage data is already complete: every California record has a positive, numeric `FIRE_SIZE`. Its current total is **25,622,806.7449 reported acres**.

The main issues are formatting, optional information, and ambiguous relationships:

- Padding spaces occur in identifiers and names.
- All three county fields are empty together in **94,797 records**. They cannot fill one another.
- Containment date and day-of-year are empty together in **121,824 records**.
- All four main identifiers are unique, including after trimming.
- **4,120 records** share discovery date, coordinates, and acreage with another record. These are review candidates, not proven duplicates.
- Twelve county labels still differ from their FIPS names after basic formatting normalization; some are abbreviations, misspellings, or multiple-county labels.

Apply these rules to a separate `fires_clean` table:

1. Retain all records and all 39 columns.
2. Trim leading and trailing whitespace. Preserve internal punctuation, spacing, and name capitalization.
3. Treat empty fields and whitespace-only strings as missing. Preserve literal strings such as `NA`, `N/A`, and `UNNAMED`; flag ambiguous placeholders instead of globally converting them.
4. Keep identifiers as text, including leading zeros.
5. Convert calendar integers, measurements, and dates explicitly. Flag conversion failures without silently deleting records.
6. Never replace existing contradictory information automatically.
7. Record every changed value and unresolved issue against `FOD_ID`.
8. Keep records with missing optional fields in acreage totals. Do not apply a blanket “drop missing rows” operation.

The source distinguishes reported county from coordinate-derived county, and local clock times from date fields. Its age category also intentionally permits null values. Preserve those meanings. [USDA field metadata](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer/0/metadata)

## Column-by-column rules

“Empty” below means an empty CSV field before cleaning, not necessarily a data defect. Fields remain text unless another type is specified.

| Column                          |   Empty | Cleaning and recovery rule                                                                                                                                      |
| ------------------------------- | ------: | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `OBJECTID`                      |       0 | Preserve as an export identifier. Validate nonmissing, unique, digit-only values; do not regenerate.                                                            |
| `FOD_ID`                        |       0 | Use as the record and audit key. Preserve and verify uniqueness.                                                                                                |
| `FPA_ID`                        |       0 | Trim padding in 41,202 values. Recheck uniqueness; do not decode it into other identifiers without documented source-specific rules.                            |
| `SOURCE_SYSTEM_TYPE`            |       0 | Preserve `FED`, `NONFED`, and `INTERAGCY`. Flag unexpected categories.                                                                                          |
| `SOURCE_SYSTEM`                 |       0 | Preserve the nine observed source codes; do not merge different reporting systems.                                                                              |
| `NWCG_REPORTING_AGENCY`         |       0 | Preserve agency codes. Check agreement with reporting-unit information; do not equate reporting agency with landowner.                                          |
| `NWCG_REPORTING_UNIT_ID`        |       0 | Preserve as text. Repeated values are expected across fires.                                                                                                    |
| `NWCG_REPORTING_UNIT_NAME`      |       0 | Preserve names. The 177 unit IDs each have one observed name; verify that relationship remains consistent.                                                      |
| `SOURCE_REPORTING_UNIT`         |       0 | Preserve source-specific codes. Interpret them within their source system.                                                                                      |
| `SOURCE_REPORTING_UNIT_NAME`    |       0 | Preserve historical names. There are 35 source-system/unit combinations with multiple names; do not force a single replacement.                                 |
| `LOCAL_FIRE_REPORT_ID`          | 214,750 | Keep text and missing values. Local report numbers are not globally unique; do not manufacture replacements.                                                    |
| `LOCAL_INCIDENT_ID`             |  64,480 | Trim padding in 78,340 values. Preserve leading zeros and missing values; repeated local IDs do not establish duplicate fires.                                  |
| `FIRE_CODE`                     | 212,432 | Preserve codes and repeated values. Flag the single literal `N/A`; do not use this field as a unique incident key.                                              |
| `FIRE_NAME`                     |  48,059 | Trim padding in 74,077 values. Preserve unnamed/unknown labels. Do not automatically substitute a complex or MTBS name.                                         |
| `ICS_209_PLUS_INCIDENT_JOIN_ID` | 278,790 | Preserve optional linkage identifiers. Repeated IDs do not justify merging occurrence records.                                                                  |
| `ICS_209_PLUS_COMPLEX_JOIN_ID`  | 281,957 | Preserve optional complex links. Never substitute them for individual-fire identifiers.                                                                         |
| `MTBS_ID`                       | 281,623 | Preserve optional perimeter linkage. Do not reconstruct it from names, coordinates, or dates.                                                                   |
| `MTBS_FIRE_NAME`                | 281,623 | Preserve the MTBS-specific name. Check that each populated MTBS ID has a consistent associated name.                                                            |
| `COMPLEX_NAME`                  | 281,852 | Trim the 21 padded values. Leave missing values missing; absence does not prove a fire was outside a complex.                                                   |
| `FIRE_YEAR`                     |       0 | Convert to nullable integer. Check 1992–2024 and agreement with discovery year.                                                                                 |
| `DISCOVERY_DATE`                |       0 | Parse the exported timestamps without shifting their calendar dates into another timezone. Preserve the three non-midnight timestamps and flag them for review. |
| `DISCOVERY_DOY`                 |       0 | Convert to nullable integer. Verify against discovery date, including leap years.                                                                               |
| `DISCOVERY_TIME`                |  45,856 | Preserve four-character local `HHMM` text. Validate 0000–2359; `0000` remains a valid recorded time. Do not infer time from midnight date values.               |
| `NWCG_CAUSE_CLASSIFICATION`     |       0 | Preserve all three categories, including 61,211 explicitly undetermined records. Do not guess a cause.                                                          |
| `NWCG_GENERAL_CAUSE`            |       0 | Preserve all 13 categories. The 118,589 undetermined values do not imply that the broader classification is also unknown.                                       |
| `NWCG_CAUSE_AGE_CATEGORY`       | 273,494 | Preserve `Minor` and null according to source semantics. Do not label nulls `Adult` or treat every null as an accidental omission.                              |
| `CONT_DATE`                     | 121,824 | Parse timestamps. Check calendar date is not before discovery. Allow containment in a later year, including 2025.                                               |
| `CONT_DOY`                      | 121,824 | Convert integral strings such as `167.0` to nullable integers. Verify against containment date; do not assume the discovery year.                               |
| `CONT_TIME`                     | 123,671 | Preserve and validate local `HHMM` text. Do not fill missing times with midnight or discovery time.                                                             |
| `FIRE_SIZE`                     |       0 | Convert to numeric acres. Preserve every positive value and its precision. Do not cap large fires, round small fires away, or estimate acreage from size class. |
| `FIRE_SIZE_CLASS`               |       0 | Preserve ordered categories A–G. Verify against acreage; current records all agree with the thresholds below.                                                   |
| `LATITUDE`                      |       0 | Convert to numeric; require finite values within −90 to 90. Preserve precision and review geographic anomalies.                                                 |
| `LONGITUDE`                     |       0 | Convert to numeric; require finite values within −180 to 180. Do not automatically reverse signs or move points.                                                |
| `OWNER_DESCR`                   |       0 | Normalize the single `Private` value to `PRIVATE`. Preserve `MISSING/NOT SPECIFIED`, `STATE OR PRIVATE`, and other distinct categories.                         |
| `STATE`                         |       0 | Require `CA` for this analysis. Preserve the reported state even when coordinates warrant review.                                                               |
| `COUNTY`                        |  94,797 | Trim whitespace and retain the original reported designation. Do not force mixed numeric codes and names into one numeric type.                                 |
| `FIPS_CODE`                     |  94,797 | Preserve five-character text, including `06`. Use as the county grouping key; verify against the 58 observed code/name pairs.                                   |
| `FIPS_NAME`                     |  94,797 | Use as the county display name. Keep an explicit “County not reported” group in summaries for missing county information.                                       |
| `GLOBALID`                      |       0 | Preserve UUID text and braces. Verify format, nonmissing values, and uniqueness; do not regenerate.                                                             |

Size-class checks use these continuous thresholds:

| Class | Reported acres                 |
| ----- | ------------------------------ |
| A     | Greater than 0 through 0.25    |
| B     | Greater than 0.25 and below 10 |
| C     | 10 through below 100           |
| D     | 100 through below 300          |
| E     | 300 through below 1,000        |
| F     | 1,000 through below 5,000      |
| G     | 5,000 or more                  |

## Exact recovery and exception handling

**Permitted recovery rules, when their prerequisites are met:**

- Recover a missing discovery year or day-of-year from a valid discovery date.
- Recover a missing discovery calendar date from a valid year and day-of-year, checking leap years. This supplies no clock time.
- Recover containment day-of-year from a valid containment date. A day-of-year alone cannot determine the containment year.
- Recover a missing size class from valid positive acreage. Never reverse this into an acreage estimate.
- Recover a missing FIPS name from a valid code using a verified, unique code/name mapping. Reverse lookup requires the state and an exact, unambiguous county name.
- Recover other descriptive labels only from a documented relationship that identifies the same entity and has one consistent value.

These checks found **no confirmed fill opportunities in the major missing date, county, or acreage fields**. Do not invent fills merely to reduce missing-value counts.

Specific exceptions:

- Eight missing fire names have an MTBS name available, but MTBS links can represent multiple occurrence records. Retain both fields without treating the alternate name as an exact replacement.
- Three discovery timestamps contain clock information while `DISCOVERY_TIME` is missing. Flag them; the exported timestamp does not establish the required local clock time.
- Preserve the 4,120 possible duplicate records pending evidence of duplicate reporting.
- Flag county discrepancies after trimming, ignoring case, removing a terminal “County,” and comparing numeric county codes with the FIPS suffix. Use the source FIPS assignment as selected.
- Use a broad coordinate screen of latitude 32.5–42.01 and longitude −124.5–−114 to identify review candidates only. It is not a California boundary test and must not trigger deletion or reassignment.
- Keep undetermined causes and missing counties visible in grouped outputs. The missing-county records account for approximately **6,314,947.892 reported acres**.

## Validation and deliverables

The cleaning specification should require:

- **Record preservation:** 283,285 rows before and after, with the same record identifiers.
- **Acreage preservation:** total remains 25,622,806.7449 acres, allowing only floating-point calculation tolerance.
- **Identifier checks:** no new missing identifiers or collisions after trimming.
- **Missingness reconciliation:** every reduction in missing values is explained by an approved recovery rule.
- **Date checks:** year/day-of-year agreement, leap-day handling, valid cross-year containment, and preservation of the three unusual timestamps.
- **Time checks:** valid four-digit clocks; unknown time stays unknown.
- **Boundary checks:** test every size-class threshold and ensure missing acreage cannot become zero.
- **County checks:** preserve leading zeros, flag the twelve nonmatching labels, and reconcile county totals—including the missing-county group—to statewide acreage.
- **Recovery checks:** conflicting lookup values, missing donor values, and shared complex/perimeter IDs must not produce automatic fills.
- **Repeatability:** a second cleaning pass makes no additional changes.
