from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class DB:
    def __init__(self, DB_PATH):
        db_url = f"sqlite:///{DB_PATH}"
        self.engine = create_engine(db_url, echo=True)
        inspector = inspect(self.engine)
        
        # Check if tables exist and create them if not
        for table_name in Base.metadata.tables.keys():
            if not inspector.has_table(table_name):
                Base.metadata.create_all(self.engine)
        
        self.Session = sessionmaker(bind=self.engine)

    def create(self, obj):
        session = self.Session()
        try:
            session.add(obj)
            session.commit()
            return obj
        except Exception as e:
            session.rollback()
            print(f"Error: {e}")
        finally:
            session.close()

    def read(self, model, *conditions, **filters):
        session = self.Session()
        try:
            query = session.query(model)

            # Apply filters for direct equality conditions (column == value)
            if filters:
                query = query.filter(*[getattr(model, key) == value for key, value in filters.items()])

            # Apply more complex conditions (e.g., <, >, !=)
            if conditions:
                query = query.filter(*conditions)

            return query.all()
        finally:
            session.close()

    def update(self, model, filters, update_data):
        session = self.Session()
        try:
            records = session.query(model).filter_by(**filters)
            if records.count():
                records.update(update_data)
                session.commit()
                return records.all()
        except Exception as e:
            session.rollback()
            print(f"Error: {e}")
        finally:
            session.close()

    def delete(self, model, **filters):
        session = self.Session()
        try:
            records = session.query(model).filter_by(**filters)
            count = records.count()
            if count:
                records.delete()
                session.commit()
                return count
        except Exception as e:
            session.rollback()
            print(f"Error: {e}")
        finally:
            session.close()
    def table_exists(self, table_name: str) -> bool:
        inspector = inspect(self.engine)
        return table_name in inspector.get_table_names()

# Define models

class AnalystReport(Base):
    __tablename__ = "analyst_reports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=True, default=None)
    ticker = Column(String, nullable=True, default=None, index=True)
    category = Column(String, nullable=True, default=None)
    content = Column(Text, nullable=True, default=None)
    model = Column(Text, nullable=True, default=None) # the llm used

class ResearchTeamDebate(Base):
    __tablename__ = "research_team_debate"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=True, default=None)
    ticker = Column(String, nullable=True, default=None, index=True)
    bullish = Column(Text, nullable=True, default=None)
    bearish = Column(Text, nullable=True, default=None)

class RiskTeamDebate(Base):
    __tablename__ = "risk_team_debate"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=True, default=None)
    ticker = Column(String, nullable=True, default=None, index=True)
    aggressive = Column(Text, nullable=True, default=None)
    neutral = Column(Text, nullable=True, default=None)
    conservative = Column(Text, nullable=True, default=None)

class ManagerDecision(Base):
    __tablename__ = "manager_decision"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=True, default=None)
    ticker = Column(String, nullable=True, default=None, index=True)
    reason = Column(Text, nullable=True, default=None)
    decision = Column(Text, nullable=True, default=None)

class ManagerDecisionLongShort(Base):
    __tablename__ = "manager_decision_long_short"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=True, default=None)
    ticker = Column(String, nullable=True, default=None, index=True)
    reason = Column(Text, nullable=True, default=None)
    decision = Column(Text, nullable=True, default=None)

class Fundamentals(Base):
    __tablename__ = "fundamentals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=True, default=None)
    ticker = Column(String, nullable=True, default=None, index=True)
    company_id = Column(Integer, nullable=True, default=None)
    pe = Column(Float, nullable=True, default=None)
    ev_to_ebitda = Column(Float, nullable=True, default=None)
    pb = Column(Float, nullable=True, default=None)
    mcap_to_sales = Column(Float, nullable=True, default=None)

class News(Base):
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=True, default=None)
    ticker = Column(String, nullable=True, default=None, index=True)
    link = Column(String, nullable=True, default=None)
    source = Column(String, nullable=True, default=None)
    content = Column(String, nullable=True, default=None)
    title = Column(String, nullable=True, default=None)

class Technicals(Base):
    __tablename__ = "technicals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=True, default=None)
    ticker = Column(String, nullable=True, default=None,  index=True)   
    open =Column(Float, nullable=True, default=None)
    high = Column(Float, nullable=True, default=None)
    low =Column(Float, nullable=True, default=None)      
    close = Column(Float, nullable=True, default=None)  
    volume = Column(Float, nullable=True, default=None)       
    rsi =Column(Float, nullable=True, default=None)   
    adx =Column(Float, nullable=True, default=None)   
    bb_lower = Column(Float, nullable=True, default=None)   
    bb_middle = Column(Float, nullable=True, default=None)  
    bb_upper = Column(Float, nullable=True, default=None)       
    atr =Column(Float, nullable=True, default=None)         
    vwma = Column(Float, nullable=True, default=None)       
    cci = Column(Float, nullable=True, default=None)     
    macd = Column(Float, nullable=True, default=None)  
    macd_signal =Column(Float, nullable=True, default=None)

# Example Usage
if __name__ == "__main__":
    """
    db = DB()
    
    # Example Create
    new_report = AnalystReport(date='2025-04-03', ticker='AAPL', category='Market', content='Apple stock is strong.')
    db.create(new_report)
    
    # Example Read
    reports = db.read(AnalystReport, ticker='AAPL')
    for report in reports:
        print(report.id, report.content)
    
    # Example Update
    db.update(AnalystReport, {"ticker": "AAPL"}, {"content": "Updated content"})
    
    # Example Delete
    db.delete(AnalystReport, ticker='AAPL')
    """

    pass