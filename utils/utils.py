from agents.utils.helpers import get_date_range
import pandas as pd
import numpy as np

import plotly.graph_objects as go

# CONFIG
#======================================================================
start_date, end_date = get_date_range(reference_date="2025-04-02", month_diff=3)

# Trading strategies
#======================================================================

def calculate_macd(df, short_window=12, long_window=26, signal_window=9):
    df['ema_short'] = df['close'].ewm(span=short_window, adjust=False).mean()
    df['ema_long'] = df['close'].ewm(span=long_window, adjust=False).mean()
    df['macd'] = df['ema_short'] - df['ema_long']
    df['macd_signal'] = df['macd'].ewm(span=signal_window, adjust=False).mean()
    return df

def macd_returns(df, initial_investment=100000):
    required_columns = ['macd', 'macd_signal', 'close']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    df = df.copy()
    df['Buy_Signal'] = np.where(
        (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1)), 1, 0
    )
    df['Sell_Signal'] = np.where(
        (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1)), -1, 0
    )
    df['Signal'] = df['Buy_Signal'] + df['Sell_Signal']
    df['Position'] = df['Signal'].replace(to_replace=0, method='ffill')
    df['Daily_Return'] = df['close'].pct_change()
    df['Strategy_Return'] = df['Position'].shift(1) * df['Daily_Return']
    df['Cumulative_Return'] = (1 + df['Strategy_Return']).cumprod() - 1
    df['Net_Return'] = initial_investment * (1 + df['Cumulative_Return'])

    buy_triggers = df['Buy_Signal'].sum()
    sell_triggers = df['Sell_Signal'].sum()

    df['Peak'] = df['Net_Return'].cummax()
    df['Drawdown'] = df['Net_Return'] - df['Peak']
    df['Drawdown'] = df['Drawdown'].clip(lower=0)
    max_drawdown = df['Drawdown'].max()

    trades = df[df['Signal'] != 0]
    trades['Trade_Return'] = trades['Net_Return'].shift(-1) - trades['Net_Return']
    profits = trades[trades['Trade_Return'] > 0]['Trade_Return']
    losses = trades[trades['Trade_Return'] < 0]['Trade_Return']
    average_profit = profits.mean() if not profits.empty else 0
    average_loss = losses.mean() if not losses.empty else 0

    return df, average_profit, average_loss, buy_triggers, sell_triggers, max_drawdown

def buy_and_hold(price_df):
    df = price_df.copy()
    start_price = price_df.iloc[0]['close']
    start_cash = 100_000
    shares = start_cash // start_price
    leftover_cash = start_cash - shares * start_price
    df['buy_n_hold'] = price_df.apply(lambda row: leftover_cash + shares * row['close'], axis=1)
    return df[['buy_n_hold']]

def long_short_trade(trades_df, price_series):
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

# Eval
#======================================================================

def sharpe_ratio(arg):
    pass

def arr(arg):
    """Annualized rate of return"""
    pass

def cr():
    """Cumulative Return"""
    pass

# Visualizations
#======================================================================

def results_figure(df):
    """Returns a Plotly figure with all indicators on a single plot."""
    df = df.copy()
    df.index = pd.to_datetime(df.index)  # Ensure index is datetime

    fig = go.Figure()

    for col in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[col],
            mode='lines',
            name=col
        ))

    fig.update_layout(
        title='All Data Columns Over Time',
        xaxis_title='Date',
        yaxis_title='Value',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        template='plotly_white',
        height=600
    )

    return fig