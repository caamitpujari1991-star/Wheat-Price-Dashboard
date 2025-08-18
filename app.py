import requests
import streamlit as st
import pandas as pd
import time

# ---------- Helper to fetch prices ----------
def get_price(item):
    url = f"https://api.api-ninjas.com/v1/commodityprice?name={item}"
    headers = {"X-Api-Key": st.secrets["API_NINJA_KEY"]}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data and isinstance(data, list):
            return data[0]  # take first result
    return None

# ---------- Streamlit App ----------
st.set_page_config(page_title="Commodity Dashboard", page_icon="🌾", layout="wide")

st.title("🌾 Real-Time Commodity Price Dashboard")

# Commodities we want
commodities = ["wheat", "corn", "rice", "cotton"]

all_data = []

# Fetch each commodity
for item in commodities:
    result = get_price(item)
    time.sleep(1)  # to respect API rate limits
    if result:
        all_data.append({
            "Commodity": item.capitalize(),
            "Price": result.get("price", "N/A"),
            "Currency": result.get("currency", "USD"),
            "Date": result.get("date", "")
        })
    else:
        all_data.append({
            "Commodity": item.capitalize(),
            "Price": "Error",
            "Currency": "",
            "Date": ""
        })

# Convert to dataframe
df = pd.DataFrame(all_data)

# ---------- Show Table ----------
st.subheader("📊 Current Prices")
st.dataframe(df, use_container_width=True)

# ---------- Show Chart ----------
st.subheader("📈 Price Comparison")
try:
    st.bar_chart(df.set_index("Commodity")["Price"])
except Exception as e:
    st.error("Chart cannot be shown due to missing price data.")
