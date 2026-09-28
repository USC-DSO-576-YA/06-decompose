# Module 6 — Decompose with Codex

Clean wildfire data, plan a dashboard, and build it in class.

## Before class

Run `uv sync --frozen` in this repository in Terminal or PowerShell.
Open **[module06_wildfire.ipynb](module06_wildfire.ipynb)** in VS Code and select
this folder's `.venv` Python as the kernel. Run the supplied setup cell:

```python
from pathlib import Path
import pandas as pd
from download_wildfire import download_data

source = download_data()
```

This downloads the national USDA archive (about 259 MB), exports every record
and attribute field to `data/raw/wildfire_raw.csv`, and returns its path.
Completed files are reused. Allow about 4 GB of free disk space.
Rerun the cell if the connection fails.

The notebook loads the full table with pandas, then selects California with
`.loc[]`. It keeps all columns. The source has one table, so no merge or concat
is needed. Cleaning, type conversions, and analysis are left for class.

You can also prepare the data from Terminal or PowerShell:

```text
uv run python download_wildfire.py
```

If necessary, register the kernel with:

```text
uv run python -m ipykernel install --user --name dso576-module6 --display-name "DSO576 Module 6"
```

## In class

| Stage | Work you add |
| --- | --- |
| Inspect | Understand one record, the columns, and missing values. |
| Clean | Choose and document rules; create an analysis table. |
| Plan | Name the audience, question, metrics, filters, and charts. |
| Build | Create `dashboard.py` with Streamlit and Plotly. |
| Review | Use the handout to evaluate your results. |

The notebook contains the loader, short instructions, and blank work cells.
Cleaning code, a completed plan, and dashboard code are intentionally left for
class. Preserve the source data. Save generated files in `outputs/`.

After creating the dashboard in class, run:

```text
uv run streamlit run dashboard.py
```

See [data/README.md](data/README.md) for the source and field definitions.
Follow the handout for the class tasks. This activity adds no separate upload.
Work and commit locally; do not push to the shared course repository.

## Codex help

Use Codex for hints, explanations, and feedback on your attempt. Work one step
at a time; you write the analysis and dashboard code. See [AGENTS.md](AGENTS.md)
and [tutor.md](tutor.md). The instructor may demonstrate Codex edits separately.

For new, ungraded pandas practice, ask:

> Read AGENTS.md and tutor.md. Give me one original Module 6 practice question
> at a time. Start with diff, shift, and cumsum. Wait for my answer before
> giving feedback or showing a solution.

You can also request mixed practice, date/string multiple-choice tracing,
merge/concat output tables, or input/output code-writing questions. Assigned
class work and homework stay hints-only; practice questions use fresh data.
