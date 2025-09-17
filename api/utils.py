from supabase import create_client
from django.conf import settings

def get_user_supabase(jwt_token: str):
    """Return a Supabase client scoped to the user's JWT."""
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    client.postgrest.auth(jwt_token)
    return client

def get_user(jwt_token: str):
    """
    Return a Supabase client scoped to the user's JWT.
    Use this client for user-level operations like update_user.
    """
    client = create_client(settings.SUPABASE_URL, jwt_token)
    return client