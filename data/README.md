# Wildfire data

| Item | Details |
| --- | --- |
| Source | USDA Forest Service, FPA FOD, seventh edition |
| Coverage | U.S. reported wildfires, 1992–2024 |
| Format | Zipped ESRI file geodatabase; no ArcGIS installation needed |
| Classroom scope | Load all states, then select California in the notebook |
| One row | One wildfire occurrence record |
| Preparation | Download, extraction, and a full CSV export; no cleaning or filtering |

[Download the national archive](https://data.fs.usda.gov/geodata/edw/edw_resources/fc/S_USA.Fire_FPA_FOD_7th_Fires.gdb.zip)
· [Dataset citation and metadata](https://doi.org/10.2737/RDS-2013-0009.7)
· [USDA field reference](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer/0)

Run `uv run python download_wildfire.py` from the repository root. Keep the
extracted `.gdb` folder intact. `data/raw/wildfire_source.json` records the URL,
archive size, SHA-256, and local path. Large downloaded files are ignored by Git
and are not included in the student ZIP.

The supplied script creates `data/raw/wildfire_raw.csv` with **all 2,661,383
records**, all 38 attribute fields, and the source `OBJECTID`. The archive has
one table, so no merge or concat is needed. No records are removed, filled,
relabeled, deduplicated, or aggregated. Geometry stays in the original `.gdb`;
latitude and longitude are included in the CSV.

The notebook loads all fields as text to preserve codes and reported values.
Empty CSV fields are read as missing. Numeric and date conversions are left
for class. The last loading step selects California into `ca`, keeping all
columns. `raw` stays nationwide. The fields below are examples used in class;
they are not a limit on the columns loaded.

## Fields used in class

Names below use the geodatabase's uppercase field names.

| Field | Meaning |
| --- | --- |
| `FOD_ID` | Source record identifier |
| `FIRE_NAME` | Reported fire name; may be missing |
| `FIRE_YEAR`, `DISCOVERY_DATE` | Year and date the fire was discovered |
| `CONT_DATE` | Containment date, when reported |
| `FIRE_SIZE` | Final reported fire size in acres |
| `FIRE_SIZE_CLASS` | Source size category |
| `NWCG_CAUSE_CLASSIFICATION` | Broad cause classification |
| `NWCG_GENERAL_CAUSE` | More detailed cause category |
| `STATE`, `COUNTY` | State abbreviation and reported county value |
| `FIPS_CODE`, `FIPS_NAME` | County code and name; retain codes as identifiers |
| `LATITUDE`, `LONGITUDE` | Reported point location in decimal degrees |

USDA has already standardized and checked the records and removed duplicates
where possible. Inspect the actual data before deciding what needs cleaning.
Missing or uncertain fields can remain. Record counts reflect available reports,
not every fire that occurred. Historical occurrence is not a forecast of risk.
Point locations are not burned-area perimeters. Summed `FIRE_SIZE` is reported
fire acreage; it is not necessarily unique land area burned.
