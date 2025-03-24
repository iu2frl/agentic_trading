import pandas as pd
import sqlite3

SENTIMENT_DB_FILE = "agents/db/sentiment_scores.db"
SOCIAL_MEDIA_DB_FILE = "agents/db/social_media.db"

class SentimentDB(object):

    """docstring for SentimentDB."""
    def __init__(self, DB_FILE=SENTIMENT_DB_FILE):
        super(SentimentDB, self).__init__()
        self.DB_FILE=DB_FILE

    def init_table(self, share_symbol):
        """Initialize a table for the given share symbol if it doesn't exist."""
        table_name = f"sentiment_{share_symbol.upper()}"  # Ensuring table names are uppercase
        with sqlite3.connect(self.DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE,
                    average_score REAL
                )
            """)
            conn.commit()

    def update_score(self, share_symbol, date, average_score):
        """Insert or update the sentiment score for a given share and date."""
        table_name = f"sentiment_{share_symbol.upper()}"
        with sqlite3.connect(self.DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO {table_name} (date, average_score)
                VALUES (?, ?)
                ON CONFLICT(date) DO UPDATE SET average_score=excluded.average_score
            """, (date, average_score))
            conn.commit()

    def date_exists(self, share_symbol, date):
        """Check if a sentiment score already exists for a given share and date."""
        table_name = f"sentiment_{share_symbol.upper()}"
        with sqlite3.connect(self.DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT 1 FROM {table_name} WHERE date = ?", (date,))
            return cursor.fetchone() is not None  # Returns True if date exists, False otherwise


    def get_sentiment_data(self, share_symbol):
        """Retrieve all sentiment scores for the given share symbol as a pandas DataFrame."""
        table_name = f"sentiment_{share_symbol.upper()}"
        with sqlite3.connect(self.DB_FILE) as conn:
            query = f"SELECT date, average_score FROM {table_name} ORDER BY date ASC"
            df = pd.read_sql_query(query, conn)
        return df
    

class SocialMediaDB(object):
    """Database for storing social media posts related to stocks."""

    def __init__(self, DB_FILE=SOCIAL_MEDIA_DB_FILE):
        super(SocialMediaDB, self).__init__()
        self.DB_FILE = DB_FILE

    def init_table(self, share_symbol):
        """Initialize a table for the given share symbol if it doesn't exist."""
        table_name = share_symbol.upper() # Ensuring table names are uppercase
        with sqlite3.connect(self.DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT,
                    link TEXT,
                    category TEXT,
                    date TEXT
                )
            """)
            conn.commit()

    def table_exists(self, table_name):
        """Check if a given table exists in the database."""
        with sqlite3.connect(self.DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            return cursor.fetchone() is not None  # Returns True if table exists, False otherwise


    def insert_post(self, share_symbol, content, link, category, date):
        """Insert a new social media post into the database."""
        table_name = share_symbol.upper()
        with sqlite3.connect(self.DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO {table_name} (content, link, category, date)
                VALUES (?, ?, ?, ?)
            """, (content, link, category, date))
            conn.commit()

    def post_exists(self, share_symbol, content):
        """Check if a specific post already exists for a given share."""
        table_name = share_symbol.upper()
        with sqlite3.connect(self.DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT 1 FROM {table_name} WHERE content = ?", (content,))
            return cursor.fetchone() is not None  # Returns True if content exists, False otherwise

    def get_posts(self, share_symbol):
        """Retrieve all social media posts for the given share symbol as a pandas DataFrame."""
        table_name = share_symbol.upper()
        with sqlite3.connect(self.DB_FILE) as conn:
            query = f"SELECT content, link, category, date FROM {table_name} ORDER BY date ASC"
            df = pd.read_sql_query(query, conn)
        return df

    