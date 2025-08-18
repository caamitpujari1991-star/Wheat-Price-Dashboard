import streamlit as st
import requests
import pandas as pd
import datetime
import os

# Load API key from secrets
API_KEY = st.secrets["API_NINJA_KEY"]
BASE_URL = "https://api.api-ninjas.com/v1"

headers = {"X-Api-Key": API_KEY}

# Function to get live price
def get_live_price(commodity):
    url = f"{BASE_URL}/commodityprice?name={commodity}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching data: {response.text}")
        return None

# Function to get historical price
def get_historical_price(commodity, period="1d"):
    url = f"{BASE_URL}/commoditypricehistorical?name={commodity}&period={period}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching historical data: {response.text}")
        return None

# Streamlit app
st.title("📊 Commodity Price Dashboard")

commodity = st.selectbox("Choose a commodity:", 
    ["wheat", "corn", "cotton", "sugar", "coffee", "gold", "platinum"])

st.write(f"### Live Price for {commodity.capitalize()}")
live_data = get_live_price(commodity)
if live_data:
    st.metric(label="Exchange", value=live_data.get("exchange", "N/A"))
    st.metric(label="Price (USD)", value=live_data.get("price", "N/A"))
    updated_time = datetime.datetime.fromtimestamp(live_data["updated"])
    st.write(f"Last updated: {updated_time}")

st.write(f"### Historical Prices for {commodity.capitalize()}")
hist_data = get_historical_price(commodity, period="1d")

if hist_data:
    df = pd.DataFrame(hist_data)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    st.line_chart(df.set_index("time")[["open", "high", "low", "close"]])
    st.dataframe(df)
