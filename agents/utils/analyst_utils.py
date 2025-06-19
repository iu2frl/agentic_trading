# Web scraping components for analyst agents

import yfinance as yf
import pandas_ta as ta
import pandas as pd

from agents.utils.llm_utils import Gpt4Free

import datetime
from datetime import timedelta
from dateutil import parser
from pprint import pprint
import os
import requests

# from agents.db.db import SentimentDB, SocialMediaDB
from agents.utils.helpers import Color

from dotenv import load_dotenv
load_dotenv()


GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
SERP_KEY=os.getenv('SERP_KEY')

class ShareData:
    """ShareData data helper for analyst agent."""
    
    def __init__(self, ticker, country='India', stock_exchange='NS'):
        """
        Initializes the ShareData class.
        :param ticker: Stock ticker symbol
        :param country: Country of the stock exchange (default: 'India')
        :param stock_exchange: Stock exchange (default: 'NS')
        """
        self.ticker = f"{ticker}.NS" if country.lower() == 'india' and stock_exchange.upper() == 'NS' else ticker
        self.stock = yf.Ticker(self.ticker)
        self.stock_info = None
        self.ratios = [
            "trailingPE", "forwardPE", "ebitdaMargins", "profitMargins", "grossMargins",
            "operatingMargins", "returnOnAssets", "returnOnEquity", "currentRatio",
            "quickRatio", "debtToEquity", "priceToBook", "priceToSalesTrailing12Months",
            "enterpriseToRevenue", "enterpriseToEbitda", "pegRatio", "payoutRatio",
            "dividendRate", "dividendYield", "fiveYearAvgDividendYield"
        ]
    
    def get_info(self):
        try:
            self.stock_info=self.stock.info
        except Exception as e:
            return e    

    def get_price(self, start_date, end_date):
        """Fetch historical stock price data for the given date range."""
        try:
            data = self.stock.history(start=start_date, end=end_date)
            return data[['Open', 'High', 'Low', 'Close', 'Volume']]
        except Exception as e:
            return f"Error fetching price data: {e}"
    
    def get_income_statement(self, period='annual'):
        """Fetch the income statement (quarterly or annual)."""
        try:
            if period == 'quarterly':
                return self.stock.quarterly_income_stmt
            return self.stock.income_stmt  # Default: Annual
        except Exception as e:
            return f"Error fetching income statement: {e}"
    
    def get_balance_sheet(self, period='annual'):
        """Fetch the balance sheet (quarterly or annual)."""
        try:
            if period == 'quarterly':
                return self.stock.quarterly_balance_sheet
            return self.stock.balance_sheet  # Default: Annual
        except Exception as e:
            return f"Error fetching balance sheet: {e}"

    def get_available_ratios(self):
        available_data = {key: self.stock_info[key] for key in self.ratios if key in self.stock_info}
        formatted_string = "\n".join(f"{key}: {value}" for key, value in available_data.items())
        return f"""{formatted_string}"""

    def get_share_name(self):
        """Fetch the company name from the ticker symbol."""
        try:
            return self.stock.info.get('longName', 'Company name not found')
        except Exception as e:
            return f"Error fetching company name: {e}"

    def get_shareholding(self):
        try:
            return self.stock.major_holders
        except Exception as e:
            return f"Error fetching major shareholders: {e}"

    def get_technical_indicators(self, start_date, end_date):
        """Calculate and return technical indicators: RSI, ADX, Bollinger Bands, ATR, VWMA (as VR), CCI, and MACD."""
        try:
            data = self.get_price(start_date, end_date)

            # RSI
            data['RSI'] = ta.rsi(data['Close'])

            # ADX
            adx = ta.adx(data['High'], data['Low'], data['Close'])
            data['ADX'] = adx['ADX_14']

            # Bollinger Bands (Fix length)
            bollinger = ta.bbands(data['Close'], length=20)  # Ensure length is 20
            if bollinger is not None:
                data['BB_lower'] = bollinger.iloc[:, 0]  # Lower Band
                data['BB_middle'] = bollinger.iloc[:, 1]  # Middle Band
                data['BB_upper'] = bollinger.iloc[:, 2]  # Upper Band

            # ATR
            data['ATR'] = ta.atr(data['High'], data['Low'], data['Close'])

            # VWMA (as Volume Indicator)
            data['VWMA'] = ta.vwma(data['Close'], data['Volume'])

            # CCI
            data['CCI'] = ta.cci(data['High'], data['Low'], data['Close'])

            # MACD
            macd = ta.macd(data['Close'])
            data['MACD'] = macd['MACD_12_26_9']
            data['MACD_signal'] = macd['MACDs_12_26_9']

            return data.dropna()

        except Exception as e:
            return f"Error calculating technical indicators: {e}"

    def summarize_technical_indicators(self, df):
        """
        Summarizes key technical indicators to send to an LLM for analysis.
        """
        summary = {}

        # RSI: Overbought (>70) or Oversold (<30)
        summary["RSI_mean"] = df["RSI"].mean()
        summary["RSI_latest"] = df["RSI"].iloc[-1]
        summary["RSI_signal"] = "Overbought" if df["RSI"].iloc[-1] > 70 else "Oversold" if df["RSI"].iloc[-1] < 30 else "Neutral"

        # ADX: Strength of Trend
        summary["ADX_mean"] = df["ADX"].mean()
        summary["ADX_latest"] = df["ADX"].iloc[-1]
        summary["ADX_trend_strength"] = "Strong Trend" if df["ADX"].iloc[-1] > 25 else "Weak Trend"

        # Bollinger Bands: Breakout Indicator
        summary["BB_latest_price_position"] = "Above Upper Band" if df["Close"].iloc[-1] > df["BB_upper"].iloc[-1] else "Below Lower Band" if df["Close"].iloc[-1] < df["BB_lower"].iloc[-1] else "Within Bands"

        # ATR: Volatility Measure
        summary["ATR_mean"] = df["ATR"].mean()
        summary["ATR_latest"] = df["ATR"].iloc[-1]

        # MACD: Buy/Sell Signals
        summary["MACD_latest"] = df["MACD"].iloc[-1]
        summary["MACD_signal_latest"] = df["MACD_signal"].iloc[-1]
        summary["MACD_crossover"] = "Bullish" if df["MACD"].iloc[-1] > df["MACD_signal"].iloc[-1] else "Bearish"

        return summary

class ScreenerData:
    def __init__(self, days=90):
        self.days = days
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json",
        }

    def api_call(self, url):
        try:
            print("---------------------------")
            print(f"Calling : {url}")
            print("---------------------------")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None
    
    def process_response(self, response):
        if not response or "datasets" not in response:
            return None

        processed_data = {}

        # Create an empty DataFrame for the merged data
        merged_df = pd.DataFrame()

        # Iterate through each dataset
        for dataset in response["datasets"]:
            metric = dataset["metric"]
            values = dataset.get("values", [])

            # Convert values into a DataFrame with Date as index
            df = pd.DataFrame(values, columns=["Date", metric])
            df["Date"] = pd.to_datetime(df["Date"])  # Convert the Date to datetime format

            # Merge the data with the main DataFrame on the 'Date' column
            if merged_df.empty:
                merged_df = df
            else:
                merged_df = pd.merge(merged_df, df, on="Date", how="outer")

        # Sort by date if necessary and reset index
        merged_df = merged_df.sort_values(by="Date").reset_index(drop=True)

        return merged_df

    def pe(self, company_id=3365):
        url = f"https://www.screener.in/api/company/{company_id}/chart/?q=Price+to+Earning-Median+PE-EPS&days={self.days}&consolidated=true"
        response = self.api_call(url)
        return self.process_response(response)
    
    def ev_multiple(self, company_id=3365):
        url = f"https://www.screener.in/api/company/{company_id}/chart/?q=EV+Multiple-Median+EV+Multiple-EBITDA&days={self.days}&consolidated=true"
        response = self.api_call(url)
        return self.process_response(response)
    
    def pbv(self, company_id=3365):
        url = f"https://www.screener.in/api/company/{company_id}/chart/?q=Price+to+book+value-Median+PBV-Book+value&days={self.days}&consolidated=true"
        response = self.api_call(url)
        return self.process_response(response)
    
    def market_cap_to_sales(self, company_id=3365):
        url = f"https://www.screener.in/api/company/{company_id}/chart/?q=Market+Cap+to+Sales-Median+Market+Cap+to+Sales-Sales&days={self.days}&consolidated=true"
        response = self.api_call(url)
        return self.process_response(response)

class NewsData:
    """News data analyst agent using SerpAPI's Google News API."""
    
    def __init__(self, api_key=SERP_KEY):
        """Initialize the News class with SerpAPI key."""
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search"
    
    def search_news(self, query, start_date=None, end_date=None, max_results=10):
        """Fetch news articles within the given date range."""
        
        if end_date is None:
            end_date = datetime.date.today()
        
        if start_date is None:
            start_date = end_date - datetime.timedelta(days=60)  # Default: Last 2 months
        
        params = {
            "engine": "google_news",
            "q": query,
            "api_key": self.api_key,
            "num": max_results,
            "tbm" : "nws",
            "tbs": f"cdr:1,cd_min:{start_date},cd_max:{end_date}"  # Date range filter

        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            articles = data['news_results']
            
            return articles if articles else "No relevant news found."
        except requests.exceptions.RequestException as e:
            return f"Error fetching news: {e}"

class SocialMedia(object):
    """docstring for SocialMedia."""
    def __init__(self, start_date, end_date):
        super(SocialMedia, self).__init__()
        # self.sentiment_db = SentimentDB()
        # self.socialmedia_db = SocialMediaDB()
        self.sentimentanalyzer = SentimentAnalyzer()

        self.start_date = start_date
        self.end_date=end_date

    def get_posts(self, share_symbol):
        df = self.socialmedia_db.get_posts(share_symbol)
        return df

    def calculate_sentiment_scores(self, share_name, share_symbol):
        """Fetch and analyze social media sentiment for the given share over a date range."""

        self.db.init_table(share_symbol=share_symbol)

        current_date = self.start_date

        while current_date <= self.end_date:
            # Step 1: Check if data already exists for this date
            if self.db.date_exists(share_symbol=share_symbol, date=current_date):
                current_date += timedelta(days=1)
                continue  # Skip processing if the date is already stored

            # Step 2: Get social media posts for the date
            all_posts = self.get_posts(date=current_date)

            if not all_posts:  # If no posts found for the date, move to next day
                current_date += timedelta(days=1)
                continue

            # Step 3: Perform sentiment analysis on posts
            all_scores = []

            for post in all_posts:
                headline = post['headline']
                score = self.sentimentanalyzer.get_sentiment_score(
                    company_name=share_name,
                    headline=headline
                )
                all_scores.append(float(score))

            # Step 4: Calculate average sentiment score and update database
            if all_scores:
                average_score = sum(all_scores) / len(all_scores)
                self.db.update_score(share_symbol=share_symbol, date=current_date, average_score=average_score)

            # Move to the next day
            current_date += timedelta(days=1)
    
    def get_sentiment_scores(self, share_symbol):
        df = self.db.get_sentiment_data(share_symbol)
        return df

# Sentiment Algo
class SentimentAnalyzer:
    def __init__(self, ai_model: Gpt4Free = Gpt4Free()):
        self.model = ai_model

    def generate_prompt(self, company_name: str, headline: str) -> str:
        return (
            f"As a financial expert, analyze the sentiment of the following news headline about {company_name}.\n"
            f"Headline: '{headline}'\n"
            "Provide a one-word sentiment classification (YES, NO, or UNKNOWN) on the first line, followed by a concise explanation."
        )

    def get_sentiment_score(self, company_name: str, headline: str):
        prompt = self.generate_prompt(company_name, headline)
        response = self.model.call(prompt)
        response_text = response.strip()
        lines = response_text.split("\n", 1)
        sentiment = lines[0].strip().upper() if lines else "UNKNOWN"
        explanation = lines[1].strip() if len(lines) > 1 else "No explanation provided."

        sentiment_mapping = {"YES": 1, "UNKNOWN": 0, "NO": -1}
        score = sentiment_mapping.get(sentiment, 0)  # Default to neutral if invalid output
        
        return {"company": company_name, "headline": headline, "sentiment": sentiment, "score": score, "explanation": explanation}


# Example usage:
if __name__ == "__main__":

    #####################################################################################################################3
    # Share Data
    share = ShareData("TCS")  # Default India, NS
    share_name = share.get_share_name()
    # print(share.get_price("2024-01-01", "2024-03-01"))
    # print(share.get_income_statement("quarterly"))
    # print(share.get_balance_sheet("annual"))
    # Initialize the ShareData class with a stock ticker

    #####################################################################################################################3
    # Fetch the technical indicators
    # start_date = "2024-01-01"
    # end_date = "2024-03-29"
    # technical_data = share.get_technical_indicators(start_date, end_date)
    # summary = share.summarize_technical_indicators(technical_data)
    # llm_prompt = f"""
    # Analyze the following technical indicator summary:

    # - RSI: {summary["RSI_latest"]} ({summary["RSI_signal"]})
    # - ADX: {summary["ADX_latest"]} ({summary["ADX_trend_strength"]})
    # - Bollinger Bands: {summary["BB_latest_price_position"]}
    # - ATR: {summary["ATR_latest"]} (Volatility Level)
    # - MACD: {summary["MACD_latest"]} vs Signal {summary["MACD_signal_latest"]} ({summary["MACD_crossover"]} Crossover)

    # What does this indicate about the stock's potential movement?
    # """
    # # Display the results
    # print(llm_prompt)
    # print("----------------")
    # print(technical_data)

    #####################################################################################################################3
    # Reddit
    # reddit = Reddit(
    #     client_id=REDDIT_CLIENT_ID, 
    #     client_secret=REDDIT_CLIENT_SECRET, 
    #     user_agent=REDDIT_USER_AGENT
    #     )
    # print(share_name)
    # # Fetch posts for a specific date (e.g., March 1, 2025)
    # target_date = date(2025, 1, 9)
    # posts = reddit.get_posts_by_date(target_date)

    # posts = reddit.search_latest_posts(share_name=share_name)

    # print(posts)

    # post_url = "https://www.reddit.com/r/stocks/comments/1jh5g8g/at_which_point_does_tesla_has_to_issue_a_profit/"
    # post_details = reddit_client.get_post_details(post_url)

    # pprint(post_details)

    # x_api = X(
    #     start_date="2024-01-01",
    #     end_date="2024-03-29"
    # )
    
    # tweets = x_api.search_posts_in_date_range(
    #     share_name="Bajaj Finance",
    #     share_symbol="BAJFINANCE",

    # )

    # print(tweets)

    # print(tweets)

    #####################################################################################################################3
    # Sentiment Analyzer Algo
    
    # analyzer = SentimentAnalyzer()
    # result = analyzer.get_sentiment_score("Apple Inc.", "Apple releases new MacBook Pro with M3 chip.")
    # print(result)


    

    pass
