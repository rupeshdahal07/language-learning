from django.shortcuts import render
from django.http import HttpResponse
from app.supabase_client import supabase
from django.http import JsonResponse

# Create your views here.
BASE_URL = 'http://139.59.72.199:8000'
def feed_page(request):
    token = request.GET.get("token") or request.headers.get("Authorization")
    if not token:
        return HttpResponse("Unauthorized", status=401)

    user_resp = supabase.auth.get_user(token)
    user = user_resp.user
    resp = supabase.table("users").select("*").eq("id", user.id).single().execute()
    user_data = resp.data

    if not user_data:
        return HttpResponse("User not found in users table", status=404)

    avatar_url = user_data.get('avatar_url')
    if avatar_url:
        avatar_url = f"{BASE_URL}{avatar_url}"

    data = {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at,
        "last_sign_in_at": user.last_sign_in_at,
        "role": user.role,
        "is_anonymous": user.is_anonymous,
        "avatar_url": avatar_url,
        "username": user_data.get('username'),
        "display_name": user_data.get('display_name'),
    }
    print(f'user:{user_data}')
    if not user:
        return HttpResponse("Invalid token", status=401)

    return render(request, "community/index.html", {"user": data})



def post(request):
    """
    Returns paginated posts for infinite scroll.
    Each post includes user info from the users table.
    """
    try:
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 10))
        offset = (page - 1) * page_size

        # Fetch posts with user info using join
        resp = supabase.table("posts") \
            .select("*, users(username, avatar_url, display_name)") \
            .order("created_at", desc=True) \
            .range(offset, offset + page_size - 1) \
            .execute()
        print("Supabase response:", resp) 
        posts = resp.data if resp.data else []

        # Format avatar_url with BASE_URL if present
        for post in posts:
            user = post.get("users")
            if user and user.get("avatar_url"):
                user["avatar_url"] = f"{BASE_URL}{user['avatar_url']}"

        has_more = len(posts) == page_size
        print(f"post: {posts}")

        return JsonResponse({
            "success": True,
            "posts": posts,
            "page": page,
            "page_size": page_size,
            "has_more": has_more
        }, status=200)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)