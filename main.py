from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from summarize_logic import summarize_text_async
from pymongo import MongoClient
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timedelta  # ต้อง import timedelta
import pandas as pd
import json
from db import get_db


app = FastAPI()

# เชื่อมต่อ MongoDB

db = get_db()  # เชื่อมต่อกับฐานข้อมูล
collection = db["news"]


# @app.get("/")
# async def check_connection():
#     try:
#         # เช็คการเชื่อมต่อกับ MongoDB
#         client.admin.command('ping')
#         return {"status": "connected to MongoDB"}
#     except ConnectionError:
#         return {"status": "failed to connect to MongoDB"}


@app.get("/get_all_news")
async def get_all_news():
    try:
        news_items = list(collection.find().limit(10))
        # Debug: Print the fetched news items
        print("Fetched News Items:", news_items)
        if news_items:
            a = []
            for item in news_items:
                
                # Assuming 'summarize_text' is a function that summarizes the content
                a.append(item['Content'])
            return {"news": a}
        else:
            return {"message": "No news found"}
    except Exception as e:
        return {"error": str(e)}


def convert_objectid(item):
    item['_id'] = str(item['_id'])  # แปลง ObjectId เป็น string
    return item

@app.get("/get_all_news_2")
async def get_all_news():
    try:
        news_items = list(collection.find().limit(10))
        if news_items:
            results = []
            for item in news_items:
                results.append(convert_objectid(item))
            return {"news": results}
        else:
            return {"message": "No news found"}
    except Exception as e:
        return {"error": str(e)}
    

# ex.http://127.0.0.1:8000/get_news_by_date?start_date=2025-01-01&end_date=2025-04-30
@app.get("/get_news_by_date")
async def get_news_by_date(start_date: str = Query(...), end_date: str = Query(...)):
    try:
        # แปลงวันที่เป็น datetime
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # รวมถึงวันสุดท้าย

        # ดึงข้อมูลจาก MongoDB ในช่วงวันที่ที่กำหนด
        pipeline = [
            {
                "$match": {
                    "Date": {
                        "$gte": start,
                        "$lt": end
                    }
                }
            },
            {
                "$sort": {
                    "Views": -1  # จัดเรียงจากมากไปน้อยก่อน group
                }
            },
            {
                "$group": {
                    "_id": "$Category",
                    "top_news": {"$first": "$Views"},
                    "doc": {"$first": "$$ROOT"}
                }
            },
            {
                "$sort": {
                    "top_news": -1  # เรียงกลุ่มตาม Views มากไปน้อย
                }
            }
        ]
        docs = list(collection.aggregate(pipeline))
        print(docs)
        
        if not docs:
            return {"message": "ไม่พบข้อมูลในช่วงวันที่ที่ระบุ"}
        
        # แปลง ObjectId เป็น string
        results = [convert_objectid_2(doc) for doc in docs]
        docs_only = [doc["doc"] for doc in results]
        
        # ส่งผลลัพธ์เป็น JSON
        return {"news": docs_only}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# ฟังก์ชันแปลง ObjectId เป็น string
def convert_objectid_2(item):
    # แปลง ObjectId เป็น string ใน '_id' และ doc
    item['_id'] = str(item['_id'])  # แปลง ObjectId เป็น string
    # ถ้า doc มีฟิลด์ '_id' ภายใน, ให้แปลง _id ภายใน doc ด้วย
    if 'doc' in item:
        item['doc']['_id'] = str(item['doc']['_id'])
    return item


# FastAPI endpoint สำหรับดึงข่าวในช่วงวันที่ที่กำหนด
# http://127.0.0.1:8000/summerize?start_date=2025-02-01&end_date=2025-04-30
import asyncio
from fastapi import FastAPI, HTTPException, Query
from datetime import datetime, timedelta
import pandas as pd

@app.get("/summerize")
async def get_news_by_date(start_date: str = Query(...), end_date: str = Query(...)):
    try:
        # แปลงวันที่เป็น datetime
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # รวมถึงวันสุดท้าย

        # ดึงข้อมูลจาก MongoDB ในช่วงวันที่ที่กำหนด
        pipeline = [
            {
                "$match": {
                    "Date": {
                        "$gte": start,
                        "$lt": end
                    }
                }
            },
            {
                "$sort": {
                    "Views": -1  # จัดเรียงจากมากไปน้อยก่อน group
                }
            },
            {
                "$group": {
                    "_id": "$Category",
                    "top_news": {"$first": "$Views"},
                    "doc": {"$first": "$$ROOT"}
                }
            },
            {
                "$sort": {
                    "top_news": -1  # เรียงกลุ่มตาม Views มากไปน้อย
                }
            }
        ]
        docs = list(collection.aggregate(pipeline))

        if not docs:
            return {"message": "ไม่พบข้อมูลในช่วงวันที่ที่ระบุ"}
        
        # แปลง ObjectId เป็น string
        results = [convert_objectid_2(doc) for doc in docs]
        docs_only = [doc["doc"] for doc in results]
        
        # แปลงผลลัพธ์เป็น pandas DataFrame
        df = pd.DataFrame(docs_only)

        # ใช้ async เพื่อสรุปข่าวทั้งหมดพร้อมกัน
        if "Content" in df.columns:
            summaries = await asyncio.gather(*[summarize_text_async(content) for content in df["Content"]])
            df["Summary"] = summaries

        # ส่งผลลัพธ์ที่มีสรุปข้อความ
        return {"news": df.to_dict(orient="records")}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
