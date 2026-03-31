from supabase import create_client, Client
import os

# Load credentials from environment variables (add them to backend/.env)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")  # use service_role key for server‑side writes if needed

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase credentials not set in environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_user(user_id: str):
    """Fetch a user row. RLS should protect this endpoint on the Supabase side."""
    return supabase.table("users").select("*").eq("id", user_id).single().execute()

def create_notification(user_id: str, title: str, payload: dict):
    """Insert a notification row – this will be pushed to the client via Realtime."""
    return supabase.table("notifications").insert({
        "user_id": user_id,
        "title": title,
        "payload": payload,
    }).execute()
