from pathlib import Path
import pandas as pd

Path('outputs').mkdir(exist_ok=True)
raw = pd.read_csv(
    'data/weekly_sales_messy.csv', dtype='string', keep_default_na=False
)
print(raw.shape)
print(raw.head())

# Add only the next step approved in class. Keep the source CSV unchanged.
