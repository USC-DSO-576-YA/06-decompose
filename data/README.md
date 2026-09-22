# Data definitions

The four practice CSVs described below are fictional, created for this module.
The additional Ralphs archive is a separate instructor-supplied dataset.

## Monday monthly files

`sales_jan.csv`, `sales_feb.csv`, `sales_mar.csv`: eight orders per file.
One row is one order. `order_id` uniquely identifies an order across the files;
`region` is a non-missing label from West, East, South, North; `amount` is numeric
USD sales before refunds. Filenames and region labels are safe for the classroom
export example. The files share the same schema and do not overlap.

## Wednesday weekly export

`weekly_sales_messy.csv`: 24 records for the week ending September 13, 2026.
One row is a product's sales at one retailer for that week. Products have distinct
codes even when their descriptions are similar. Do not deduplicate on description.

- `record_id`: stable source-row identifier.
- `week_ending`: reporting date, already in ISO format; no date cleaning required.
- `product_code`: text identifier; leading zeros are meaningful.
- `description`: exported product text, including package information.
- `dollar_sales`: USD revenue for the row, not a price for one unit. Source text
  contains dollar signs, thousands separators, and unknown-value placeholders.
- `unit_sales`: number of sellable packages sold; some values may be absent.

Package size is ounces per sellable package. For example, a single 8 oz package
has size 8. A multipack description needs a separate interpretation rule. Dates,
brands, flavors, and product-code parsing are not tasks in this exercise.

## Additional Ralphs dataset

`11-ralphs_sales.csv.gz` is the original instructor-supplied file, kept unchanged.
The `11-` prefix belongs to its original filename; this repository is Module 6.
It is additional material, not a replacement for `weekly_sales_messy.csv` in
the current guided exercise. Inspect its columns and values before adapting
the cleaning rules; the practice dataset's answers do not apply to this file.

The moved Ralphs homework uses this file in `module06_ralphs.ipynb` at the
repository root. See `../RALPHS_HOMEWORK.md` for the full homework instructions.
The archive is byte-for-byte identical to the copy formerly in Module 5.

Read the compressed CSV directly with pandas (no manual extraction needed):

```python
import pandas as pd

ralphs = pd.read_csv("data/11-ralphs_sales.csv.gz", dtype="string")
print(ralphs.head())
```
