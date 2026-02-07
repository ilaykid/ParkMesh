import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

try:
    buckets = supabase.storage.list_buckets()
    print(f"Available buckets: {[b.name for b in buckets]}")
    for b in buckets:
        print(f"Bucket {b.name}: Public={b.public}")
except Exception as e:
    print(f"Error listing buckets: {e}")
