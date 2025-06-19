from agents.utils.llm_utils import Gpt4Free
from agents.utils.prompts import manager_prompt, manager_prompt_long_short
from agents.db.db import ManagerDecision, DB, ResearchTeamDebate, ManagerDecisionLongShort

import pandas as pd

from datetime import datetime
import re

class Manager:
    def __init__(self, DB_PATH):
        self.llm = Gpt4Free()
        self.db = DB(DB_PATH)

    def get_debate(self, date, ticker):
        
        formatted_date = datetime.strptime(date, "%Y-%m-%d").date()
        debate_content = self.db.read(
            ResearchTeamDebate,
            ticker = ticker,
            date = formatted_date
        )[0]

        return debate_content

    def get_prev_trades(self, ticker):
        prev_trades = self.db.read(
            ManagerDecision,
            ticker = ticker,
        )
        df = pd.DataFrame([row.__dict__ for row in prev_trades])
        df.drop(columns=["_sa_instance_state"], inplace=True, errors="ignore")  # Remove SQLAlchemy metadata column

        if len(df) >0:
            df = df.drop(columns=['reason'], axis=1)

        return df.to_string()


    def extract_decision(self, text):
        match = re.search(r'final recommendation:\s*(buy|sell|hold)', text, re.IGNORECASE)
        if match:
            decision = match.group(1).lower().capitalize()  # Ensures proper casing: Buy, Sell, Hold
            return decision
        else:
            print("No recommendation found.")
            return None
        
    def extract_decision_long_short(self, text):
        match = re.search(r'final recommendation:\s*(long|short)', text, re.IGNORECASE)
        if match:
            decision = match.group(1).lower().capitalize()  # Ensures proper casing: Buy, Sell, Hold
            return decision
        else:
            print("No recommendation found.")
            return None


    def trade(self, date, ticker):
        debate = self.get_debate(date=date, ticker=ticker)

        # prev_trades = self.get_prev_trades(ticker=ticker)

        prompt = manager_prompt.format(
            share_name = ticker,
            bullish_argument = debate.bullish,
            bearish_argument = debate.bearish,
        )

        print("================================================")
        print(f"Sending LLM Call...")
        print("================================================")
        response = self.llm.call(prompt=prompt)
        decision = self.extract_decision(response)

        manager_record = ManagerDecision(
            date = datetime.strptime(date, "%Y-%m-%d"),
            ticker = ticker,
            reason = response,
            decision = decision
        )

        self.db.create(manager_record)


    def trade_long_short(self, date , ticker):


        # manager_prompt_long_short

        debate = self.get_debate(date=date, ticker=ticker)

        # prev_trades = self.get_prev_trades(ticker=ticker)

        prompt = manager_prompt_long_short.format(
            share_name = ticker,
            bullish_argument = debate.bullish,
            bearish_argument = debate.bearish,
        )

        print("================================================")
        print(f"Sending LLM Call...")
        print("================================================")
        response = self.llm.call(prompt=prompt)
        decision = self.extract_decision_long_short(response)

        manager_record = ManagerDecisionLongShort(
            date = datetime.strptime(date, "%Y-%m-%d"),
            ticker = ticker,
            reason = response,
            decision = decision
        )

        self.db.create(manager_record)

    def read_trade_long_short(self, ticker, till_date):
        cutoff_date = datetime.strptime(till_date, "%Y-%m-%d")
        data = self.db.read(
            ManagerDecisionLongShort, 
            ManagerDecisionLongShort.date < cutoff_date,  # Condition with `<`
            ticker=ticker  # Direct equality using `==`
        )

        # Convert to DF
        df = pd.DataFrame([row.__dict__ for row in data])
        df.drop(columns=["_sa_instance_state"], inplace=True, errors="ignore")  # Remove SQLAlchemy metadata column
        return df

