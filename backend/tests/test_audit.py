import asyncio
import httpx

async def test():
    payload = {
        "prompt": "Sally has 3 brothers. Each brother has 2 sisters. How many sisters does Sally have?",
        "response_a": "To solve this, we need to carefully account for each sisterly relationship. Sally has 3 brothers: Brother 1, Brother 2, and Brother 3. Each brother has 2 sisters, so 3 × 2 = 6 sister-relationships. Sally has 6 sisters.",
        "response_b": "Sally has 1 sister. All 3 brothers share the same sisters — Sally and one other girl. So there are exactly 2 girls in the family total.",
        "judges": [
            "groq/llama-3.3-70b-versatile",
            "groq/llama-3.1-8b-instant",
            "groq/qwen/qwen3-32b",
        ],
        "criteria": ["accuracy", "helpfulness", "conciseness"],
        "n_samples": 2,
        "temperatures": [0.0, 0.5, 1.0],
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post("http://127.0.0.1:8000/audit", json=payload)
        data = response.json()

        print("Status:", response.status_code)
        print("overall winner   :", data.get("overall_winner"))
        print("reliability score:", data.get("reliability_score"))
        print("temperatures used:", data.get("temperatures_used"))
        print()

        ts = data.get("temperature_sensitivity")
        if ts:
            print("=== TEMPERATURE SENSITIVITY ===")
            print("most stable judge :", ts["most_stable_judge"])
            print("least stable judge:", ts["least_stable_judge"])
            print()
            print("per judge sensitivity scores:")
            for judge, score in ts["per_judge_sensitivity"].items():
                print(f"  {judge.replace('groq/', '')}: {score}")
            print()
            print("optimal temperature per judge:")
            for judge, temp in ts["optimal_temperature"].items():
                print(f"  {judge.replace('groq/', '')}: {temp}")
            print()
            print("verdict heatmap (AB order only):")
            for judge, temps in ts["verdict_heatmap"].items():
                print(f"  {judge.replace('groq/', '')}:")
                for temp, dist in temps.items():
                    print(f"    temp={temp}: A={dist['A']} B={dist['B']} tie={dist['tie']}")
        else:
            print("no temperature sensitivity data (single temperature)")

        print()
        print("total verdicts:", len(data.get("verdicts", [])))

asyncio.run(test())