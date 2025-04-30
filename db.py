from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()  # โหลด environment variables จากไฟล์ .env

def get_db():
    # ดึงค่า MONGO_URI จากไฟล์ .env
    mongo_uri = os.getenv("MONGO_URI")

    client = MongoClient(mongo_uri)
    db = client["news_db"]
    return db
