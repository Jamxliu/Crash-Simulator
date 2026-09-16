import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Tiered Crash Deployment Simulator", layout="wide")

st.title("📉 Tiered Crash-Buying Simulator")
st.markdown("Simulate automated institutional deployment strategies during historic market crashes.")

st.sidebar.header("Strategy Controls")
initial_cash = st.sidebar.number_input("Initial Cash ($)", value=100000, step=10000)

crash_option = st.sidebar.selectbox(
    "Select Crash Period",
    ("2020 COVID Crash", "2022 Bear Market", "2008 Financial Crisis")
)

if crash_option == "2020 COVID Crash":
    start_date, end_date = "2020-02-01", "2020-05-01"
elif crash_option == "2022 Bear Market":
    start_date, end_date = "2022-01-01", "2022-10-31"
else:
    start_date, end_date = "2008-01-01", "2009-03-31"

ticker = st.sidebar.text_input("Asset Ticker", value="QQQ")

if st.sidebar.button("Run Simulation", type="primary"):
    with st.spinner("Downloading data and running simulation..."):
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)

        if df.empty:
            st.error("No data found for this ticker/date range.")
        else:
            if isinstance(df.columns, pd.MultiIndex):
                price_series = df['Close'][ticker]
            else:
                price_series = df['Close']

            cash = initial_cash
            shares_held = 0
            peak_price = price_series.iloc[0]

            tiers = [
                {"drop": -0.10, "deploy_pct": 0.20, "fired": False},
                {"drop": -0.15, "deploy_pct": 0.30, "fired": False},
                {"drop": -0.20, "deploy_pct": 0.50, "fired": False}
            ]

            simulation_log = []

            for date, price in price_series.items():
                if price > peak_price:
                    peak_price = price

                current_drawdown = (price - peak_price) / peak_price

                for tier in tiers:
                    if current_drawdown <= tier["drop"] and not tier["fired"]:
                        deploy_amount = cash * tier["deploy_pct"]
                        if deploy_amount > 0 and cash > 0:
                            shares_bought = deploy_amount / price
                            shares_held += shares_bought
                            cash -= deploy_amount
                            tier["fired"] = True

                            simulation_log.append({
                                "Date": date.strftime('%Y-%m-%d'),
                                "Price": round(float(price), 2),
                                "Drawdown": f"{current_drawdown*100:.1f}%",
                                "Action": f"Deployed ${deploy_amount:,.2f}",
                                "Cash Remaining": round(float(cash), 2)
                            })

            final_price = float(price_series.iloc[-1])
            final_portfolio_value = cash + (shares_held * final_price)
            total_return = ((final_portfolio_value - initial_cash) / initial_cash) * 100

            col1, col2, col3 = st.columns(3)
            col1.metric("Starting Capital", f"${initial_cash:,.2f}")
            col2.metric("Ending Portfolio Value", f"${final_portfolio_value:,.2f}")
            col3.metric("Total Return", f"{total_return:.2f}%")

            st.subheader("Price Trend & Drawdown Chart")
            st.line_chart(price_series)

            st.subheader("Execution Log")
            if simulation_log:
                st.dataframe(pd.DataFrame(simulation_log), use_container_width=True)
            else:
                st.info("No tiers were breached during this period.")
