# Wildfire data

| Item | Details |
| --- | --- |
| Source | USDA Forest Service, FPA FOD, seventh edition |
| Coverage | U.S. reported wildfires, 1992–2024 |
| Format | Zipped ESRI file geodatabase; no ArcGIS installation needed |
| Classroom scope | California by default; source archive remains nationwide |
| One row | One wildfire occurrence record |
| Preparation | Download and extraction only; no supplied cleaning or aggregation |

[Download the national archive](https://data.fs.usda.gov/geodata/edw/edw_resources/fc/S_USA.Fire_FPA_FOD_7th_Fires.gdb.zip)
· [Dataset citation and metadata](https://doi.org/10.2737/RDS-2013-0009.7)
· [USDA field reference](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer/0)

Run `uv run python download_wildfire.py` from the repository root. Keep the
extracted `.gdb` folder intact. `data/raw/wildfire_source.json` records the URL,
archive size, SHA-256, and local path. Large downloaded files are ignored by Git
and are not included in the student ZIP.

The notebook loads selected source fields with `pyogrio`, without geometry.
It retains latitude and longitude. The provided state filter selects the
classroom scope; it does not clean the selected records. Set `STATE = None`
only if you want to load the national table and have sufficient memory.

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
