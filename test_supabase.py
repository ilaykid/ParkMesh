import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
bucket = os.getenv("SUPABASE_BUCKET", "videos")

supabase = create_client(url, key)

print(f"Checking bucket: {bucket}")
try:
    # Try listing root
    res = supabase.storage.from_(bucket).list()
    print(f"Root list: {res}")
    
    # Try getting public URL for the specific file user mentioned
    test_file = "198.mp4"
    public_url = supabase.storage.from_(bucket).get_public_url(test_file)
    print(f"Public URL for {test_file}: {public_url}")
    
except Exception as e:
    print(f"Error: {e}")
