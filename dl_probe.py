import os
from dotenv import load_dotenv
load_dotenv("cropbima-express/backend/.env")
import httpx
url = "https://appsprodaksharpublicsa.blob.core.windows.net/akshar-uploads/01a11b82-629f-7724-8502-2bdfdc1682b1/01a11b82-62a5-766f-b599-fcfbb2bb2452/01a12f5d-b708-701d-a590-6989c6ba4ebf/output.md"
# NOTE: URL above is from probe; re-fetch fresh via status if expired. Just try:
print("trying saved URL...")
try:
    r = httpx.get(url, timeout=30)
    print(r.status_code, len(r.text))
    print(r.text[:3000])
except Exception as e:
    print("ERR", str(e)[:300])
