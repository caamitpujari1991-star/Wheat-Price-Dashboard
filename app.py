# app.py
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Wheat/Cotton/Barley — Yields & Prices")

st.title("Wheat · Cotton · Barley — Yields & Prices (UZ/KZ/RU)")

@st.cache_data
def load_data():
    y = pd.read_csv("data/yields.csv")
    try:
        p = pd.read_csv("data/prices.csv")
    except:
        p = pd.DataFrame(columns=['Country','Crop','Year','Price_local','Price_usd_per_t','Price_source'])
    return y, p

yields_df, prices_df = load_data()

# Basic checks
if yields_df.empty:
    st.error("yields.csv is empty — run fetch_build_data.py first.")
    st.stop()

# Controls
countries = st.multiselect("Countries", sorted(yields_df['Country'].unique()), default=['Uzbekistan','Kazakhstan','Russian Federation'])
crops = st.multiselect("Crops", sorted(yields_df['Crop'].unique()), default=['Wheat','Barley','Cotton (seed)'])
year_min = int(yields_df['Year'].min())
year_max = int(yields_df['Year'].max())
years = st.slider("Year range", min_value=year_min, max_value=year_max, value=(year_min, year_max))

# Filters applied
df = yields_df[(yields_df['Country'].isin(countries)) & (yields_df['Crop'].isin(crops)) & 
               (yields_df['Year'].between(years[0], years[1]))]

st.subheader("Yields / Production Table")
st.dataframe(df)

# Time series: Yield
st.subheader("Yield (t/ha) — time series")
fig = px.line(df, x='Year', y='Yield_t_per_ha', color='Country', line_dash='Crop', markers=True,
              title="Yield (t/ha) by Country & Crop")
st.plotly_chart(fig, use_container_width=True)

# If prices available, show price chart
if not prices_df.empty:
    p = prices_df[(prices_df['Country'].isin(countries)) & (prices_df['Crop'].isin(crops)) & (prices_df['Year'].between(years[0], years[1]))]
    if not p.empty:
        st.subheader("Prices (USD per t)")
        if 'Price_usd_per_t' in p.columns:
            figp = px.line(p, x='Year', y='Price_usd_per_t', color='Country', line_dash='Crop', markers=True)
            st.plotly_chart(figp, use_container_width=True)
    else:
        st.info("No price data for your filters — check data/prices.csv or add TradingEconomics data.")
else:
    st.info("No prices.csv found or it is empty. The fetch script creates a placeholder if no FAOSTAT prices present.")

# Scatter: price vs yield (latest year)
st.subheader("Price vs Yield (latest available year in selection)")
latest = df['Year'].max()
df_latest = df[df['Year'] == latest]
if not df_latest.empty:
    merged = df_latest.merge(prices_df[prices_df['Year']==latest][['Country','Crop','Price_usd_per_t']], on=['Country','Crop'], how='left')
    figs = px.scatter(merged, x='Yield_t_per_ha', y='Price_usd_per_t', color='Country', size='Production_t',
                      hover_data=['Country','Crop','Production_t'], title=f'Yield vs Price — {latest}')
    st.plotly_chart(figs, use_container_width=True)
else:
    st.write("No data for latest year:", latest)

# Export cleaned CSV button
st.download_button("Download filtered yields CSV", df.to_csv(index=False).encode('utf-8'), file_name="yields_filtered.csv")

