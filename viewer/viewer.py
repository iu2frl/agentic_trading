import gradio as gr
import pandas as pd
import plotly.graph_objs as go
import numpy as np

from config.settings import *
from simulation.engine import Engine

# Config
#======================================================================
engine = Engine(
        ticker=SHARE,
        DB_PATH=DB_PATH,
        start_date=START_DATE,
        end_date=END_DATE
    )
initial_value = 100_000

# Helper Functions
#======================================================================
def start_news_search():
    if not engine.analyst.db.table_exists(NEWS_TABLE):
        engine.analyst.scrape_news(share_name=SHARE_NAME)
        return pd.DataFrame({"INFO":"News scrape initiated..."}, index=[0]) 
    else:
        return pd.DataFrame({"INFO":"News results already exist."}, index=[0]) 

def load_news_results():
    data = engine.analyst.read_news(till_date=TILL_DATE)
    return pd.DataFrame(data)

def start_fundamental_search():
    if not engine.analyst.db.table_exists(FUNDAMENTALS_TABLE):
        engine.analyst.scrape_news(share_name=SHARE_NAME)
        return pd.DataFrame({"INFO":"Fundamentals scrape initiated..."}, index=[0]) 
    else:
        return pd.DataFrame({"INFO":"Fundamentals results already exist."}, index=[0]) 

def load_fundamental_results():
    data = engine.analyst.read_fundamentals(till_date=TILL_DATE)
    return pd.DataFrame(data)

def start_technicals_search():
    if not engine.analyst.db.table_exists(TECHNICALS_TABLE):
        engine.analyst.scrape_news(share_name=SHARE_NAME)
        return pd.DataFrame({"INFO":"Technicals scrape initiated..."}, index=[0]) 
    else:
        return pd.DataFrame({"INFO":"Technicals results already exist."}, index=[0]) 

def load_technicals_results():
    data = engine.analyst.read_technicals(till_date=TILL_DATE)
    return pd.DataFrame(data)

# ANALYST REPORTS
def start_analyst_report():
    if not engine.analyst.db.table_exists(REPORTS_TABLE):
        engine.analyst.scrape_news(share_name=SHARE_NAME)
        return pd.DataFrame({"INFO":"Analyst Reports Generation sequence initiated..."}, index=[0]) 
    else:
        return pd.DataFrame({"INFO":"Analyst Reports already exist."}, index=[0]) 

def load_analyst_reports():
    data = engine.analyst.read_reports(till_date=TILL_DATE)
    return pd.DataFrame(data)

def start_research():
    if not engine.analyst.db.table_exists(DEBATE_TABLE):
        engine.debate()
        return pd.DataFrame({"INFO":"Research Debate sequence initiated..."}, index=[0]) 
    else:
        return pd.DataFrame({"INFO":"Research Debates already exist."}, index=[0]) 

def load_research():
    data = engine.researchers.read_debate(ticker=SHARE, till_date=TILL_DATE)
    return pd.DataFrame(data)


def start_trade():
    if not engine.analyst.db.table_exists(DECISION_TABLE):
        engine.trade_long_short()
        return pd.DataFrame({"INFO":"Manager decision sequence initiated..."}, index=[0]) 
    else:
        return pd.DataFrame({"INFO":"Manager decision already exist."}, index=[0]) 

def load_trade():
    data = engine.manager.read_trade_long_short(ticker=SHARE, till_date=TILL_DATE)
    return pd.DataFrame(data)

from utils.utils import results_figure, macd_returns

# Technical Trading results
#======================================================================

from utils.utils import buy_and_hold, long_short_trade

technicals_df = load_technicals_results()
trade_df = load_trade()

macd_df, average_profit, average_loss, buy_triggers, sell_triggers, max_drawdown = macd_returns(technicals_df)
buy_hold = buy_and_hold(technicals_df.set_index('date')[['close']])
long_short = long_short_trade(trade_df, technicals_df.set_index('date')['close'])

# results = pd.DataFrame(
#     [
#     {"CATEGORY" : "Market ",  "MODEL" :  "Buy n Hold",
#         "CR%" : , "ARR%" : , "SR%" :  },

#      {"CATEGORY" : "Rule Based ",  "MODEL" :  "Buy n Hold",
#         "CR%" : , "ARR%" : , "SR%" :  }
#     ]
# )

# Visualizations
#======================================================================
dfs = [buy_hold, macd_df.set_index('date')[['Net_Return']], long_short]
results_df = pd.concat(dfs, axis=1, join='inner')  # or join='outer' if you want all dates

def visualize_results():
    df=results_df
    fig = results_figure(df)
    return fig

# Gradio UI
#======================================================================
with gr.Blocks() as demo:
    # Fixed Config Section
        # Fixed Config Section
    with gr.Column():
        gr.Markdown("""# LLM Trader
## Preset Configuration""")
    with gr.Row():
        with gr.Column(scale=1):
            share_name = gr.Textbox(label="Share Name", value=SHARE)
        with gr.Column(scale=1):
            start_date = gr.Textbox(label="Start Date (YYYY-MM-DD)", value=START_DATE)
        with gr.Column(scale=1):
            end_date = gr.Textbox(label="End Date (YYYY-MM-DD)", value=END_DATE)
        with gr.Column(scale=1):
            model = gr.Textbox(label='LLM Type', value=LLM_TYPE)
        with gr.Column(scale=1):
            model = gr.Textbox(label='Model', value=MODEL)
        with gr.Column(scale=1):
            model = gr.Textbox(label='DB Path', value=DB_PATH)

    # Tabs Section
    with gr.Tabs():
        with gr.Tab("Web Search"):
            gr.Markdown(
            f"""
            # Web Search Data for share : {share_name.value} 
            """)
            # NEWS
            with gr.Row():
                news_search_btn = gr.Button("Start Web Search")
                news_load_btn = gr.Button("Load Web Results")
            news_output = gr.Dataframe(label="News Search Results")
            news_search_btn.click(fn=start_news_search, outputs=news_output)
            news_load_btn.click(fn=load_news_results, outputs=news_output)

            # FUNDA
            with gr.Row():
                fundamentals_search_btn = gr.Button("Start Funda Search")
                fundamentals_load_btn = gr.Button("Load Funda Results")

            fundamentals_output = gr.Dataframe(label="Fundamental Data Results")
            fundamentals_search_btn.click(fn=start_fundamental_search, outputs=fundamentals_output)
            fundamentals_load_btn.click(fn=load_fundamental_results, outputs=fundamentals_output)

            # TECHN
            with gr.Row():
                technicals_search_btn = gr.Button("Start Technicals Search")
                technicals_load_btn = gr.Button("Load Technicals Results")

            technicals_output = gr.Dataframe(label="Technical Data Results")
            technicals_search_btn.click(fn=start_technicals_search, outputs=technicals_output)
            technicals_load_btn.click(fn=load_technicals_results, outputs=technicals_output)

        with gr.Tab("Report Analysis"):

            with gr.Row():
                start_reports_btn = gr.Button("Start Analyst reporting...")
                load_reports_btn = gr.Button("Load Analyst reports")

            reports_output = gr.Dataframe(label="Analyst summarization Reports")
            start_reports_btn.click(fn=start_analyst_report, outputs=reports_output)
            load_reports_btn.click(fn=load_analyst_reports, outputs=reports_output)

        with gr.Tab("Research"):
            with gr.Row():
                start_research_btn = gr.Button("Start Research Debate")
                load_research_btn = gr.Button("Load Research Debates")

            debate_output = gr.Dataframe(label="Research Team Debate")
            start_research_btn.click(fn=start_research, outputs=debate_output)
            load_research_btn.click(fn=load_research, outputs=debate_output)

        with gr.Tab("Manager Decision"):
            with gr.Row():
                start_trade_btn = gr.Button("Start Trade")
                load_trade_btn = gr.Button("Load Manager Decisions")

            trade_output = gr.Dataframe(label="Research Team Debate")
            start_trade_btn.click(fn=start_trade, outputs=trade_output)
            load_trade_btn.click(fn=load_trade, outputs=trade_output)

        with gr.Tab("Final Results"):
            result_btn = gr.Button("Visualize Results")
            result_plot = gr.Plot(label="Result Chart")
            result_table = gr.Dataframe(label="Summary Table")

            # gr.Markdown(
            # f"""
            # ### Initial Investment: {initial_value}
            # ### Final Value of Investment: {df['Net_Return'].iloc[-1]:.2f}
            # ### Total Return: {df['Cumulative_Return'].iloc[-1] * 100:.2f}%
            # ### Number of Buy Triggers: {buy_triggers}
            # ### Number of Sell Triggers: {sell_triggers}
            # ### Maximum Drawdown: {max_drawdown:.2f}
            # ### Average Profit per Trade: {average_profit:.2f}
            # ### Average Loss per Trade: {average_loss:.2f}
            # """)
            # gr.DataFrame(results_df)
            result_btn.click(
                fn=visualize_results, 
                inputs=[],
                outputs=[result_plot]
                )

demo.launch()
