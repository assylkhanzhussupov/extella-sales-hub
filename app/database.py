from supabase import create_client, Client
from app.config import settings

_client = None


def get_db() -> Client:
    global _client
    if _client is None:
        if not settings.supabase_url or not settings.supabase_key:
            raise ValueError("Supabase credentials not configured")
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client
