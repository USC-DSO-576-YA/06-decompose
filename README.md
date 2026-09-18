# Module 6 — Repeatable Analytics Workflows

DSO 576 · YA

Monday: repeat familiar pandas work across regions and monthly files; trace a
condition-controlled inventory calculation. Wednesday: build a cleaning script
with the instructor, one approved step at a time.

## AI help

Personal AI help in this repo is **hints-only**, including Wednesday: short context
reminders, one hint at a time, and feedback on your attempt—not completed code or
answers. The instructor-led demonstration is separate. See [tutor.md](tutor.md)
and [AGENTS.md](AGENTS.md). After updating your clone, start a new Codex session
from this repo to load the instructions.

## Start

Open a terminal in this folder. The same commands work in Terminal and PowerShell.

```text
uv sync
uv run python monday.py
uv run python wednesday.py
```

The starter files load data only. Add the code developed in class. Keep the data
files unchanged. Generated files belong in `outputs/`; keep the folder's `.gitkeep`.
Running your script again may replace its generated files, not the source data.

If you received a ZIP, extract it so the folder is `~/dso576/06-repeat`.
If you cloned the course copy, work locally and commit locally. Do not push to
the shared course repository. Follow the handout for exercises and submission.

## Data

The four practice CSVs are fictional teaching data. The additional
`data/11-ralphs_sales.csv.gz` is the instructor-supplied Ralphs dataset,
preserved unchanged in its original compressed format.
Read `data/README.md` for the source definitions and loading instructions.
These datasets are separate activities; do not join or append them together.
