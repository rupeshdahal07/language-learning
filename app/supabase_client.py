# myapp/supabase_client.py
import os
from config.env import env, BASE_DIR
from supabase import create_client, Client



env.read_env(os.path.join(BASE_DIR, '.env'))

# url: str = "http://64.227.141.251:8000"
url: str = env('SUPABASE_URL')
# key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU0ODQ5NzAwLCJleHAiOjE5MTI2MTYxMDB9.Sb8f7UBYH1JncIawaFImCPgxG5d6Ljk3lPOb904kdC8"
key: str = env('SUPABASE_KEY')
supabase: Client = create_client(url, key)

auth = supabase.auth.sign_in_with_password({
    "email": env('SUPABASE_EMAIL'),
    "password": env('SUPABASE_PASSWORD')
})
access_token = auth.session.access_token
print(f"access_tocken: {access_token}")
supabase.postgrest.auth(access_token)