# Module 6 — Decompose with Codex

Clean wildfire data, plan a dashboard, and build it in class.

## Before class

Run these commands from this repository in Terminal or PowerShell:

```text
uv sync --frozen
uv run python download_wildfire.py
```

The script downloads the national USDA archive (about 259 MB), extracts it to
`data/raw/`, and records the source and checksum. Allow about 2 GB of free disk
space. It reuses a completed download. It does not clean, aggregate, or chart data.
If the connection fails, rerun the command.

Open **[module06_wildfire.ipynb](module06_wildfire.ipynb)** in VS Code and select
this folder's `.venv` Python as the kernel. Run only the supplied setup and load
cells before class. The default is **California, 1992–2024**; the downloaded
archive includes all states. `STATE` controls the notebook's geographic scope.
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

## Ralphs homework

The homework remains separate: complete [module06_ralphs.ipynb](module06_ralphs.ipynb)
using [RALPHS_HOMEWORK.md](RALPHS_HOMEWORK.md). The original
`data/11-ralphs_sales.csv.gz` is included unchanged. Submit the completed Ralphs
notebook to the posted Module 6 homework assignment on Gradescope. Keep any work
already started; do not begin again. Do not combine the two datasets.
