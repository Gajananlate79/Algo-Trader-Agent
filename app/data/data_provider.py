import pandas as pd
import requests
from io import BytesIO
import zipfile


class DataProvider:

    @staticmethod
    def fetch_nifty50_stocks():
        # Read CSV into DataFrame
        df = pd.read_csv("./data/EQUITY_L.csv")

        # Column "Symbol" contains stock symbols
        symbols = df["SYMBOL"].tolist()
        print(f"Received the stocks: {symbols}")
        return symbols
