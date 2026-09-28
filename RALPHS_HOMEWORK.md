# Module 6 Homework

## Clean the Ralphs sales data

Prepare a reusable sales table from the Ralphs grocery csv. The goal is to
extract useful information from messy text, choose appropriate data types, and
check that your cleaning rules preserve the meaning of the source data.

Work individually in one Jupyter notebook named `module06_ralphs.ipynb`. Use
short code cells, with a brief explanation before each cleaning step. This
assignment does not require charts, a dashboard, or phrase mining.

**Submission:** Upload `module06_ralphs.ipynb` to the Module 6 homework
assignment on Gradescope. Follow the posted course calendar for the deadline.

### Data and setup

The data is in your [YA Module 6 repository](https://github.com/USC-DSO-576-YA/06-decompose),
at `data/11-ralphs_sales.csv.gz`. Save your notebook in the top-level
`06-decompose` folder, beside the `data` folder, so the relative path below works.
This starter loads the source as strings so you can inspect the original text:

```python
import pandas as pd

raw = pd.read_csv("data/11-ralphs_sales.csv.gz", dtype="string")
```

### Using Codex

You may use Codex for hints, explanations, and feedback on code you have tried.
Do not ask it to complete the notebook, write a finished cleaning function for
you. Before asking for help, write what you expected it to do. If you cannot
get started, first describe the intended transformation in plain language.
Ask about one step at a time.

For example: “Here is my attempt and the output I expected. Give me one hint
about why it does not work.”

### 1 Inspect before changing anything

Display the first few rows, the column names, the number of rows, and the
number of distinct non-missing values in each column. Inspect the distinct
values in `Geography` and several examples from `Time` and `Product`.

Before using Codex, write brief answers to these questions:

- What does one row represent? Use the geography, reporting period, and product
  information in your answer.
- Which fields contain numbers stored as text? Which number-looking field is
  actually an identifier?
- Show one raw description and explain which pieces you expect to extract.

### 2 Clean dates and sales amounts

Create these columns in `sales`:

| Column | Required meaning and representation |
| --- | --- |
| `Week Ending` | Date following “Ending” in `Time`, converted to a pandas datetime value. |
| `Description` | A lowercase version of the raw `Product` description. |
| `Dollar Sales` | Numeric sales revenue, with currency formatting removed. |
| `Unit Sales` | Numeric number of packages sold. |

Inspect the actual formatting before choosing a cleaning rule. After converting
each numeric or date column, count missing results and inspect any raw values
that could not be converted. Report zero if there are no failures. Do not
replace an unsuccessful conversion with zero.

### 3 Separate packaging from the product description

Create `Packaging` from the description. The original exercise uses `bag`,
`canister`, and `assorted`; inspect how those words appear in this file before
writing your rule. Keep unmatched or ambiguous cases missing and report them.

Create a Series named `prefix` containing the description before the packaging
information. Remove packaging modifiers such as `plastic` and `resealable`
from that boundary, without deleting meaningful words elsewhere in a product
description. Remove leftover surrounding whitespace.

Display five distinct examples with their `Description`, `Packaging`, and
`prefix`. Include an example with a packaging modifier if one is present.

### 4 Separate product family and flavor

Use `prefix` to create `Product` and `Flavor`. Here, `Product` means the brand
and product family together, not just the brand. For example:

| Prefix | Product | Flavor |
| --- | --- | --- |
| `doritos tortilla chip nacho cheese` | `doritos tortilla chip` | `nacho cheese` |
| `lays potato chip classic` | `lays potato chip` | `classic` |
| `cheetos cheese snack flamin hot` | `cheetos cheese snack` | `flamin hot` |

Inspect the distinct prefixes and write down the product-family boundaries
your code recognizes. Apply the same rules to every row, rather than manually
editing individual records. Do not assume the first word is always the full
product family or that the last word is always the full flavor.

Display five distinct results. Report how many rows your rules could not
confidently separate, and show up to three examples. Keep those uncertain
fields missing; do not invent a product or flavor to make the table complete.
A documented limitation is preferable to a confident but incorrect split.

### 5 Extract identifiers and package sizes

Create these additional columns:

- `Product Code`: the identifier after the final hyphen in `Description`.
  Keep it as a string, including leading zeros. It is not a measurement.
- `Oz`: the numeric package size explicitly expressed in ounces in the
  description. Your rule must handle integers, decimals such as `9.75`, and
  decimals written without a leading zero, such as `.75`.
- `Price Per Oz`: average dollars paid per ounce sold for that record.

Use this definition for the last column:

```text
Price Per Oz = Dollar Sales / (Unit Sales * Oz)
```

Only calculate it when revenue is present and both unit sales and package
size are present and greater than zero. Otherwise leave the result missing.
Do not fill unknown package sizes with zero or a typical size. If a description
does not support one unambiguous package weight, flag it for review and explain
why you did not infer a value.

Report how many rows have missing `Oz` and how many have missing `Price Per Oz`.
Inspect examples rather than assuming that every missing result is a mistake.

### 6 Show that the cleaning worked

Include the following evidence in your notebook:

1. **Preserved records:** show the source and cleaned row counts and confirm
   that they agree. Show the data type and missing-value count of every output
   column. Explain any unexpected missing values.
2. **Three source checks:** choose three different records: an ordinary package,
   a decimal package size, and a record with a missing or ambiguous size. If the
   last category is absent, choose a packaging-modifier example instead.
   Display the full raw `Product` and `Time` beside the relevant cleaned fields.
   Write what the values should be by reading the source yourself, then compare
   with your code's output. Identify the records so another person can find them.
3. **One independent calculation:** for a valid record, show the raw revenue,
   units, and ounces. Calculate price per ounce yourself, using a calculator if
   needed, and compare it with your computed column. Explain why dividing only
   by ounces would give the wrong quantity.
4. **One limitation:** describe a real case your rules cannot confidently
   resolve, or a boundary case you tested successfully. State how you handled
   it and what additional information would resolve any uncertainty.

The checks and explanations must be your own. A second AI response saying the
code is correct is not independent verification.

### Finish and submit

Sort by `Week Ending` ascending, then `Dollar Sales` descending. Reset the index
with `drop=True`. Display the first ten rows of the final table, using these
ten columns:

```text
Week Ending, Description, Dollar Sales, Unit Sales, Packaging,
Product, Flavor, Product Code, Oz, Price Per Oz
```

Save `sales` locally as `06-cleaned_sales.csv` without the DataFrame index.
Restart the notebook kernel, run all cells in order, and save the notebook
with its outputs visible.

At the end, include a short assistance note: what you asked Codex, one useful
hint or correction, and how you checked the resulting change. If you did not
use Codex, say so. You do not need to submit a full chat transcript.

Submit **one file**, `module06_ralphs.ipynb`, to the **Module 6 homework assignment
on Gradescope**. It must include your code, outputs, source checks, explanations,
and assistance note. The exported CSV is generated by the notebook and does not
need a separate upload. Follow the posted course calendar for the deadline.
