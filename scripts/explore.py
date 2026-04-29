import pandas as pd
import os
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
df = pd.read_csv(os.path.join(DATA_DIR, "steam_store_games.csv"))
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print()
print(df.head(2).to_string())
print()
genres_col = df["genres"].dropna()
print(f"Genres unique (first 20): {genres_col.unique()[:20]}")
print(f"Price range: {df['price'].min()} - {df['price'].max()}")
print(f"Positive ratings range: {df['positive_ratings'].min()} - {df['positive_ratings'].max()}")
total = df["positive_ratings"] + df["negative_ratings"]
print(f"Rows with reviews > 0: {(total > 0).sum()}")
print(f"Owners sample: {df['owners'].unique()[:10]}")
print(f"Null counts:")
print(df.isnull().sum())
