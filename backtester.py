# backtester.py

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
TICKER = 'TSLA'
START_DATE = '2020-01-01'
END_DATE = '2023-12-31'
SHORT_SMA = 50
LONG_SMA = 200
INITIAL_CAPITAL = 100000.0

def fetch_data(ticker, start, end):
    """Fetches historical stock data from Yahoo Finance."""
    print(f"Fetching data for {ticker} from {start} to {end}...")
    df = yf.download(ticker, start=start, end=end, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No data found for {ticker}. Check ticker symbol or date range.")
    print("Data fetched successfully.")
    return df

def run_backtest(df, initial_capital, short_window, long_window):
    """Runs the SMA Crossover backtesting strategy using a standard, clear loop."""
    print("Running backtest...")
    
    # 1. Calculate SMAs
    df['Short_SMA'] = df['Close'].rolling(window=short_window).mean()
    df['Long_SMA'] = df['Close'].rolling(window=long_window).mean()

    # 2. Generate Signals
    df['Signal'] = 0.0
    # A '1' indicates a golden cross trend (short > long)
    df['Signal'] = np.where(df['Short_SMA'] > df['Long_SMA'], 1.0, 0.0)
    
    # 'Position' finds the exact crossover day. 1 for buy, -1 for sell.
    df['Position'] = df['Signal'].diff()

    # 3. Simulate Portfolio using a clean loop
    # Initialize portfolio columns directly on the main dataframe for simplicity
    df['cash'] = initial_capital
    df['holdings_value'] = 0.0
    df['total_value'] = initial_capital
    df['shares'] = 0.0

    # Use iloc for explicit integer-location based indexing in the loop
    for i in range(1, len(df)):
        # Carry forward values from the previous day (i-1) to the current day (i)
        df.iloc[i, df.columns.get_loc('cash')] = df.iloc[i-1]['cash']
        df.iloc[i, df.columns.get_loc('shares')] = df.iloc[i-1]['shares']

        # Check for Buy Signal: Crossover from 0 to 1, and we have cash
        if df.iloc[i]['Position'] == 1.0 and df.iloc[i-1]['cash'] > 0:
            shares_to_buy = df.iloc[i-1]['cash'] / df.iloc[i]['Close']
            df.iloc[i, df.columns.get_loc('shares')] += shares_to_buy
            df.iloc[i, df.columns.get_loc('cash')] = 0.0

        # Check for Sell Signal: Crossover from 1 to 0, and we have shares
        elif df.iloc[i]['Position'] == -1.0 and df.iloc[i-1]['shares'] > 0:
            cash_from_sale = df.iloc[i-1]['shares'] * df.iloc[i]['Close']
            df.iloc[i, df.columns.get_loc('cash')] += cash_from_sale
            df.iloc[i, df.columns.get_loc('shares')] = 0.0

        # Update portfolio value for the current day after any trades
        holdings_value = df.iloc[i]['shares'] * df.iloc[i]['Close']
        df.iloc[i, df.columns.get_loc('holdings_value')] = holdings_value
        df.iloc[i, df.columns.get_loc('total_value')] = df.iloc[i]['cash'] + holdings_value

    df['Portfolio_Total'] = df['total_value']
    
    # 4. Calculate Performance Metrics
    final_value = df['total_value'].iloc[-1]
    total_return = (final_value / initial_capital - 1) * 100
    
    # Benchmark: Buy and Hold
    buy_and_hold_value = initial_capital * (df['Close'].iloc[-1] / df['Close'].iloc[0])
    buy_and_hold_return = (buy_and_hold_value / initial_capital - 1) * 100

    print("Backtest complete.")
    return df, final_value, total_return, buy_and_hold_value, buy_and_hold_return


def plot_results(df, ticker, short_window, long_window):
    """Visualizes the backtest results."""
    print("Generating plot...")
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(15, 8))
    
    ax.plot(df['Close'], label='Close Price', color='skyblue', alpha=0.8)
    ax.plot(df['Short_SMA'], label=f'{short_window}-Day SMA', color='orange', linestyle='--')
    ax.plot(df['Long_SMA'], label=f'{long_window}-Day SMA', color='purple', linestyle='--')
    
    buy_signals = df[df['Position'] == 1.0]
    ax.plot(buy_signals.index, df.loc[buy_signals.index]['Short_SMA'], '^', markersize=12, color='green', label='Buy Signal (Golden Cross)', alpha=1)
    
    sell_signals = df[df['Position'] == -1.0]
    ax.plot(sell_signals.index, df.loc[sell_signals.index]['Short_SMA'], 'v', markersize=12, color='red', label='Sell Signal (Death Cross)', alpha=1)
    
    ax.set_title(f'"{ticker}" SMA Crossover Backtest ({START_DATE} to {END_DATE})', fontsize=20)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Price (USD)', fontsize=12)
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True)
    
    ax2 = ax.twinx()
    ax2.plot(df['Portfolio_Total'], label='Strategy Portfolio Value', color='darkgreen', linestyle=':', alpha=0.6)
    ax2.set_ylabel('Portfolio Value (USD)', fontsize=12, color='darkgreen')
    ax2.tick_params(axis='y', labelcolor='darkgreen')
    
    fig.tight_layout()
    plt.savefig('trading_chart.png', dpi=300)
    print("Plot saved as 'trading_chart.png'.")
    plt.show()

if __name__ == "__main__":
    try:
        data = fetch_data(TICKER, START_DATE, END_DATE)
        results_df, strategy_val, strategy_ret, bnh_val, bnh_ret = run_backtest(data.copy(), INITIAL_CAPITAL, SHORT_SMA, LONG_SMA)
        
        print("\n--- Backtest Performance ---")
        print(f"Strategy: SMA Crossover ({SHORT_SMA}/{LONG_SMA}) on {TICKER}")
        print(f"Period: {START_DATE} to {END_DATE}")
        print("-" * 35)
        print(f"Initial Capital:       ${INITIAL_CAPITAL:,.2f}")
        print(f"Final Portfolio Value: ${strategy_val:,.2f}")
        print(f"Total Return:          {strategy_ret:.2f}%")
        print("-" * 35)
        print("Benchmark: Buy and Hold")
        print(f"Final Portfolio Value: ${bnh_val:,.2f}")
        print(f"Total Return:          {bnh_ret:.2f}%")
        print("-" * 35)

        plot_results(results_df, TICKER, SHORT_SMA, LONG_SMA)
        
    except Exception as e:
        print(f"An error occurred: {e}")