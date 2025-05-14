# Web scraping components for analyst agents

import yfinance as yf
import pandas_ta as ta
import pandas as pd
import praw

from ntscraper import Nitter

from google import genai
from google.genai.types import HttpOptions

import datetime
from datetime import  timezone, timedelta, date
from dateutil import parser
from pprint import pprint
import os
import re
import time
import requests

# from agents.db.db import SentimentDB, SocialMediaDB
from agents.utils.helpers import Color

from dotenv import load_dotenv
load_dotenv()

REDDIT_CLIENT_SECRET=os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_CLIENT_ID=os.getenv('REDDIT_CLIENT_ID')
REDDIT_USER_AGENT=os.getenv('REDDIT_USER_AGENT')
X_BEARER_TOKEN=os.getenv('X_BEARER_TOKEN')
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
SERP_KEY=os.getenv('SERP_KEY')

class Reddit:
    """Reddit data helper for analyst agent."""
    
    def __init__(self, client_id, client_secret, user_agent):
        """Initialize Reddit API client."""
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        self.subreddits = [
            "IndianStockMarket",
            "IndiaInvestments",
            "IndianStreetBets",
            "StockMarketIndia"
        ]
    
    def get_posts_by_date(self, date, limit=50):
        """
        Retrieve Reddit posts from the specified date across multiple subreddits.

        :param date: A datetime.date object representing the date to retrieve posts for.
        :param limit: Maximum number of posts to fetch per subreddit.
        :return: List of relevant Reddit posts.
        """
        try:
            # Convert date to start and end timestamps (00:00:00 - 23:59:59)
            start_timestamp = int(time.mktime(datetime.datetime(date.year, date.month, date.day, 0, 0, 0).timetuple()))
            end_timestamp = int(time.mktime(datetime.datetime(date.year, date.month, date.day, 23, 59, 59).timetuple()))

            results = []

            for subreddit in self.subreddits:
                subreddit_obj = self.reddit.subreddit(subreddit)

                # Use search with 'timestamp' filtering
                posts = subreddit_obj.search(
                    query="timestamp:{}..{}".format(start_timestamp, end_timestamp),
                    sort="new",
                    syntax="cloudsearch",
                    limit=limit
                )

                for post in posts:
                    results.append({
                        'title': post.title,
                        'url': post.url,
                        'created_utc': datetime.datetime.utcfromtimestamp(post.created_utc),
                        'score': post.score,
                        'num_comments': post.num_comments,
                        'subreddit': post.subreddit.display_name
                    })

            return results if results else "No relevant posts found on this date."
        except Exception as e:
            return f"Error fetching Reddit posts: {e}"
        
    def search_latest_posts(self, share_name, limit=20):
        """
        Search for the latest Reddit posts related to a given share in specified subreddits.
        
        :param share_name: The stock/company name to search for.
        :param subreddits: List of subreddits to search within. Defaults to ['stocks', 'investing'] if None.
        :param limit: Number of posts to retrieve per subreddit.
        :return: List of relevant Reddit posts.
        """
        try:
            if self.subreddits is None:
                self.subreddits = ["stocks", "investing"]  # Default subreddits if none are provided

            results = []
            query = f'"{share_name}"'  # Use quotes for better match
            
            for subreddit in self.subreddits:
                posts = self.reddit.subreddit(subreddit).search(query, sort='new', limit=limit)
                
                for post in posts:
                    results.append({
                        'title': post.title,
                        'url': post.url,
                        'created_utc': datetime.datetime.utcfromtimestamp(post.created_utc),
                        'score': post.score,
                        'num_comments': post.num_comments,
                        'subreddit': post.subreddit.display_name  # Include subreddit name
                    })

            return results if results else "No relevant posts found."
        except Exception as e:
            return f"Error fetching Reddit posts: {e}"
        
    def get_post_details(self, post_url):
        """
        Get detailed information about a Reddit post from its URL.
        
        :param post_url: The URL of the Reddit post.
        :return: Dictionary containing post details.
        """
        try:
            # Extract post ID from URL using regex
            match = re.search(r"comments/([a-z0-9]+)/", post_url)
            if not match:
                return "Invalid Reddit post URL."
            
            post_id = match.group(1)
            post = self.reddit.submission(id=post_id)

            # Fetch post details
            post_details = {
                'title': post.title,
                'url': post.url,
                'created_utc': datetime.fromtimestamp(post.created_utc, timezone.utc),
                'score': post.score,
                'num_comments': post.num_comments,
                'subreddit': post.subreddit.display_name,
                'author': post.author.name if post.author else 'Unknown',
                'content': post.selftext,  # The text content of the post
                'top_comments': []
            }

            # Fetch top 5 comments (sorted by best)
            post.comments.replace_more(limit=0)  # Ensure we get all comments
            top_comments = sorted(post.comments, key=lambda x: x.score, reverse=True)[:5]
            
            for comment in top_comments:
                post_details['top_comments'].append({
                    'author': comment.author.name if comment.author else 'Unknown',
                    'text': comment.body,
                    'score': comment.score
                })

            return post_details
        except Exception as e:
            return f"Error fetching Reddit post details: {e}"

class X:
    """X (Twitter) data helper using Nitter."""

    def __init__(self, start_date, end_date ):
        """
        Initializes the X class with a date range and database connection.
        
        :param start_date: Start date in 'YYYY-MM-DD' format.
        :param end_date: End date in 'YYYY-MM-DD' format.
        :param db_file: Path to the SocialMediaDB SQLite database.
        """
        self.scraper = Nitter(log_level=1, skip_instance_check=False)
        self.start_date = start_date
        self.end_date = end_date
        # self.db = SocialMediaDB()

    def search_posts_in_date_range(self, share_name, share_symbol,  max_results=10, force_scrape=False):
        def parse_tweet_date(tweet_date):
            """
            Convert tweet date from 'Mar 28, 2024 · 12:30 PM UTC' format to 'YYYY-MM-DD'.
            """
            try:
                parsed_date = datetime.datetime.strptime(tweet_date, "%b %d, %Y · %I:%M %p %Z")
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError as e:
                print(f"Error parsing date: {tweet_date} -> {e}")
                return None  # Handle errors gracefully
        """
        Searches for tweets about a given share within the specified date range
        and inserts them into the database with category 'X'.

        """
        table_name = share_symbol.upper()
        
        # Skip scraping if the table exists and force_scrape=False
        if not force_scrape and self.db.table_exists(table_name):
            print(f"Table '{table_name}' already exists. Skipping scraping.")
            return  
        
        self.db.init_table(table_name)

        try:
            print(f"{Color.BLUE}Getting tweets...{Color.RESET}")
            tweets = self.scraper.get_tweets(
                share_name, 
                mode="term", 
                since=self.start_date, 
                until=self.end_date
            )
            print(tweets)

            print(f"{Color.BLUE}Validating response...{Color.RESET}")
            if not isinstance(tweets, list):
                print(f"Unexpected response format: {tweets}")
                return

            if not tweets or len(tweets) == 0:
                print(f"{Color.RED}No tweets retrieved.{Color.RESET}")
                return
            for tweet in tweets:
                try:
                    raw_date = tweet.get("date", "")  # Example: 'Mar 28, 2024 · 12:30 PM UTC'
                    formatted_date = parse_tweet_date(raw_date)  # Convert to 'YYYY-MM-DD'
                    
                    if formatted_date is None:
                        continue  # Skip tweet if date conversion fails

                    self.db.insert_post(
                        share_symbol=table_name,
                        content=tweet.get("text", ""),
                        link=tweet.get("link", ""),
                        category="X",
                        date=formatted_date
                    )
                except Exception as e:
                    print(f"{Color.RED}Skipping a tweet due to error: {e}{Color.RESET}")

        except Exception as e:
            print(f"{Color.RED}Error fetching tweets: {e}{Color.RESET}")
    
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
        self.stock_info = self.stock.info
        self.ratios = [
            "trailingPE", "forwardPE", "ebitdaMargins", "profitMargins", "grossMargins",
            "operatingMargins", "returnOnAssets", "returnOnEquity", "currentRatio",
            "quickRatio", "debtToEquity", "priceToBook", "priceToSalesTrailing12Months",
            "enterpriseToRevenue", "enterpriseToEbitda", "pegRatio", "payoutRatio",
            "dividendRate", "dividendYield", "fiveYearAvgDividendYield"
        ]
    
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
    def __init__(self, model_name="gemini-2.0-flash-001"):
        self.client = genai.Client(http_options=HttpOptions(api_version="v1"), api_key=GEMINI_API_KEY)
        self.model_name = model_name

    def generate_prompt(self, company_name: str, headline: str) -> str:
        return (
            f"As a financial expert, analyze the sentiment of the following news headline about {company_name}.\n"
            f"Headline: '{headline}'\n"
            "Provide a one-word sentiment classification (YES, NO, or UNKNOWN) on the first line, followed by a concise explanation."
        )

    def get_sentiment_score(self, company_name: str, headline: str):
        prompt = self.generate_prompt(company_name, headline)
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        
        response_text = response.text.strip()
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

    x_api = X(
        start_date="2024-01-01",
        end_date="2024-03-29"
    )
    
    tweets = x_api.search_posts_in_date_range(
        share_name="Bajaj Finance",
        share_symbol="BAJFINANCE",

    )

    print(tweets)

    # print(tweets)

    #####################################################################################################################3
    # Sentiment Analyzer Algo
    
    # analyzer = SentimentAnalyzer()
    # result = analyzer.get_sentiment_score("Apple Inc.", "Apple releases new MacBook Pro with M3 chip.")
    # print(result)


    

    pass
