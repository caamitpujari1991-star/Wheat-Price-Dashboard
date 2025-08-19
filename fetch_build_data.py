# fetch_build_data.py
"""
Fetch yields (FAOSTAT bulk) and (optionally) producer prices.
Outputs:
 - data/yields.csv
 - data/prices.csv  (may be partial if country producer prices missing)
"""
import os
import requests
import zipfile, io
import pandas as pd
from datetime import datetime

# Config
OUTDIR = "data"
os.makedirs(OUTDIR, exist_ok=True)
YEARS = list(range(2015, datetime.now().year + 1))   # 2015..current year
COUNTRIES = ["Uzbekistan", "Kazakhstan", "Russian Federation"]
# FAOSTAT item names (exact names used in FAOSTAT bulk CSV)
ITEMS = {
    "Wheat": "Wheat",
    "Barley": "Barley",
    # for cotton: FAO often uses "Seed cotton, unginned" (check your FAOSTAT bulk file for exact name)
    "Cotton (seed)": "Seed cotton, unginned"
}

# 1) Download FAOSTAT bulk: Production_Crops_E_All_Data_(Normalized).zip
prod_url = "http://fenixservices.fao.org/faostat/static/bulkdownloads/Production_Crops_E_All_Data_(Normalized).zip"
print("Downloading FAOSTAT production bulk (this can be ~100MB)...")
r = requests.get(prod_url, stream=True, timeout=120)
r.raise_for_status()
z = zipfile.ZipFile(io.BytesIO(r.content))
# find CSV filename inside
csv_name = [n for n in z.namelist() if n.endswith(".csv") and "Production_Crops" in n][0]
print("Found", csv_name)
prod_df = pd.read_csv(z.open(csv_name), encoding='utf-8')
print("Loaded production rows:", len(prod_df))

# 2) Filter: Years, Countries, Items
prod_df = prod_df[prod_df['Area'].isin(COUNTRIES)]
prod_df = prod_df[prod_df['Item'].isin(ITEMS.values())]
prod_df = prod_df[prod_df['Year'].between(min(YEARS), max(YEARS))]

# 3) Keep relevant cols and pivot
prod_df = prod_df[['Area','Item','Year','Value','Unit']]
# FAOSTAT production file contains multiple elements; to ensure you have 'Production' & 'Area harvested' etc,
# you may need to load the "Production" dataset (this CSV is usually production in tonnes)
# If the CSV contains multiple 'Element' types, filter Element values for 'Production' and for 'Area harvested' separately.
# The normalized file sometimes has rows where 'Element' is present - check columns:
if 'Element' in prod_df.columns:
    print("Elements found in production file; filtering for Production & Area harvested")
    # for safety, reload full bulk "Production_Crops_E_All_Data_(Normalized)" which includes Element column
    zcsv = pd.read_csv(z.open(csv_name), encoding='utf-8')
    zcsv = zcsv[zcsv['Area'].isin(COUNTRIES)]
    zcsv = zcsv[zcsv['Item'].isin(ITEMS.values())]
    zcsv = zcsv[zcsv['Year'].between(min(YEARS), max(YEARS))]
    # Keep Production and Area harvested and yield (if provided)
    keep = zcsv[zcsv['Element'].isin(['Production','Area harvested','Yield'])]
    df = keep.copy()
else:
    # If Element is absent, treat Value as production. (rare)
    df = prod_df.copy()

# Reshape to have Production & Area & Year per row
# If Element exists -> pivot by Element
if 'Element' in df.columns:
    pivot = df.pivot_table(index=['Area','Item','Year'], columns='Element', values='Value').reset_index()
    # Standardize column names
    pivot = pivot.rename(columns={'Area':'Country','Item':'Crop', 'Area harvested':'Area_ha','Production':'Production_t','Yield':'Yield_t_per_ha'})
    # FAOSTAT sometimes units: '1000 Ha' or 'tonnes' - convert if needed
else:
    pivot = df.rename(columns={'Area':'Country','Item':'Crop','Value':'Production_t'})

# Normalize units: attempt to detect units column if present
# Many FAOSTAT normalized files have units embedded - user may need to convert
# For safety, compute yield = production / area if both present
if 'Area_ha' in pivot.columns and 'Production_t' in pivot.columns:
    pivot['Yield_t_per_ha'] = pivot['Production_t'] / pivot['Area_ha']

# Filter crops to our canonical names and map back
pivot['Crop'] = pivot['Crop'].replace({v:k for k,v in ITEMS.items()})

# Keep only desired columns
out = pivot[['Country','Crop','Year','Area_ha','Production_t','Yield_t_per_ha']].copy()
out['Source'] = 'FAOSTAT_Production_Bulk'

# Save yields CSV
yields_csv = os.path.join(OUTDIR, "yields.csv")
out.to_csv(yields_csv, index=False)
print("Wrote yields:", yields_csv)

# 4) TRY producer prices - FAOSTAT has a separate 'Prices' bulk (may be sparse)
prices_url = "http://fenixservices.fao.org/faostat/static/bulkdownloads/Prices_E_All_Data_(Normalized).zip"
try:
    print("Downloading FAOSTAT producer prices bulk...")
    r2 = requests.get(prices_url, stream=True, timeout=120)
    r2.raise_for_status()
    z2 = zipfile.ZipFile(io.BytesIO(r2.content))
    prices_csv_name = [n for n in z2.namelist() if n.endswith(".csv") and "Prices" in n][0]
    price_df = pd.read_csv(z2.open(prices_csv_name), encoding='utf-8')
    price_df = price_df[price_df['Area'].isin(COUNTRIES)]
    price_df = price_df[price_df['Item'].isin(ITEMS.values())]
    price_df = price_df[price_df['Year'].between(min(YEARS), max(YEARS))]
    # Keep typical producer price elements (Price received by producers)
    price_df = price_df[['Area','Item','Year','Value','Unit','Element']]
    # pivot or rename as appropriate
    price_df = price_df.rename(columns={'Area':'Country','Item':'Crop','Value':'Price','Unit':'Price_unit','Element':'Element'})
    price_df.to_csv(os.path.join(OUTDIR,'prices_faostat_raw.csv'), index=False)
    print("Saved raw FAOSTAT prices (may be sparse).")
except Exception as e:
    print("FAOSTAT prices download failed or not available:", e)
    # We'll write an empty prices CSV for now and the Streamlit app will show missing values
    empty_prices = pd.DataFrame(columns=['Country','Crop','Year','Price','Price_unit','Element','Source'])
    empty_prices.to_csv(os.path.join(OUTDIR,'prices.csv'), index=False)

print("Finished. Please check data/ folder. If prices are incomplete you can (A) add manual price columns, or (B) use TradingEconomics (code for that can be added).")

