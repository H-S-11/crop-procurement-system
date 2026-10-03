import pandas as pd
from sqlalchemy import create_engine
import json
import os

def load_data(engine):
    query = """
    SELECT * FROM dpcs
    """
    return pd.read_sql(query, engine)
