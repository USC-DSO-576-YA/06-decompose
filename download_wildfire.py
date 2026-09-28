"""Download the USDA source and prepare a California CSV for class."""

from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile
import argparse
import hashlib
import json

URL = (
    "https://data.fs.usda.gov/geodata/edw/edw_resources/fc/"
    "S_USA.Fire_FPA_FOD_7th_Fires.gdb.zip"
)
RAW_DIR = Path(__file__).resolve().parent / "data" / "raw"
LAYER = "Fire_FPA_FOD_7th_Fires"
CLASS_COLUMNS = [
    "FOD_ID", "FIRE_NAME", "FIRE_YEAR", "DISCOVERY_DATE", "CONT_DATE",
    "FIRE_SIZE", "FIRE_SIZE_CLASS", "NWCG_CAUSE_CLASSIFICATION",
    "NWCG_GENERAL_CAUSE", "STATE", "COUNTY", "FIPS_CODE", "FIPS_NAME",
    "LATITUDE", "LONGITUDE",
]


def _download_source(data_dir=RAW_DIR):
    """Return the local geodatabase path; reuse a completed download."""
    data_dir = Path(data_dir).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    ready = data_dir / "wildfire_source.json"
    if ready.exists():
        metadata = json.loads(ready.read_text(encoding="utf-8"))
        gdb = data_dir / metadata["geodatabase"]
        if gdb.is_dir() and any(gdb.glob("*.gdbtable")):
            print(f"Source already available: {gdb}")
            return gdb
        raise FileNotFoundError("Incomplete source folder. Restore it or use --data-dir with a new folder.")

    archive = data_dir / URL.rsplit("/", 1)[-1]
    last_modified = None
    if not archive.exists():
        part = archive.with_suffix(".zip.part")
        print("Downloading the national archive (about 259 MB).", flush=True)
        try:
            request = Request(URL, headers={"User-Agent": "DSO576-wildfire-class/1.0"})
            with urlopen(request, timeout=90) as response, part.open("wb") as out:
                total = int(response.headers.get("Content-Length", 0))
                last_modified = response.headers.get("Last-Modified")
                received = 0
                next_report = 25_000_000
                while block := response.read(1024 * 1024):
                    out.write(block)
                    received += len(block)
                    if received >= next_report:
                        print(f"  {received / 1_000_000:.0f} MB downloaded", flush=True)
                        next_report += 25_000_000
                if total and received != total:
                    raise IOError(f"Incomplete download: {received} of {total} bytes.")
            with ZipFile(part) as zipped:
                bad = zipped.testzip()
                if bad:
                    raise IOError(f"ZIP integrity check failed: {bad}")
            part.replace(archive)
        finally:
            part.unlink(missing_ok=True)

    destination = data_dir / "fpa_fod_7th"
    if destination.exists():
        raise FileExistsError(f"Preserving existing folder: {destination}. Use a new --data-dir.")
    print("Checking and extracting the archive...", flush=True)
    with ZipFile(archive) as zipped, TemporaryDirectory(dir=data_dir) as temp:
        temp = Path(temp)
        for item in zipped.infolist():
            if not (temp / item.filename).resolve().is_relative_to(temp):
                raise ValueError(f"Unsafe archive path: {item.filename}")
        zipped.extractall(temp)
        candidates = list(temp.rglob("*.gdb"))
        if len(candidates) != 1 or not any(candidates[0].glob("*.gdbtable")):
            raise ValueError("Expected one readable .gdb folder in the USDA archive.")
        relative_gdb = candidates[0].relative_to(temp)
        # Move only after extraction succeeds; interrupted runs can be rerun.
        extracted = temp / "completed"
        extracted.mkdir()
        for child in list(temp.iterdir()):
            if child != extracted:
                child.rename(extracted / child.name)
        extracted.rename(destination)

    digest = hashlib.sha256()
    with archive.open("rb") as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
    gdb = destination / relative_gdb
    metadata = {
        "source_url": URL,
        "edition": 7,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": digest.hexdigest(),
        "server_last_modified": last_modified,
        "geodatabase": gdb.relative_to(data_dir).as_posix(),
    }
    ready.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Ready: {gdb}\nNo cleaning or analysis has been performed.")
    return gdb


def prepare_class_csv(data_dir=RAW_DIR):
    """Export California source fields without cleaning or aggregation."""
    source = _download_source(data_dir)
    csv_path = Path(data_dir).resolve() / "wildfire_ca.csv"
    if csv_path.is_file():
        print(f"Class CSV already available: {csv_path}")
        return csv_path

    import pyogrio

    print("Preparing the California CSV...", flush=True)
    frame = pyogrio.read_dataframe(
        source, layer=LAYER, columns=CLASS_COLUMNS,
        where="STATE = 'CA'", read_geometry=False,
    )
    frame = frame.loc[:, CLASS_COLUMNS]
    part = csv_path.with_suffix(".csv.part")
    try:
        frame.to_csv(part, index=False)
        part.replace(csv_path)
    finally:
        part.unlink(missing_ok=True)
    print(f"Ready: {csv_path} ({len(frame):,} records). No cleaning performed.")
    return csv_path


def download_data(data_dir=RAW_DIR):
    """Prepare the class data and return its CSV path for pandas."""
    return prepare_class_csv(data_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=RAW_DIR)
    args = parser.parse_args()
    try:
        download_data(args.data_dir)
    except (OSError, ValueError, BadZipFile) as error:
        parser.exit(1, f"Download setup failed: {error}\nFix the connection or path and rerun.\n")
