"""互動式 demo 的後端：把同一份 state + questions 分別送給 Jev 與一般 LLM。

金鑰只留在伺服器端；瀏覽器只會拿到上游的原始回應與伺服器量到的毫秒數。
"""

import json
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

load_dotenv()

BASE_URL = (os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1").rstrip("/")
JEV_MODEL = os.getenv("JEV_MODEL") or "jev-latest"
LLM_MODEL = os.getenv("OPENROUTER_MODEL") or "google/gemini-3.5-flash-lite"

LLM_SYSTEM_PROMPT = """You are a classifier. Answer every question about the given state.
Reply with JSON only, no prose and no markdown, shaped exactly like:
{"<question_key>": {"answer": <value>, "confidence": <number 0-1>}}
- type "choice": answer is exactly one key from criteria.
- type "score": answer is the integer index (starting at 0) of the best matching level in criteria.
- type "noul": answer is true or false."""

app = FastAPI()
static_dir = Path(__file__).parent / "static"


class Ask(BaseModel):
    state: str | dict | list
    questions: dict


async def post_upstream(path: str, payload: dict) -> dict:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return {"ok": False, "status": 0, "ms": 0, "error": "伺服器沒有設定 OPENROUTER_API_KEY，請在 .env 填入後重新啟動。"}

    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            upstream = await client.post(
                f"{BASE_URL}{path}",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
    except httpx.HTTPError as exc:
        return {"ok": False, "status": 0, "ms": 0, "error": f"連不上 {BASE_URL}：{exc}"}
    ms = (time.perf_counter() - started) * 1000

    try:
        body = upstream.json()
    except json.JSONDecodeError:
        body = upstream.text
    return {"ok": upstream.is_success, "status": upstream.status_code, "ms": ms, "request": payload, "body": body}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/api/config")
async def config() -> dict:
    return {"jev_model": JEV_MODEL, "llm_model": LLM_MODEL, "has_key": bool(os.getenv("OPENROUTER_API_KEY"))}


@app.post("/api/jev")
async def ask_jev(ask: Ask) -> dict:
    return await post_upstream(
        "/systemone", {"model": JEV_MODEL, "state": ask.state, "questions": ask.questions}
    )


@app.post("/api/llm")
async def ask_llm(ask: Ask) -> dict:
    user_content = json.dumps({"state": ask.state, "questions": ask.questions}, ensure_ascii=False)
    return await post_upstream(
        "/chat/completions",
        {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": LLM_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        },
    )
