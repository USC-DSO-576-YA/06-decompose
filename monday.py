from pathlib import Path
import pandas as pd

Path('outputs').mkdir(exist_ok=True)
sales = pd.read_csv('data/sales_jan.csv')
print(sales)

# Add the region loop and monthly-file loop from class below.
