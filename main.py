from simulation.engine import Engine
from config.settings import SHARE, DB_PATH
from utils.utils import start_date, end_date

def init_engine():
    engine = Engine(
        ticker=SHARE,
        DB_PATH=DB_PATH,
        start_date=start_date,
        end_date=end_date
    )
    return engine

# Step 1 : Generate Analyst Reports
def generate_analyst_reports():
    pass

# Step 2 : Generate Research debates
def generate_research_debates():
    pass

# Step 3 : Trading Decision : Long/ Short
def generate_trades():
    pass

if __name__ == "__main__":





    pass