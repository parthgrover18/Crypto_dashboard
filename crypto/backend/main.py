import yfinance as yf
import pandas as pd
from pymongo import MongoClient
import matplotlib.pyplot as plt
import time



def fetch_btc_data(max_retries=5, delay=10):
    for attempt in range(max_retries):
        try:
            btc_data = yf.download("BTC-USD", period="max", interval="1d")
            if btc_data.empty:
                raise ValueError("Downloaded data is empty.")
            
            new_columns = []
            for col in btc_data.columns:
                if isinstance(col, tuple):
                    new_columns.append(col[0])
                else:
                    new_columns.append(col)
            btc_data.columns = new_columns
            btc_data.reset_index(inplace=True)
            btc_data["Date"] = btc_data["Date"].astype(str)
            return btc_data

        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            time.sleep(delay)

    print("Max retries exceeded. Failed to download BTC data.")
    return pd.DataFrame()

def connect_to_mongo():
    try:
        client = MongoClient("mongodb://127.0.0.1:27017/")
        client.admin.command("ping")
        return client
    except Exception as e:
        return None

def store_data_in_mongo(data, client):
    if client:
        db = client["crypto_database"]
        collection = db["btc_usd_data"]
        collection.delete_many({})
        collection.insert_many(data.to_dict("records"))


def fetch_data_from_mongo(client):
    if client:
        db = client["crypto_database"]
        collection = db["btc_usd_data"]
        btc_data_from_db = pd.DataFrame(list(collection.find()))
        btc_data_from_db["Date"] = pd.to_datetime(btc_data_from_db["Date"])
        btc_data_from_db.sort_values("Date", inplace=True)
        return btc_data_from_db
    else:
        return None


def plot_btc_data(btc_data):
    if btc_data is not None and not btc_data.empty:
        plt.figure(figsize=(12, 6))
        plt.plot(btc_data["Date"], btc_data["Close"], label="BTC/USD Price", color="blue")
        plt.xlabel("Date")
        plt.ylabel("Price (USD)")
        plt.title("BTC/USD Price")
        plt.legend()
        plt.grid()
        plt.show()





btc_data = fetch_btc_data()
mongo_client = connect_to_mongo()

if mongo_client:
    store_data_in_mongo(btc_data, mongo_client)
    btc_data_from_db = fetch_data_from_mongo(mongo_client)
    plot_btc_data(btc_data_from_db)