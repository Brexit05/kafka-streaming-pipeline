import os
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("url")

symbol = os.getenv("symbols")
if symbol is None:
    SYMBOL = []
else:
    SYMBOL = symbol.split(",")


PARAMS = {
        'ids': ','.join(SYMBOL),
        'vs_currencies': 'usd',
        'include_market_cap': 'true',
        'include_24hr_change': 'true',
        'include_24hr_vol': 'true',
        'include_last_updated_at': 'true'
        }

POSTGRES_DB = os.getenv("POSTGRES_DB", "crypto_db")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

PG_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres:5432/{POSTGRES_DB}"

