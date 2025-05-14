from agents.utils.prompts import bullish_prompt, bearish_prompt
from agents.utils.debate_utils import DebateEngine
from agents.utils.helpers import load_file
from agents.db.db import ResearchTeamDebate, AnalystReport, DB

import pandas as pd
from datetime import datetime

class Researchers(object):
    """docstring for Researchers."""
    def __init__(self, DB_PATH):
        self.engine = DebateEngine(DB_PATH)
        
        self.db = DB(DB_PATH)

    def get_reports(self, analysis_date, ticker):

        formatted_date = datetime.strptime(analysis_date, "%Y-%m-%d").date()
        print("----------------------------")
        print(formatted_date)
        reports = self.db.read(
            AnalystReport,
            ticker = ticker,
            date = formatted_date
        )

        report_contents = """"""

        for report in reports:
            report_contents += f"{report.date} | {report.ticker}"
            report_contents += "\n"
            report_contents += report.category
            report_contents += "\n"
            report_contents += report.content

        # print(report_contents)
        return report_contents

    def generate_agent_context(self, date, ticker):

        report_contents = self.get_reports(analysis_date=date, ticker=ticker)

        # Defining agents
        agent_contexts = []
        agent_contexts.append([{"role": "user", "content": bullish_prompt.format(report_content=report_contents)}])
        agent_contexts.append([{"role": "user", "content": bearish_prompt.format(report_content=report_contents)}])

        agent_desc = ["Bullish", "Bearish"]

        return agent_contexts, agent_desc


    def debate(self, date, ticker):
        agent_contexts, agent_desc = self.generate_agent_context(date=date, ticker=ticker) 
        self.engine.execute_rounds(
            date=date,
            ticker=ticker,
            agent_contexts=agent_contexts,
            agent_desc=agent_desc,
            num_rounds=2,
        )

    def read_debate(self, ticker, till_date):
        cutoff_date = datetime.strptime(till_date, "%Y-%m-%d")
        data = self.db.read(
            ResearchTeamDebate, 
            ResearchTeamDebate.date < cutoff_date,  # Condition with `<`
            ticker=ticker  # Direct equality using `==`
        )

        # Convert to DF
        df = pd.DataFrame([row.__dict__ for row in data])
        df.drop(columns=["_sa_instance_state"], inplace=True, errors="ignore")  # Remove SQLAlchemy metadata column
        return df

