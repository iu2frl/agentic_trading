from agents.utils.analyst_utils import ShareData, NewsData, ScreenerData
from agents.utils.llm_utils import DeepSeekV3, GeminiFlash
from agents.utils.prompts import technicals_prompt, fundamentals_prompt, news_prompt
from agents.db.db import Fundamentals, News, Technicals, AnalystReport, DB

from agents.utils.helpers import Color

from datetime import datetime
from functools import reduce
from pprint import pprint
import time
import os

import pandas as pd

class Analyst:
    """Generates concise detailed REPORTS for
        - Market Data (Technical Indicators)
        - Fundamental Data
        - News
    """
    def __init__(
            self, 
            ticker,
            DB_PATH,
            start_date = None, 
            end_date = None,


        ):
        self.ticker= ticker
        self.start_date = start_date
        self.end_date=end_date
        self.db_path = DB_PATH

        # self.socialmedia= SocialMedia()

        # self.share = ShareData(ticker)
        # self.share_name = self.share.get_share_name()

        self.screener_data = ScreenerData()
        self.newsapi = NewsData()
        self.llm = GeminiFlash()

        # Databases
        self.db = DB(DB_PATH=DB_PATH)

    def write_output(
            self, 
            content,
            file_path
            ):
        if file_path==None:
            print("No file path mentioned.")
        else:
            with open(file_path, "w") as f:
                f.write(content)
                f.close()
            print(f"Saved output at : {file_path}")

    def generate_report(self,prompt):
        report = self.llm.call(prompt)
        return report        

    def merge_dfs(self, dfs):

        # Merge all DataFrames on 'Date' using outer join
        merged_df = reduce(lambda left, right: pd.merge(left, right, on='Date', how='outer'), dfs)

        # Convert 'Date' to datetime for proper sorting
        merged_df['Date'] = pd.to_datetime(merged_df['Date'])

        # Sort by Date
        merged_df = merged_df.sort_values(by='Date').reset_index(drop=True)
        return merged_df

    def format_news_date(self, date_str):
        # Remove timezone information if present
        date_str = date_str.split(', ')[0]
        
        # Parse the date string
        parsed_date = datetime.strptime(date_str, "%m/%d/%Y").date()  # Return a date object
        
        return parsed_date

    def scrape_market(self, start_date, end_date):
        # Print initial message with color
        print(Color.CYAN + f"Fetching technical data from {self.start_date} to {self.end_date}..." + Color.RESET)
        
        # Fetching technical indicators
        technical_data = self.share.get_technical_indicators(
            start_date, 
            end_date
            )

        for date, row in technical_data.iterrows():

            technical_record = Technicals(
                ticker = self.ticker,
                date = pd.to_datetime(date),  # Ensure it's in datetime format
                open = row["Open"],
                high = row["High"],
                low = row['Low']   ,     
                close = row['Close'],   
                volume = row['Volume'],        
                rsi = row['RSI']       , 
                adx = row['ADX']     ,
                bb_lower = row['BB_lower'] ,   
                bb_middle = row['BB_middle'],     
                bb_upper = row['BB_upper']   ,     
                atr = row['ATR']         ,
                vwma = row['VWMA']        , 
                cci = row['CCI']       ,
                macd = row['MACD']  ,
                macd_signal = row['MACD_signal']
            )

            self.db.create(technical_record)

        # pprint(technical_data)
        
    def scrape_news(self, share_name, max_results=100):

        articles = self.newsapi.search_news(
            query=share_name,
            start_date=self.start_date,
            end_date=self.end_date,
            max_results=max_results
        )
        for article in articles:
            # pprint(article)
            news_data= News(
                 date = self.format_news_date(article['date']),
                 ticker = self.ticker,
                 link = article['link'],
                 source = article['source']['name'],
                #  content = article['content'], update latest after extraction
                 title = article['title'],
             )
            self.db.create(news_data)

            # print(article['title'], "|", article['date'])

    def scrape_fundamentals(
            self,
            company_id,
            ):
        
        # bs_a = self.share.get_balance_sheet(period='annual').to_string()
        # bs_q = self.share.get_balance_sheet(period='quarterly').to_string()
        # is_a = self.share.get_income_statement(period='annual').to_string()
        # is_q = self.share.get_income_statement(period='quarterly').to_string()
        # shareholding = self.share.get_shareholding().to_string()
        # ratios = self.share.get_available_ratios()

        print(Color.CYAN + "Fetching data from screener..." + Color.RESET)

        # Adding sleep delay before making requests
        time.sleep(2)  # 2 seconds delay to avoid rapid requests

        pe_data = self.screener_data.pe(company_id=company_id)
        print(Color.GREEN + "Successfully fetched PE ratio data!" + Color.RESET)

        time.sleep(2)  # Sleep delay before next request
        ev_multiple_data = self.screener_data.ev_multiple(company_id=company_id)
        print(Color.GREEN + "Successfully fetched EV Multiple data!" + Color.RESET)

        time.sleep(2)  # Sleep delay before next request
        pbv_data = self.screener_data.pbv(company_id=company_id)
        print(Color.GREEN + "Successfully fetched PBV data!" + Color.RESET)

        time.sleep(2)  # Sleep delay before next request
        market_cap_to_sales_data = self.screener_data.market_cap_to_sales(company_id=company_id)
        print(Color.GREEN + "Successfully fetched Market Cap to Sales data!" + Color.RESET)

        dfs = [pe_data, ev_multiple_data, pbv_data, market_cap_to_sales_data]
        merged_df = self.merge_dfs(dfs)

        
      
        for i, row in merged_df.iterrows():
            date = merged_df.loc[i, 'Date']
            pe = merged_df.loc[i, 'Price to Earning']
            ev_to_ebitda = merged_df.loc[i, 'EV Multiple']
            pb = merged_df.loc[i, 'Price to book value']
            mcap_to_sales = merged_df.loc[i, 'Market Cap to Sales']

            fundamentals_data = Fundamentals(
                date=date,
                ticker=self.ticker,
                company_id=company_id,
                pe=pe,
                ev_to_ebitda=ev_to_ebitda,
                pb=pb,
                mcap_to_sales=mcap_to_sales,
            )

            self.db.create(fundamentals_data)
            print(f"Inserted record for {date}")

    # Analyst Report Generations
    def fundamentals(
            self,
            till_date, 
        ):
        
        if not till_date:
            print("Please provide till_date : to gen report")
            return None
    
        cutoff_date = datetime.strptime(till_date, "%Y-%m-%d")
        
        data = self.db.read(
            Fundamentals, 
            Fundamentals.date < cutoff_date,  # Condition with `<`
            ticker=self.ticker  # Direct equality using `==`
        )

        # Convert to DF
        df = pd.DataFrame([row.__dict__ for row in data])
        df.drop(columns=["_sa_instance_state"], inplace=True, errors="ignore")  # Remove SQLAlchemy metadata column
           
        if len(df) == 0:
            return

        # Get the share name

        # Prepare the prompt for report generation
        prompt = fundamentals_prompt.format(
            share_name=self.share_name,
            content=df.to_string()
        )
        print("=======================")
        print(f"PROMPT \n\n {prompt}")
        print("=======================")
        # print(prompt)
        # Generate the report
        print(Color.YELLOW + "Generating the report..." + Color.RESET)
        report = self.generate_report(prompt=prompt)

        # print("=======================")
        # print(f"REPORT \n\n {report}")
        # print("=======================")

        # Save report output
        report_data = AnalystReport(
            date=cutoff_date,
            ticker=self.ticker,
            category="Fundamental",
            content = report,
            model = self.llm.model
        )
        self.db.create(report_data)
        print(Color.GREEN + "Saved report to DB" + Color.RESET)

    def market(
            self,
            till_date
            ):

        if not till_date:
            print("Please provide till_date : to gen report")
            return None
    
        cutoff_date = datetime.strptime(till_date, "%Y-%m-%d")
        
        data = self.db.read(
            Technicals, 
            Technicals.date < cutoff_date,  # Condition with `<`
            ticker=self.ticker  # Direct equality using `==`
        )

        # Convert to DF
        df = pd.DataFrame([row.__dict__ for row in data])
        df.drop(columns=["_sa_instance_state"], inplace=True, errors="ignore")  # Remove SQLAlchemy metadata column
        df = df.drop(columns=['open', 'high', 'low'], axis=1)

        # Prepare the prompt for report generation
        prompt = technicals_prompt.format(
            share_name=self.share_name,
            content=df.to_string()
        )

        print("=======================")
        print(f"PROMPT \n\n {prompt}")
        print("=======================")

        # Generate the report
        print(Color.YELLOW + "Generating the report..." + Color.RESET)
        report = self.generate_report(prompt=prompt)

        # Save report output
        report_data = AnalystReport(
            date=cutoff_date,
            ticker=self.ticker,
            category="Technical",
            content = report,
            model = self.llm.model
        )
        self.db.create(report_data)
        print(Color.GREEN + "Saved report to DB" + Color.RESET)

    def news(self, till_date):
        if not till_date:
            print("Please provide till_date : to gen report")
            return None
        content = ""

        for idx, row in df.iterrows():
            text = f"""{df.loc[idx, 'date']} | {df.loc[idx, 'ticker']} | {df.loc[idx, 'source']}
News Headline : {df.loc[idx, 'title']}

"""
            content += "\n"
            content += text

        prompt = news_prompt.format(
            share_name = self.share_name,
            content = content
        )

        print("=======================")
        print(f"PROMPT \n\n {prompt}")
        print("=======================")
        # print(prompt)
        # Generate the report
        print(Color.YELLOW + "Generating the report..." + Color.RESET)
        report = self.generate_report(prompt=prompt)

        # print("=======================")
        # print(f"REPORT \n\n {report}")
        # print("=======================")

        # Save report output
        report_data = AnalystReport(
            date=cutoff_date,
            ticker=self.ticker,
            category="News",
            content = report,
            model = self.llm.model
        )
        self.db.create(report_data)
        print(Color.GREEN + "Saved report to DB" + Color.RESET)

        pass

    # Read DB

    def read_reports(self, till_date):
        cutoff_date = datetime.strptime(till_date, "%Y-%m-%d")
        
        data = self.db.read(
            AnalystReport, 
            AnalystReport.date < cutoff_date,  # Condition with `<`
            ticker=self.ticker  # Direct equality using `==`
        )
        # Convert to DF
        df = pd.DataFrame([row.__dict__ for row in data])
        df.drop(columns=["_sa_instance_state"], inplace=True, errors="ignore")  # Remove SQLAlchemy metadata column
        return df

    def read_news(self, till_date):
        cutoff_date = datetime.strptime(till_date, "%Y-%m-%d")
        
        data = self.db.read(
            News, 
            News.date < cutoff_date,  # Condition with `<`
            ticker=self.ticker  # Direct equality using `==`
        )
        # Convert to DF
        df = pd.DataFrame([row.__dict__ for row in data])
        df.drop(columns=["_sa_instance_state"], inplace=True, errors="ignore")  # Remove SQLAlchemy metadata column
        df = df.drop(columns=['content'], axis=1)
        return df
    
    def read_fundamentals(self, till_date):
        cutoff_date = datetime.strptime(till_date, "%Y-%m-%d")
        
        data = self.db.read(
            Fundamentals, 
            Fundamentals.date < cutoff_date,  # Condition with `<`
            ticker=self.ticker  # Direct equality using `==`
        )
        # Convert to DF
        df = pd.DataFrame([row.__dict__ for row in data])
        df.drop(columns=["_sa_instance_state"], inplace=True, errors="ignore")  # Remove SQLAlchemy metadata column
        return df

    def read_technicals(self, till_date):
        cutoff_date = datetime.strptime(till_date, "%Y-%m-%d")
        
        data = self.db.read(
            Technicals, 
            Technicals.date < cutoff_date,  # Condition with `<`
            ticker=self.ticker  # Direct equality using `==`
        )
        # Convert to DF
        df = pd.DataFrame([row.__dict__ for row in data])
        df.drop(columns=["_sa_instance_state"], inplace=True, errors="ignore")  # Remove SQLAlchemy metadata column
        return df
