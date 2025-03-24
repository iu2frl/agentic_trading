from agents.utils.analyst_utils import ShareData, SocialMedia, SentimentAnalyzer
from agents.utils.prompts import market_analyst_prompt
from agents.db.db import DB


class Analyst:
    """Generates concise detailed reports for
        - Social Media
        - Market Data (Technical Indicators)
        - Fundamental Data
        - News
    """
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date=end_date

        self.socialmedia= SocialMedia()


    def llm_call(self, prompt):

        pass

    def market(self, ticker, share_name):
        share = ShareData(ticker)
        technical_data = share.get_technical_indicators(self.start_date, self.end_date)

        prompt = market_analyst_prompt.format(
            share_name=share_name,
            start_date=self.start_date,
            end_date=self.end_date,
            technical_data=technical_data.to_string(),
        )

        report = self.llm_call(prompt)
        return report


    def social_media(self, share_name, share_symbol):

        pass

    def news(self):
        pass

    def fundamentals(self):
        pass

