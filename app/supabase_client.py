# myapp/supabase_client.py
import os
from supabase import create_client, Client

url: str = "http://64.227.141.251:8000"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU0ODQ5NzAwLCJleHAiOjE5MTI2MTYxMDB9.Sb8f7UBYH1JncIawaFImCPgxG5d6Ljk3lPOb904kdC8"
supabase: Client = create_client(url, key)

auth = supabase.auth.sign_in_with_password({
    "email": "rupyesdahal12@gmail.com",
    "password": "rupesh123"
})
access_token = auth.session.access_token
supabase.postgrest.auth(access_token)