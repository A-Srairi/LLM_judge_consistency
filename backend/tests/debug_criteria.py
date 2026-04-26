import asyncio
import os
os.environ.pop("SSL_CERT_FILE", None)
from dotenv import load_dotenv
load_dotenv()

import httpx

async def test():
    payload = {
        "prompt": "Sally has 3 brothers. Each brother has 2 sisters. How many sisters does Sally have?",
        "response_a": "To solve this, we need to carefully account for each sisterly relationship...",
        "response_b": "Sally has 1 sister. All 3 brothers share the same sisters.",
        "judges": ["groq/llama-3.3-70b-versatile"],
        "criteria": ["accuracy", "helpfulness", "conciseness"],
        "n_samples": 1,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post("http://127.0.0.1:8000/audit", json=payload)
        data = response.json()

        for v in data["verdicts"]:
            print(f"judge: {v['judge_model']}")
            print(f"winner: {v['winner']}")
            print(f"criteria_scores: {v['criteria_scores']}")
            print(f"reasoning: {v['reasoning'][:100]}")
            print()

asyncio.run(test())