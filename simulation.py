from agents.db.db import DB, ManagerDecision, ManagerDecisionLongShort, Technicals
from utils import start_date, end_date

import pandas as pd
import numpy as np

import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objs as go
from datetime import datetime

from config.settings import *

ticker = 'TCS'
db = DB(DB_PATH)

num_days = ( datetime.strptime(end_date, "%Y-%m-%d")  - datetime.strptime(start_date, "%Y-%m-%d")).days

data = db.read(
    ManagerDecision,
    ticker=ticker
)

df = pd.DataFrame([row.__dict__ for row in data])
df.drop(columns=["_sa_instance_state"], inplace=True, errors="ignore")  # Remove SQLAlchemy metadata column
trade_data = df.drop(columns=['reason', 'ticker'], axis=1)       

data_long_short = db.read(
    ManagerDecisionLongShort,
    ticker=ticker
)

df = pd.DataFrame([row.__dict__ for row in data_long_short])
df.drop(columns=["_sa_instance_state"], inplace=True, errors="ignore")  # Remove SQLAlchemy metadata column
trade_data_long_short = df.drop(columns=['reason', 'ticker'], axis=1)       

technicals_data = db.read(
    Technicals,
    ticker=ticker
)

df = pd.DataFrame([row.__dict__ for row in technicals_data])
df.drop(columns=["_sa_instance_state"], inplace=True, errors="ignore")  # Remove SQLAlchemy metadata column
technicals_df = df  


# print(trade_data_long_short)

TICKER = "TCS.NS"
# START_DATE = "2025-01-01"
# END_DATE = "2025-03-31"
START_DATE = start_date
END_DATE = end_date


# --- SIMULATED TRADE DECISIONS (replace this with your real df if loading from a file) ---

trade_data['date'] = pd.to_datetime(trade_data['date'])

# --- FETCH PRICE DATA ---
# data = yf.download(TICKER, start=START_DATE, end=END_DATE)
data = technicals_df[['date', 'close']].set_index('date')
data = data[['close']].rename(columns={'close': 'price'})
data.index = pd.to_datetime(data.index)

# --- SIMULATION ---
def simulate_trades(trade_df, price_df):
    portfolio_value = []
    cash = 100000  # starting with 100k INR
    shares = 0

    for current_date in price_df.index:
        actions = trade_df.loc[trade_df['date'] == current_date, 'decision']
        price = price_df.loc[current_date, 'price']
        price = price.iloc[0] if isinstance(price, pd.Series) else price

        for act in actions:
            decision = str(act).strip().lower()
            if decision == 'buy' and cash >= price:
                shares_to_buy = cash // price
                cash -= shares_to_buy * price
                shares += shares_to_buy
            elif decision == 'sell' and shares > 0:
                cash += shares * price
                shares = 0

        portfolio_value.append((current_date, cash + shares * price))

    return pd.DataFrame(portfolio_value, columns=['date', 'portfolio_value']).set_index('date')


def simulate_long_short(trades_df, price_series):
    """
    Simulates a long/short strategy portfolio.
    
    Parameters:
    - trades_df: DataFrame with columns ['date', 'id', 'decision'] where 'decision' is 'Long' or 'Short'
    - price_series: Series indexed by date with daily prices of the share
    
    Returns:
    - DataFrame indexed by date with column 'portfolio_value'
    """
    trades_df['date'] = pd.to_datetime(trades_df['date'])
    price_series.index = pd.to_datetime(price_series.index)

    # Flatten price_series if it has multiple levels (e.g., from yfinance)
    if isinstance(price_series, pd.DataFrame):
        if 'Adj Close' in price_series.columns:
            price_series = price_series['Adj Close']
        else:
            price_series = price_series.iloc[:, 0]  # Use the first column

    price_series.name = 'price'  # Optional, keeps things clean

    # Sort everything
    trades_df = trades_df.sort_values('date')
    price_series = price_series.sort_index()

    initial_cash = 100_000
    cash = initial_cash
    positions = []

    # Simulate day-by-day
    portfolio_values = []
    for date in price_series.index:
        # Check if any trades were made today
        todays_trades = trades_df[trades_df['date'] == date]
        
        for _, trade in todays_trades.iterrows():
            entry_price = price_series.loc[date]
            positions.append({
                'entry_date': date,
                'entry_price': entry_price,
                'type': trade['decision']  # 'Long' or 'Short'
            })
        
        # Calculate current portfolio value
        value = cash
        current_price = price_series.loc[date]
        
        for pos in positions:
            if pos['type'] == 'Long':
                value += current_price - pos['entry_price']
            elif pos['type'] == 'Short':
                value += pos['entry_price'] - current_price
        
        portfolio_values.append({'date': date, 'portfolio_value': value})
    
    # Return DataFrame with date as a clean single-level index
    result_df = pd.DataFrame(portfolio_values)
    result_df['date'] = pd.to_datetime(result_df['date'])
    result_df = result_df.set_index('date')
    result_df.index.name = 'date'  # Set index name explicitly
    result_df = result_df[['portfolio_value']]  # Ensure correct column order
    return result_df


# --- BUY & HOLD STRATEGY ---
def buy_and_hold(price_df):
    start_price = price_df.iloc[0]['price']
    start_cash = 100000
    shares = start_cash // start_price
    leftover_cash = start_cash - shares * start_price
    processed_df = price_df.apply(lambda row: leftover_cash + shares * row['price'], axis=1)

    return processed_df
    # return processed_df.iloc[-1, -1]


# --- RUN SIMULATION ---
simulated = simulate_trades(trade_data, data)
long_short_simulated = simulate_long_short(trade_data_long_short, data)
# print(long_short_simulated)
buy_hold = buy_and_hold(data)

# --- STREAMLIT UI ---
st.title("Trade Strategy vs Buy & Hold Simulator : TCS")


st.subheader("Long-Short Strategy vs Buy & Hold")
st.dataframe(trade_data_long_short)
comparison_ls_df = long_short_simulated.copy()
comparison_ls_df['Buy & Hold'] = buy_hold

portfolio_fig = go.Figure()
portfolio_fig.add_trace(go.Scatter(x=comparison_ls_df.index, y=comparison_ls_df['portfolio_value'], mode='lines', name='Long-Short Strategy'))
portfolio_fig.add_trace(go.Scatter(x=comparison_ls_df.index, y=comparison_ls_df['Buy & Hold'], mode='lines', name='Buy & Hold'))
st.plotly_chart(portfolio_fig)

st.subheader("Final Portfolio Values")
ls_value = round(long_short_simulated.iloc[-1]['portfolio_value'], 2)
buy_value = round(buy_hold.iloc[-1].item(), 2)

final_values = {
    "Strategy": ["Long-Short Strategy", "Buy & Hold"],
    "Final Value (₹)": [ls_value, buy_value]
}
final_df = pd.DataFrame(final_values)
st.table(final_df)


initial_value = 100000
ls_change_pct = ((ls_value - initial_value) / initial_value) * 100
annual_growth_rate = ((1 + (ls_change_pct/100))**(365/int(num_days)) - 1) *100
buy_change_pct = ((buy_value - initial_value) / initial_value) * 100
absolute_diff = ls_value - buy_value
performance_diff_pct = ls_change_pct - buy_change_pct

metrics = {
    "Metric": [
        "Initial Portfolio Value (₹)",
        "% Change - Long-Short Strategy",
        "Estimated Annual Growth Rate",
        "% Change - Buy & Hold",
        "Absolute Difference (₹)",
        "Performance Difference (%)"
    ],
    "Value": [
        f"{initial_value:,.2f}",
        f"{ls_change_pct:.2f}%",
        f"{annual_growth_rate:.2f}%",
        f"{buy_change_pct:.2f}%",
        f"{absolute_diff:,.2f}",
        f"{performance_diff_pct:.2f}%"
    ]
}
metrics_df = pd.DataFrame(metrics)

# Highlight only values for absolute and percentage difference
def highlight_green(val, metric):
    if metric in ["Absolute Difference (₹)", "Performance Difference (%)"]:
        return 'color: green'
    return ''

styled_metrics = metrics_df.style.apply(
    lambda row: ['' if col == 'Metric' else highlight_green(row['Value'], row['Metric']) for col in row.index],
    axis=1
)
st.dataframe(styled_metrics, use_container_width=True)

st.divider()

st.subheader("Standard By/Sell/Hold")
st.dataframe(trade_data)


st.subheader("Portfolio Comparison")
comparison_df = simulated.copy()
comparison_df['Buy & Hold'] = buy_hold

portfolio_fig = go.Figure()
portfolio_fig.add_trace(go.Scatter(x=comparison_df.index, y=comparison_df['portfolio_value'], mode='lines', name='Simulated Strategy'))
portfolio_fig.add_trace(go.Scatter(x=comparison_df.index, y=comparison_df['Buy & Hold'], mode='lines', name='Buy & Hold'))
st.plotly_chart(portfolio_fig)

st.subheader("Final Portfolio Values")
st.write("Simulated Strategy:", round(simulated.iloc[-1]['portfolio_value'], 2))
st.write("Buy & Hold Strategy:", round(buy_hold.iloc[-1], 2))


# --- FINAL VALUES TABLE ---
# --- FINAL PORTFOLIO VALUES TABLE ---
st.subheader("Final Portfolio Values")
sim_value = round(simulated.iloc[-1]['portfolio_value'], 2)
buy_value = round(buy_hold.iloc[-1], 2)  # Make sure buy_hold is a DataFrame

final_values = {
    "Strategy": ["Simulated Strategy", "Buy & Hold"],
    "Final Value (₹)": [sim_value, buy_value]
}
final_df = pd.DataFrame(final_values)
st.table(final_df)

# --- METRICS CALCULATION ---
initial_value = 100000

sim_change_pct = ((sim_value - initial_value) / initial_value) * 100
buy_change_pct = ((buy_value - initial_value) / initial_value) * 100
absolute_diff = sim_value - buy_value
performance_diff_pct = sim_change_pct - buy_change_pct

# --- METRICS TABLE ---
st.subheader("Performance Metrics")
metrics = {
    "Metric": [
        "Initial Portfolio Value (₹)",
        "% Change - Simulated Strategy",
        "% Change - Buy & Hold",
        "Absolute Difference (₹)",
        "Performance Difference (%)"
    ],
    "Value": [
        f"{initial_value:,.2f}",
        f"{sim_change_pct:.2f}%",
        f"{buy_change_pct:.2f}%",
        f"{absolute_diff:,.2f}",
        f"{performance_diff_pct:.2f}%"
    ]
}
metrics_df = pd.DataFrame(metrics)
def highlight_specific_values(val, metric):
    if metric in ["Absolute Difference (₹)", "Performance Difference (%)"]:
        return 'color: green'
    return ''

styled_metrics = metrics_df.style.apply(
    lambda row: ['' if col == 'Metric' else highlight_specific_values(row['Value'], row['Metric']) for col in row.index],
    axis=1
)

st.dataframe(styled_metrics, use_container_width=True)

# ##############################################3

st.subheader("Technicals")
st.dataframe(technicals_df)

from utils import macd_returns
import matplotlib.pyplot as plt


df, average_profit, average_loss, buy_triggers, sell_triggers, max_drawdown = macd_returns(technicals_df)

st.write(f"Initial Investment: ${initial_value}")
st.write(f"Final Value of Investment: ${df['Net_Return'].iloc[-1]:.2f}")
st.write(f"Total Return: {df['Cumulative_Return'].iloc[-1] * 100:.2f}%")
st.write(f"Number of Buy Triggers: {buy_triggers}")
st.write(f"Number of Sell Triggers: {sell_triggers}")
st.write(f"Maximum Drawdown: {max_drawdown:.2f}")
st.write(f"Average Profit per Trade: {average_profit:.2f}")
st.write(f"Average Loss per Trade: {average_loss:.2f}")

import pandas as pd
import matplotlib.pyplot as plt
import io

fig, axes = plt.subplots(4, 1, figsize=(14, 14), sharex=True)
fig.tight_layout(pad=3.0)

# Subplot 1: Close Price
axes[0].plot(df.index, df['close'], label='Close Price', color='blue')
axes[0].set_title('Nifty 50 Daily Prices')
axes[0].legend()

# Subplot 2: MACD
axes[1].plot(df.index, df['macd'], label='MACD', color='blue')
axes[1].plot(df.index, df['macd_signal'], label='MACD Signal', color='red')
axes[1].set_title('MACD Indicator')
axes[1].legend()

# Subplot 3: Buy and Sell Signals
axes[2].plot(df.index, df['close'], label='Close Price', color='blue')
buy_signals = df[df['Buy_Signal'] == 1]
sell_signals = df[df['Sell_Signal'] == -1]
axes[2].scatter(buy_signals.index, buy_signals['close'], marker='^', color='green', label='Buy Signal', alpha=1)
axes[2].scatter(sell_signals.index, sell_signals['close'], marker='v', color='red', label='Sell Signal', alpha=1)
axes[2].set_title('Buy and Sell Signals')
axes[2].legend()

# Subplot 4: Net Return
axes[3].plot(df.index, df['Net_Return'], label='Net Return', color='purple')
axes[3].set_title('Net Return')
axes[3].legend()

# Convert Matplotlib figure to a Streamlit-displayable format
buf = io.BytesIO()
fig.savefig(buf, format="png")
st.image(buf)
