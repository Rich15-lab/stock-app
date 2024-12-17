import yfinance as yf
import pandas as pd
import random
import time
from flask import Flask
import threading

app = Flask(__name__)

def save_recommendation(ticker, current_price, buy_price, sell_price, stop_loss):
    data = {
        "Ticker": [ticker],
        "Current Price": [current_price],
        "Buy Price": [buy_price],
        "Sell Price": [sell_price],
        "Stop Loss": [stop_loss]
    }
    df = pd.DataFrame(data)
    file_name = "stock_recommendations.csv"
    try:
        df.to_csv(file_name, mode="a", header=not pd.io.common.file_exists(file_name), index=False)
        print(f"Recommendation saved to {file_name}!")
    except Exception as e:
        print(f"Error saving recommendation: {e}")

def track_stock_performance(ticker, buy_price, sell_price, stop_loss):
    print(f"Tracking {ticker}...")
    stock = yf.Ticker(ticker)
    while True:
        try:
            data = stock.history(period="5d")
            if data.empty:
                print(f"Error: No price data found for {ticker}. Stock may be delisted.")
                break

            current_price = data["Close"].iloc[-1]
            sma_5 = data["Close"].rolling(window=5).mean().iloc[-1]
            volume = data["Volume"].iloc[-1]

            print(f"{ticker} current price: ${current_price:.2f}, Volume: {volume}, 5-day SMA: ${sma_5:.2f}")

            if current_price >= sell_price:
                print(f"{ticker} hit the sell price of ${sell_price:.2f}. Time to sell!")
                break
            elif current_price <= stop_loss:
                print(f"{ticker} hit the stop-loss price of ${stop_loss:.2f}. Time to exit!")
                break
            else:
                print(f"{ticker} is holding at ${current_price:.2f}.")
        except Exception as e:
            print(f"Error tracking {ticker}: {e}")
            break

        time.sleep(60)

def fetch_random_stock_under_5(profit_target=10, stop_loss_percent=10):
    print(f"Scanning the market for a random stock under $5 with a {profit_target}% profit target...\n")
    try:
        nasdaq_url = "https://datahub.io/core/nasdaq-listings/r/nasdaq-listed-symbols.csv"
        tickers = pd.read_csv(nasdaq_url)["Symbol"].tolist()
        random.shuffle(tickers)
    except Exception as e:
        print(f"Error fetching stock tickers: {e}")
        return

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period="1y")

            if data.empty:
                continue

            live_price = data["Close"].iloc[-1]
            if live_price <= 5:
                recent_low = data["Low"].min()
                support_level = recent_low + (live_price - recent_low) * 0.2

                buy_price = max(live_price, support_level)
                sell_price = buy_price * (1 + profit_target / 100)
                stop_loss_price = buy_price * (1 - stop_loss_percent / 100)

                print(f"Recommended Stock: {ticker}")
                print(f"Current Price: ${live_price:.2f}")
                print(f"Historical Support Level: ${support_level:.2f}")
                print(f"Recommended Buy Price: ${buy_price:.2f}")
                print(f"Recommended Sell Price: ${sell_price:.2f}")
                print(f"Stop Loss Price: ${stop_loss_price:.2f}")

                save_recommendation(ticker, live_price, buy_price, sell_price, stop_loss_price)
                track_stock_performance(ticker, buy_price, sell_price, stop_loss_price)
                return
        except Exception as e:
            print(f"Error processing ticker {ticker}: {e}")
            continue

    print("No stocks under $5 found.")

def run_stock_app():
    fetch_random_stock_under_5(profit_target=10, stop_loss_percent=10)

@app.route('/')
def home():
    return "Stock-Smart App is running!"

if __name__ == "__main__":
    threading.Thread(target=run_stock_app).start()
    app.run(host="0.0.0.0", port=5000)
