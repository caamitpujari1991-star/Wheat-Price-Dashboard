# Wheat Market Dashboard (Streamlit) + Google Looker Studio Kit

This package gives you two ways to monitor and time wheat sales:

1) **Streamlit Web App** (ready to deploy on Streamlit Cloud or any server).  
2) **Google Looker Studio Dashboard** (fed by a Google Sheet + Apps Script).

---

## 1) Streamlit App — Quick Start

### A) Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
The app loads sample data from `data/` so you can see charts immediately. Replace these CSVs or connect to your own sources.

### B) Deploy free on Streamlit Cloud
1. Create a **new GitHub repo** and upload everything in this folder.  
2. Go to **share.streamlit.io** → **New app** → select your repo and set **Main file path** to `app.py`.  
3. Add the environment variable `NEWS_FEEDS` (optional JSON list of RSS URLs).  
4. Click **Deploy** → You get a public link.

### Data you can replace
- `data/prices_sample.csv` — weekly UZEX, FOB Black Sea, CPT prices.  
  - Columns: `date,country,market,price_uzs_per_t,price_usd_per_t` (use either one per row).  
- `data/production_sample.csv` — 2024/25 actual vs 2025/26 estimates.  
- `data/signals_sample.csv` — dated events like "export duty change".

### Live news
By default, the app reads RSS feeds from a few sources. You can add more by setting the `NEWS_FEEDS` environment variable to a JSON array (see app sidebar).

---

## 2) Google Looker Studio Dashboard (Online Link)

### A) Create a Google Sheet with 4 tabs
- **Prices** → Columns: `date, country, market, price_uzs_per_t, price_usd_per_t`  
- **Production** → `country, marketing_year, production_thousand_t, yield_t_per_ha`  
- **Signals** → `date, signal, severity` (1=low, 2=medium, 3=high)  
- **News** → `pub_date, title, source, url`

### B) Add the Apps Script (for news automation)
1. In the Sheet, Extensions → **Apps Script**.  
2. Create a script file **Code.gs** and paste the contents from `google/Code.gs` in this package.  
3. In the script, adjust the `FEEDS` list to the RSS you want.  
4. Run `refreshNews()` once and grant permissions.  
5. Setup a **time-based trigger** (e.g., hourly/daily) for `refreshNews`.

> Prices & Production: either paste weekly values manually OR connect to your database/API and write to the sheet. The dashboard will update automatically.

### C) Build the Looker Studio report
1. Open **lookerstudio.google.com** → **Blank report**.  
2. **Add data** → **Google Sheets** → select your sheet and the 4 tabs.  
3. Create these visuals:
   - **Line chart**: Wheat prices (select country/market filters).  
   - **Bar/column**: Production by country (2024/25 vs 2025/26).  
   - **Table**: Signals (sorted by date, severity color).  
   - **Table** with clickable link: News (title → url).
4. Click **Share** to get a **public link**.

---

## Notes
- Sample numbers are placeholders so charts render immediately. Replace them with your live data.  
- For UZEX prices, paste the weekly averages you track.  
- For Russian/Black Sea benchmarks, you can paste from your subscription/assessments.  
- Always comply with terms of use of any data provider.

