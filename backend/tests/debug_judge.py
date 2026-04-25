import asyncio
import os
os.environ.pop("SSL_CERT_FILE", None)

import litellm
litellm.set_verbose = False

from dotenv import load_dotenv
load_dotenv()

PROMPT = """You are an expert evaluator. Compare these two responses.

## Prompt
Explain gravity

## Response A
Gravity pulls objects together based on mass.

## Response B  
Gravity is a fundamental force described by Einstein as spacetime curvature.

## Instructions
Output raw JSON only. First character must be { and last must be }

{
  "winner": "A" or "B" or "tie",
  "criteria_scores": {
    "accuracy": {"A": <1-5>, "B": <1-5>}
  },
  "reasoning": "brief reason"
}"""


async def test_model(model):
    import os
    response = await litellm.acompletion(
        model=model,
        messages=[{"role": "user", "content": PROMPT}],
        temperature=0.0,
        max_tokens=256,
        api_key=os.getenv("GROQ_API_KEY"),
    )
    raw = response.choices[0].message.content
    print(f"\n--- {model} ---")
    print(repr(raw[:500]))


async def main():
    await test_model("groq/mixtral-8x7b-32768")
    await test_model("groq/gemma2-9b-it")

asyncio.run(main())