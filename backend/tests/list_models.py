import os
os.environ.pop("SSL_CERT_FILE", None)
from dotenv import load_dotenv
load_dotenv()
import requests

key = os.getenv("GROQ_API_KEY")
r = requests.get(
    "https://api.groq.com/openai/v1/models",
    headers={"Authorization": f"Bearer {key}"}
)
models = [m["id"] for m in r.json()["data"]]
for m in sorted(models):
    print(m)