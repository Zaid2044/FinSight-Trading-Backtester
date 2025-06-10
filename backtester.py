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
    """Runs the SMA Crossover backtesting strategy using a robust NumPy-based loop."""
    print("Running backtest...")
    
    # 1. Calculate SMAs
    df['Short_SMA'] = df['Close'].rolling(window=short_window).mean()
    df['Long_SMA'] = df['Close'].rolling(window=long_window).mean()

    # 2. Generate Signals
    df['Signal'] = 0.0
    df['Signal'] = np.where(df['Short_SMA'] > df['Long_SMA'], 1.0, 0.0)
    df['Position'] = df['Signal'].diff()

    # 3. Simulate Portfolio using NumPy for speed and clarity
    close_prices = df['Close'].to_numpy()
    positions = df['Position'].to_numpy()
    
    cash = initial_capital
    shares = 0.0
    portfolio_history = []

    for i in range(len(close_prices)):
        current_position_signal = positions[i]
        current_price = close_prices[i]

        if current_position_signal == -1.0 and shares > 0:
            cash += shares * current_price
            shares = 0.0
            
        elif current_position_signal == 1.0 and cash > 0:
            shares_to_buy = cash / current_price
            shares += shares_to_buy
            cash = 0.0

        current_portfolio_value = cash + (shares * current_price)
        portfolio_history.append(current_portfolio_value)

    df['Portfolio_Total'] = portfolio_history
    
    # 4. Calculate Performance Metrics
    final_value = df['Portfolio_Total'].iloc[-1]
    total_return = (final_value / initial_capital - 1) * 100
    
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
    ax2.plot(df.index, df['Portfolio_Total'], label='Strategy Portfolio Value', color='darkgreen', linestyle=':', alpha=0.6)
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
        print(f"Final Portfolio Value: ${float(strategy_val):,.2f}")
        print(f"Total Return:          {float(strategy_ret):.2f}%")
        print("-" * 35)
        print("Benchmark: Buy and Hold")
        print(f"Final Portfolio Value: ${float(bnh_val):,.2f}")
        print(f"Total Return:          {float(bnh_ret):.2f}%")
        print("-" * 35)

        plot_results(results_df, TICKER, SHORT_SMA, LONG_SMA)
        
    except Exception as e:
        print(f"An error occurred: {e}")