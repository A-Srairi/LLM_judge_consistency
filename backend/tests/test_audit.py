import asyncio
import httpx

async def test():
    payload = {
        "prompt": "What is the difference between supervised and unsupervised learning?",
        "response_a": "Supervised learning uses labeled data to train models that predict outputs. Examples include classification and regression. The model learns from input-output pairs provided during training.",
        "response_b": "In supervised learning you have labels, in unsupervised you do not. Unsupervised learning finds hidden patterns. Both are types of machine learning.",
        "judges": ["groq/llama-3.3-70b-versatile"],
        "criteria": ["accuracy", "helpfulness"],
        "n_samples": 2,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post("http://127.0.0.1:8000/audit", json=payload)
        data = response.json()

        print("Status:", response.status_code)
        print()
        print("verdict summary  :", data.get("verdict_summary"))
        print("reliability score:", data.get("reliability_score"))
        print("flip rate        :", data.get("positional_bias", {}).get("flip_rate"))
        print("krippendorff     :", data.get("inter_judge_agreement", {}).get("krippendorff_alpha"))
        print("shapley          :", data.get("shapley_attribution", {}).get("per_criterion"))
        print("overall winner   :", data.get("overall_winner"))
        print()
        print("verdicts:")
        for v in data.get("verdicts", []):
            print(f"  {v['judge_model']} | order={v['order']} | winner={v['winner']}")

asyncio.run(test())