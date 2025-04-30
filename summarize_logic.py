from langchain_openai import ChatOpenAI
from langchain_core.runnables.base import Runnable
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()  # โหลดค่า environment จาก .env

# ฟังก์ชันสร้าง LLM
def chat_openai() -> Runnable:
    llm = ChatOpenAI(
        model="gpt-4o-mini",  # หรือ gpt-4 หากคุณมีเครดิตเพียงพอ
        temperature=0
    )
    return llm

llm = chat_openai()

# ตั้งค่า prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "คุณคือผู้ช่วยที่เชี่ยวชาญในการสรุปข่าวให้สั้น กระชับ และชัดเจน"),
    ("user", "สรุปข่าวนี้ให้หน่อย: {input}")
])

# สร้าง chain
chain = prompt | llm

# ฟังก์ชัน async สำหรับสรุปข้อความข่าว
async def summarize_text_async(text: str) -> str:
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: chain.invoke({"input": text}))
    return result.content
