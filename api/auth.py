import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

class SupabaseUser:
    """Simple user class to represent Supabase authenticated user"""
    def __init__(self, payload):
        self.payload = payload
        self.id = payload.get('sub')  # Supabase user ID
        self.email = payload.get('email')
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

class SupabaseJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        try:
            # Use JWT secret directly - you need to add this to your .env
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,  # Add this to your settings
                algorithms=["HS256"],  # Most self-hosted use HS256
                options={"verify_aud": False, "verify_iss": False}  # Disable audience/issuer verification
            )
            
            # Create a user object from the payload
            user = SupabaseUser(payload)
            return (user, token)  # Return (user, auth) tuple
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationFailed(f"Invalid token: {str(e)}")
        except Exception as e:
            raise AuthenticationFailed(f"Authentication error: {str(e)}")