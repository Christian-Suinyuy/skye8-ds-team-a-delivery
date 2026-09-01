import psycopg
from dotenv import load_dotenv
import os

load_dotenv()
connection_string = os.getenv("DATABASE_STRING")

connenction = psycopg.connect(connection_string if connection_string else "")