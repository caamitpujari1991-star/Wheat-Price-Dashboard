
import os, json, datetime as dt
import pandas as pd
import numpy as np
import streamlit as st
import feedparser

st.set_page_config(page_title="Wheat Market Dashboard", layout="wide")

@st.cache_data
def load_prices(path="data/prices_sample.csv"):
    df = pd.read_csv(path, parse_dates=["date"])
    return df

@st.cache_data
def load_production(path="data/production_sample.csv"):
    return pd.read_csv(path)

@st.cache_data
def load_signals(path="data/signals_sample.csv"):
    df = pd.read_csv(path, parse_dates=["date"])
    return df

def parse_feeds(feed_urls, limit=30):
    items = []
    for url in feed_urls:
        try:
            d = feedparser.parse(url)
            for e in d.entries[:limit]:
                items.append({
                    "pub_date": pd.to_datetime(getattr(e, "published", getattr(e, "updated", dt.datetime.utcnow()))),
                    "title": getattr(e, "title", ""),
                    "source": d.feed.get("title", url),
                    "url": getattr(e, "link", url)
                })
        except Exception as ex:
            items.append({"pub_date": pd.Timestamp.utcnow(), "title": f"Feed error: {url} ({ex})", "source": "System", "url": url})
    if not items:
        return pd.DataFrame(columns=["pub_date","title","source","url"])
    news = pd.DataFrame(items).sort_values("pub_date", ascending=False).head(limit)
    return news

st.sidebar.header("Filters & Settings")

default_feeds = [
    "https://www.reutersagency.com/feed/?best-sectors=commodities&post_type=best",
    "https://www.reuters.com/markets/commodities/rss",
    "https://www.fao.org/giews/rss/en/",
    "https://www.usda.gov/media/press-releases/rss"
]

custom_env = os.getenv("NEWS_FEEDS","")
try:
    custom_list = json.loads(custom_env) if custom_env else []
    if not isinstance(custom_list, list):
        custom_list = []
except Exception:
    custom_list = []

feed_urls = list(dict.fromkeys(custom_list + default_feeds))

with st.sidebar.expander("News feeds"):
    st.write("Using these RSS feeds:")
    for u in feed_urls:
        st.caption(u)

st.title("Wheat Market Dashboard — Russia, Uzbekistan & Neighbors")

col1, col2, col3 = st.columns([2,1,1])
with col1:
    st.subheader("Prices")
with col2:
    today = dt.date.today()
    start_date = st.date_input("Start date", value=today - dt.timedelta(days=120))
with col3:
    end_date = st.date_input("End date", value=today)

prices = load_prices()
mask = (prices["date"].dt.date >= start_date) & (prices["date"].dt.date <= end_date)
pview = prices.loc[mask].copy()

# Currency conversion helper (user input)
uzs_per_usd = st.sidebar.number_input("Exchange rate (UZS per USD)", value=12510, step=1)

# Build tidy price table with a unified 'price_usd' column
pview["price_usd"] = pview.apply(
    lambda r: (r["price_usd_per_t"] if not pd.isna(r.get("price_usd_per_t", np.nan)) else
               (r["price_uzs_per_t"] / uzs_per_usd if not pd.isna(r.get("price_uzs_per_t", np.nan)) else np.nan)),
    axis=1
)

# Chart selection
markets = st.multiselect("Select markets", sorted(pview["market"].dropna().unique().tolist()),
                         default=sorted(pview["market"].dropna().unique().tolist()))

pchart = pview[pview["market"].isin(markets)].copy()
pchart = pchart.sort_values("date")

tab1, tab2, tab3 = st.tabs(["📈 Price Charts", "🌾 Production", "📰 News & Signals"])

with tab1:
    st.write("Prices shown in USD/t (UZEX converted using the exchange rate above).")
    for mkt in markets:
        seg = pchart[pchart["market"] == mkt]
        if seg.empty: 
            continue
        st.line_chart(seg.set_index("date")["price_usd"], height=260)
        st.caption(f"{mkt} — last: {seg['price_usd'].dropna().iloc[-1]:.2f} USD/t" if not seg['price_usd'].dropna().empty else f"{mkt} — no USD data")

    st.divider()
    st.subheader("Timing Helper (What-if)")
    colA, colB, colC, colD = st.columns(4)
    base = float(pchart["price_usd"].dropna().iloc[-1]) if not pchart["price_usd"].dropna().empty else 210.0
    up5 = base * 1.05
    up10 = base * 1.10
    down15 = base * 0.85
    colA.metric("Now (base)", f"{base:.2f} USD/t")
    colB.metric("Harvest +5%", f"{up5:.2f} USD/t", f"+5%")
    colC.metric("Winter +10%", f"{up10:.2f} USD/t", f"+10%")
    colD.metric("Russia opens −15%", f"{down15:.2f} USD/t", "−15%")

with tab2:
    prod = load_production()
    st.write("Production — 2024/25 actual vs 2025/26 estimate")
    sel_countries = st.multiselect("Countries", sorted(prod["country"].unique().tolist()),
                                   default=sorted(prod["country"].unique().tolist()))
    view = prod[prod["country"].isin(sel_countries)].copy()
    pivot_prod = view.pivot(index="country", columns="marketing_year", values="production_thousand_t").fillna(0)
    st.bar_chart(pivot_prod, height=360)
    st.caption("Units: thousand metric tons (1,000 t).")

with tab3:
    st.subheader("Signals (events that may move price)")
    sig = load_signals()
    st.dataframe(sig.sort_values("date", ascending=False), use_container_width=True, hide_index=True, height=280)

    st.subheader("Latest News (RSS)")
    news = parse_feeds(feed_urls, limit=40)
    if news.empty:
        st.info("No news fetched. Add feeds via the NEWS_FEEDS environment variable.")
    else:
        st.dataframe(news[["pub_date","title","source","url"]], use_container_width=True, hide_index=True, height=360)
        st.caption("Click a row and copy the URL to open in a new tab (Streamlit restricts auto-opening links).")

st.sidebar.markdown("---")
st.sidebar.write("**Data files**: drop updated CSVs into `/data` with the same columns to refresh the charts.")
st.sidebar.write("**Tip**: Add your private price feeds via automation (cron) that rewrites `prices_sample.csv`.")
