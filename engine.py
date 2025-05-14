from agents.analysts import Analyst
from agents.researchers import Researchers
from agents.fund_manager import Manager

from datetime import datetime, timedelta
import time

from rich import console

class Engine:
    def __init__(
            self,
            ticker,
            DB_PATH,
            start_date=None,
            end_date=None
            ):

        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.db_path = DB_PATH

        self.analyst = Analyst(ticker, DB_PATH=DB_PATH, start_date=start_date, end_date=end_date)
        self.researchers = Researchers(DB_PATH)
        self.manager = Manager(DB_PATH)

    def analyst_reports(self):
        """Generate and save all reports over the period self.start_date to self.end_date"""
        start = datetime.strptime(self.start_date, "%Y-%m-%d")
        end = datetime.strptime(self.end_date, "%Y-%m-%d")

        resume_from_date= datetime.strptime("2025-03-01", "%Y-%m-%d") 

        days = (end - start).days
        i = 1
        current = start
        while current <= end:
            # if current <= resume_from_date:
                    
            #     current += timedelta(days=1)
            #     i+=1  
            #     continue
            print("================================================")
            print(f"[{i}/{days}]Getting for date : {current}")
            print("================================================")
            formatted_date = current.strftime("%Y-%m-%d")

            # print(f"Calling fundamentals for: {formatted_date}")
            # self.analyst.fundamentals(till_date=formatted_date)
            
            # print(f"Calling Technicals for: {formatted_date}")
            # self.analyst.market(till_date=formatted_date)
            
            # print(f"Calling News Reports for: {formatted_date}")
            # self.analyst.news(till_date=formatted_date)

            current += timedelta(days=1)
            i+=1  
        print("Done")
            # break

    def debate(self):

        start = datetime.strptime(self.start_date, "%Y-%m-%d")
        end = datetime.strptime(self.end_date, "%Y-%m-%d")

        resume_from_date= datetime.strptime("2025-03-01", "%Y-%m-%d") 

        days = (end - start).days
        i = 1
        current = start
        while current <= end:

            # if current <= resume_from_date:
            #     current += timedelta(days=1)
            #     i+=1  
            #     continue
            formatted_date = current.strftime("%Y-%m-%d")
            print("================================================")
            print(f"[{i}/{days}]Debating for date : {current}")
            print("================================================")

            self.researchers.debate(date=formatted_date, ticker=self.ticker)

            current += timedelta(days=1)
            i+=1  
        print("Done")
            # break

        pass

    def trade(self):
        """Fund Manager makes a trade. """

        start = datetime.strptime(self.start_date, "%Y-%m-%d")
        end = datetime.strptime(self.end_date, "%Y-%m-%d")

        resume_from_date= datetime.strptime("2025-03-01", "%Y-%m-%d") 

        days = (end - start).days
        i = 1
        current = start
        while current <= end:

            # if current <= resume_from_date:
            #     current += timedelta(days=1)
            #     i+=1  
            #     continue
            formatted_date = current.strftime("%Y-%m-%d")
            print("================================================")
            print(f"[{i}/{days}]Trading for date : {current}")
            print("================================================")

            self.manager.trade(date=formatted_date, ticker=self.ticker)

            current += timedelta(days=1)
            i+=1  
            time.sleep(2)
        print("Done")

    def trade_long_short(self):
        """Fund Manager makes a trade. """

        start = datetime.strptime(self.start_date, "%Y-%m-%d")
        end = datetime.strptime(self.end_date, "%Y-%m-%d")

        resume_from_date= datetime.strptime("2025-03-01", "%Y-%m-%d") 

        days = (end - start).days
        i = 1
        current = start
        while current <= end:

            # if current <= resume_from_date:
            #     current += timedelta(days=1)
            #     i+=1  
            #     continue
            formatted_date = current.strftime("%Y-%m-%d")
            print("================================================")
            print(f"[{i}/{days}]Trading for date : {current}")
            print("================================================")

            self.manager.trade_long_short(date=formatted_date, ticker=self.ticker)

            current += timedelta(days=1)
            i+=1  
            time.sleep(2)
        print("Done")




            
