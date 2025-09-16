from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from .utils import get_user_supabase
import json
from .supabase_client import supabase
from django.shortcuts import render
from django.http import HttpResponse

class UserPathProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's path progress - all paths or specific path"""
        try:
            jwt_token = request.auth
            supabase = get_user_supabase(jwt_token)
            
            # Get user_id from JWT token (you might need to decode this)
            # For now, assuming you have a way to get user_id
            user_id = request.GET.get('user_id')  # or extract from JWT
            path_id = request.GET.get('path_id')
            
            if not user_id:
                return Response(
                    {"error": "User ID is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Build query
            query = supabase.table("user_path_progress").select("*").eq("user_id", user_id)
            
            if path_id:
                query = query.eq("path_id", path_id)
                response = query.single().execute()
                print(f'user_path_progress: {response.data}')
                return Response(response.data)
            else:
                response = query.execute()
                return Response(response.data)
                
        except Exception as e:
            return Response(
                {"error": f"Error fetching progress: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



    def post(self, request):
        """Create new path progress for user or update existing"""
        try:
            jwt_token = request.auth
            supabase = get_user_supabase(jwt_token)
            
            user_id = request.data.get("user_id")
            path_id = request.data.get("path_id")
            
            if not user_id or not path_id:
                return Response(
                    {"error": "user_id and path_id are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get total lessons in this path from the path table
            path_response = supabase.table("paths").select("lessons").eq("id", path_id).single().execute()
            lessons_list = path_response.data.get("lessons", []) if path_response.data else []
            total_lessons = len(lessons_list)

            # Get current progress
            user_path_progress = supabase.table("user_path_progress").select("*").eq("user_id", user_id).eq("path_id", path_id).execute()
            
            # Initialize completed_lessons
            completed_lessons = []
            if user_path_progress.data:
                lesson_data = user_path_progress.data[0]
                completed_lessons = lesson_data.get('completed_lessons', [])
                if not isinstance(completed_lessons, list):
                    completed_lessons = [completed_lessons] if completed_lessons is not None else []

            # Get new lessons to append from request data
            new_completed_lessons = request.data.get("completed_lessons", completed_lessons)
            if not isinstance(new_completed_lessons, list):
                new_completed_lessons = [new_completed_lessons] if new_completed_lessons is not None else []

            # Merge and deduplicate
            for lesson in new_completed_lessons:
                if lesson not in completed_lessons:
                    completed_lessons.append(lesson)

            # Calculate progress percentage
            progress_percentage = (len(completed_lessons) / total_lessons) * 100 if total_lessons > 0 else 0

            # Determine status
            status_value = 1 if progress_percentage >= 100 else 0

            if user_path_progress.data:
                # Update existing progress
                update_data = {
                    "status": status_value,
                    "path_progress": progress_percentage,
                    "completed_lessons": completed_lessons
                }
                response = supabase.table("user_path_progress").update(update_data).eq("user_id", user_id).eq("path_id", path_id).execute()
                return Response(response.data, status=status.HTTP_200_OK)
            else:
                # Create new progress
                progress_data = {
                    "user_id": user_id,
                    "path_id": path_id,
                    "status": status_value,
                    "path_progress": progress_percentage,
                    "completed_lessons": completed_lessons
                }
                response = supabase.table("user_path_progress").insert(progress_data).execute()
                return Response(response.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": f"Error creating/updating progress: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserLessonProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's path progress - all paths or specific path"""
        try:
            jwt_token = request.auth
            supabase = get_user_supabase(jwt_token)
            
            # Get user_id from JWT token (you might need to decode this)
            # For now, assuming you have a way to get user_id
            user_id = request.GET.get('user_id')  # or extract from JWT
            path_id = request.GET.get('path_id')
            lesson_id = request.GET.get('lesson_id')
            
            if not user_id or not lesson_id:
                return Response(
                    {"error": "User ID or lesson_id is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Build query
            query = supabase.table("user_lesson_progress").select("*").eq("user_id", user_id).eq("lesson_id", lesson_id)
            
            if path_id:
                query = query.eq("path_id", path_id)
                
            else:
                query = query.is_("path_id", None)

            response = query.execute()
            return Response(response.data)
                
        except Exception as e:
            return Response(
                {"error": f"Error fetching progress: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """Create or update lesson progress for user, progress is based on incorrect_levels"""
        try:
            jwt_token = request.auth
            supabase = get_user_supabase(jwt_token)

            user_id = request.data.get("user_id")
            path_id = request.data.get("path_id")
            lesson_id = request.data.get("lesson_id")

            if not user_id or not lesson_id:
                return Response(
                    {"error": "user_id and lesson_id are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get lesson info
            lesson = supabase.table("lessons").select("*").eq("id", lesson_id).single().execute()
            total_levels = []
            if lesson.data:
                total_levels = lesson.data.get('data', [])

            # Get current progress
            query = supabase.table("user_lesson_progress").select("*").eq("user_id", user_id).eq("lesson_id", lesson_id)
            if path_id:
                query = query.eq("path_id", path_id)
            else:
                query = query.is_("path_id", None)
            existing = query.execute()

            # Prepare completed level progress
            new_completed_levels = request.data.get("completed_levels", [])
            if not isinstance(new_completed_levels, list):
                new_completed_levels = [new_completed_levels] if new_completed_levels is not None else []

            completed_levels = new_completed_levels
            if existing.data:
                existing_data = existing.data[0]
                existing_completed_levels = existing_data.get("completed_levels", [])
                if not isinstance(existing_completed_levels, list):
                    existing_completed_levels = [existing_completed_levels] if existing_completed_levels is not None else []
                # Merge and deduplicate
                completed_levels = list({json.dumps(l, sort_keys=True): l for l in (existing_completed_levels + new_completed_levels)}.values())
                            
            total_count = len(total_levels) if isinstance(total_levels, list) else 0
            progress_percentage = (len(completed_levels) / total_count) * 100 if total_count > 0 else 0
            
            status_value = 1 #if progress_percentage >= 10 else 0

            # Prepare update/insert data
            progress_data = {
                "user_id": user_id,
                "lesson_id": lesson_id,
                "completed_levels": completed_levels,
                "incorrect_levels": request.data.get("incorrect_levels", []),
                "status": status_value,
                "lesson_progress": progress_percentage,
            }
            if path_id:
                progress_data["path_id"] = path_id

            # Update or insert
            if existing.data:
                update_query = supabase.table("user_lesson_progress").update(progress_data).eq("user_id", user_id).eq("lesson_id", lesson_id)
                if path_id:
                    update_query = update_query.eq("path_id", path_id)
                else:
                    update_query = update_query.is_("path_id", None)
                response = update_query.execute()
                return Response(response.data, status=status.HTTP_200_OK)
            else:
                response = supabase.table("user_lesson_progress").insert(progress_data).execute()
                return Response(response.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": f"Error creating/updating progress: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class UserLevelProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's progress for a specific level (level is jsonb)"""
        try:
            jwt_token = request.auth
            supabase = get_user_supabase(jwt_token)

            user_id = request.GET.get('user_id')
            path_id = request.GET.get('path_id')
            lesson_id = request.GET.get('lesson_id')
            level = request.GET.get('level')  # Should be a JSON string

            if not all([user_id, level]):
                return Response(
                    {"error": "user_id, lesson_id, and level are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Parse level JSON string to dict
            try:
                level_dict = json.loads(level)
            except Exception:
                return Response(
                    {"error": "level must be a valid JSON object"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            query = supabase.table("user_level_progress").select("*") \
                .eq("user_id", user_id) \
                .eq("level", json.dumps(level_dict, sort_keys=True))

            if lesson_id:
                query = query.eq("lesson_id", lesson_id)
            else:
                query = query.is_("lesson_id", None)
            if path_id:
                query = query.eq("path_id", path_id)
            else:
                query = query.is_("path_id", None)

            response = query.execute()
            if not response.data:
                return Response(None, status=status.HTTP_200_OK)
            return Response(response.data[0])
        
        except Exception as e:
            return Response(
                {"error": f"Error fetching level progress: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """Create or update user's progress for a specific level (level is jsonb)"""
        try:
            jwt_token = request.auth
            supabase = get_user_supabase(jwt_token)

            user_id = request.data.get("user_id")
            path_id = request.data.get("path_id")
            lesson_id = request.data.get("lesson_id")
            level = request.data.get("level")  # Should be a dict
            
            status_value = request.data.get("status", 0)
            time_spent = request.data.get("time_spent")
            extra_data = request.data.get("extra_data", {})

            if not all([user_id, level]):
                return Response(
                    {"error": "user_id, lesson_id, and level are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Use JSON string for filtering
            level_json_str = json.dumps(level, sort_keys=True)

            # Check if progress exists
            query = supabase.table("user_level_progress").select("*") \
                .eq("user_id", user_id) \
                .eq("level", level_json_str)
            if lesson_id:
                query = query.eq("lesson_id", lesson_id)
            else:
                query = query.is_("lesson_id", None)

            if path_id:
                query = query.eq("path_id", path_id)
            else:
                query = query.is_("path_id", None)
            existing = query.execute()

            progress_data = {
                "user_id": user_id,
                "lesson_id": lesson_id,
                "level": level,  # dict for insert/update
                "status": request.data.get("status", 0),
                "extra_data": extra_data,
            }
            if path_id:
                progress_data["path_id"] = path_id
            if time_spent:
                progress_data["time_spent"] = time_spent

            if existing.data:
                update_query = supabase.table("user_level_progress").update(progress_data) \
                    .eq("user_id", user_id).eq("level", level_json_str)
                if lesson_id:
                    update_query = update_query.eq("lesson_id", lesson_id)
                else:
                    update_query = update_query.is_("lesson_id", None)

                if path_id:
                    update_query = update_query.eq("path_id", path_id)

                response = update_query.execute()
                return Response(response.data, status=status.HTTP_200_OK)
            else:
                response = supabase.table("user_level_progress").insert(progress_data).execute()
                return Response(response.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": f"Error creating/updating level progress: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


import random

class UserRegistration(APIView):
    def post(self, request):
        try:
            data = request.data
            name = data.get('name', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            phone = data.get('phone', '').strip()
            avatar_file = request.FILES.get('avatar_url')

            if not all([name, email, password]):
                return Response(
                    {"error": "Name, email, and password are required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate username
            name_parts = name.split()
            first_part = name_parts[0] if name_parts else name
            username = f"{first_part}{random.randrange(100, 100000)}"

            # Signup user (sends confirmation email automatically)
            resp = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {"phone": phone} if phone else {}
                }
            })

            # Check if signup failed
            if not resp.user:
                error_message = getattr(resp, "message", "Signup failed.")
                return Response(
                    {"error": error_message},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user_id = resp.user.id

            # Handle avatar upload
            image_url = None
            if avatar_file:
                file_name = f"users/{avatar_file.name}"
                try:
                    supabase.storage.from_("users").upload(file_name, avatar_file.read())
                    image_url = f"/storage/v1/object/public/users/{file_name}"
                except Exception as e:
                    return Response(
                        {"error": f"Avatar upload failed: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            # Insert profile into users table
            user_data = {
                "id": user_id,
                "display_name": name,
                "username": username,
                "avatar_url": image_url
            }
            response = supabase.table("users").insert(user_data).execute()

            return Response(response.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": f"Error creating user: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class ResetUserPassword(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Send a password reset link to the user's email.
        Expects: { "email": "user@example.com" }
        """
        try:
            email = request.data.get("email", "").strip()
            if not email:
                return Response(
                    {"error": "Email is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate email format (optional but recommended)
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            
            try:
                validate_email(email)
            except ValidationError:
                return Response(
                    {"error": "Please enter a valid email address."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Send password reset email using Supabase
            # Correct method name is reset_password_for_email()
            resp = supabase.auth.reset_password_for_email(
                email,
                options={"redirect_to": "http://13.229.98.72:8000/api/reset-password/"}
            )
            
            # The method typically returns None on success or raises an exception
            return Response(
                {"message": "Password reset link sent to email if account exists."},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            # Log the actual error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Password reset error for email {email}: {str(e)}")
            
            # Return generic message for security (don't reveal if email exists)
            return Response(
                {"message": "Password reset link sent to email if account exists."},
                status=status.HTTP_200_OK
            )
        
def reset_password(request):
    # Get tokens from URL parameters (sent by Supabase after email verification)
    access_token = request.GET.get("access_token", "")
    refresh_token = request.GET.get("refresh_token", "")
    token_type = request.GET.get("token_type", "")
    recovery_type = request.GET.get("type", "")
    
    # Verify this is a valid recovery session
    if recovery_type != "recovery" or not access_token:
        return render(request, "account/reset_password.html", {
            "error": "Invalid or expired reset link. Please request a new one."
        })

    if request.method == "POST":
        new_password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if not new_password or new_password != confirm_password:
            return render(request, "account/reset_password.html", {
                "error": "Passwords do not match.",
                "access_token": access_token,
                "refresh_token": refresh_token
            })

        if len(new_password) < 8:  # Add password validation
            return render(request, "account/reset_password.html", {
                "error": "Password must be at least 8 characters long.",
                "access_token": access_token,
                "refresh_token": refresh_token
            })

        try:
            # Set the session with the recovery tokens
            session_response = supabase.auth.set_session(access_token, refresh_token)
            
            # Now update the password
            resp = supabase.auth.update_user({"password": new_password})
            
            if resp:
                return HttpResponse("✅ Password has been reset successfully. You can now log in with your new password.")
            else:
                return render(request, "account/reset_password.html", {
                    "error": "Failed to reset password. Please try again.",
                    "access_token": access_token,
                    "refresh_token": refresh_token
                })
                
        except Exception as e:
            return render(request, "account/reset_password.html", {
                "error": f"Error resetting password: {str(e)}",
                "access_token": access_token,
                "refresh_token": refresh_token
            })

    return render(request, "account/reset_password.html", {
        "access_token": access_token,
        "refresh_token": refresh_token
    })


class CheckUserVerified(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        try:
            # Query the public users table for is_verified field
            resp = supabase.table("users").select("id, is_verified").eq("id", user_id).single().execute()
            
            if not resp.data:
                return Response({"error": "User not found"}, status=404)

            user_data = resp.data
            verified = user_data.get("is_verified", False)

            return Response({
                "id": user_data["id"],
                "verified": verified
            }, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class LearnDataView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get comprehensive learning progress data for a user"""
        try:
            jwt_token = request.auth
            supabase = get_user_supabase(jwt_token)
            
            user_id = request.GET.get('user_id')
            
            if not user_id:
                return Response(
                    {"error": "user_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get user basic info - use execute() instead of single() to handle missing users
            user_response = supabase.table("users") \
                .select("display_name") \
                .eq("id", str(user_id)) \
                .limit(1) \
                .execute()

            if user_response.data:
                user_name = user_response.data[0].get("display_name", "User")
            else:
                user_name = "User"
            print("User name:", user_name)

            
            # Get user path progress
            path_progress_response = supabase.table("user_path_progress").select("*").eq("user_id", user_id).execute()
            path_progress = path_progress_response.data or []
            
            # Calculate streak (may need to implement this based on your streak logic)
            streak = 2  
            
            # Calculate alphabet progress
            alphabet_total = supabase.table("letters").select("id", count="exact").limit(0).execute()
            alphabet_completed = supabase.table("user_level_progress").select("id", count="exact").is_("path_id", None).is_("lesson_id", None).limit(0).eq("user_id", user_id).execute()
            
            alphabet_progress = 0.0
            if alphabet_total.count and alphabet_total.count > 0:
                completed_count = alphabet_completed.count or 0
                alphabet_progress = min(completed_count / alphabet_total.count, 1.0)
            
                       # Calculate vocab progress
            vocab_total = supabase.table("lessons").select("id", count="exact").eq("lesson_type", 4).limit(0).execute()
            vocab_completed_response = supabase.table("user_lesson_progress") \
                .select("*, lessons!inner(lesson_type)") \
                .eq("user_id", user_id) \
                .eq("lessons.lesson_type", 4) \
                .execute()
            
            vocab_progress = 0.0
            vocab_total_count = vocab_total.count or 0  # Handle None case
            
            if vocab_total_count > 0:
                vocab_lesson_count = 0
                for lesson_progress in vocab_completed_response.data or []:
                    lesson_progress_value = lesson_progress.get("lesson_progress", 0) or 0
                    if lesson_progress_value > 0:
                        vocab_lesson_count += 1
                vocab_progress = min(vocab_lesson_count / vocab_total_count, 1.0)

            # # Calculate tracing progress (based on letters with specific criteria)
            tracing_progress = alphabet_progress  # Using same logic for now
            
            response_data = {
                "name": user_name,
                "streak": streak,
                "path_progress": path_progress,
                "alphabet_progress": round(alphabet_progress, 2),
                "vocab_progress": round(vocab_progress, 2),
                "tracing_progress": round(tracing_progress, 2)
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error fetching learning data: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # def put(self, request):
    #     """Update user's path progress"""
    #     try:
    #         jwt_token = request.auth
    #         supabase = get_user_supabase(jwt_token)
            
    #         user_id = request.data.get("user_id")
    #         path_id = request.data.get("path_id")
            
    #         if not user_id or not path_id:
    #             return Response(
    #                 {"error": "user_id and path_id are required"}, 
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )
            
    #         # Prepare update data (only include fields that are provided)
    #         update_data = {}
            
    #         if "status" in request.data:
    #             update_data["status"] = request.data["status"]
            
    #         if "path_progress" in request.data:
    #             update_data["path_progress"] = request.data["path_progress"]
            
    #         if "completed_lessons" in request.data:
    #             update_data["completed_lessons"] = request.data["completed_lessons"]
            
    #         if not update_data:
    #             return Response(
    #                 {"error": "No valid fields to update"}, 
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )
            
    #         response = supabase.table("user_path_progress").update(update_data).eq("user_id", user_id).eq("path_id", path_id).execute()
            
    #         if not response.data:
    #             return Response(
    #                 {"error": "Progress not found"}, 
    #                 status=status.HTTP_404_NOT_FOUND
    #             )
            
    #         return Response(response.data)
            
    #     except Exception as e:
    #         return Response(
    #             {"error": f"Error updating progress: {str(e)}"}, 
    #             status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #         )

    # def delete(self, request):
    #     """Delete user's path progress"""
    #     try:
    #         jwt_token = request.auth
    #         supabase = get_user_supabase(jwt_token)
            
    #         user_id = request.data.get("user_id")
    #         path_id = request.data.get("path_id")
            
    #         if not user_id or not path_id:
    #             return Response(
    #                 {"error": "user_id and path_id are required"}, 
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )
            
    #         response = supabase.table("user_path_progress").delete().eq("user_id", user_id).eq("path_id", path_id).execute()
            
    #         return Response(
    #             {"message": "Progress deleted successfully"}, 
    #             status=status.HTTP_200_OK
    #         )
            
    #     except Exception as e:
    #         return Response(
    #             {"error": f"Error deleting progress: {str(e)}"}, 
    #             status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #         )


# class UserPathProgressBulkView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         """Add completed lesson to user's progress"""
#         try:
#             jwt_token = request.auth
#             supabase = get_user_supabase(jwt_token)
            
#             user_id = request.data.get("user_id")
#             path_id = request.data.get("path_id")
#             lesson_id = request.data.get("lesson_id")
            
#             if not all([user_id, path_id, lesson_id]):
#                 return Response(
#                     {"error": "user_id, path_id, and lesson_id are required"}, 
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             # Get current progress
#             current_progress = supabase.table("user_path_progress").select("*").eq("user_id", user_id).eq("path_id", path_id).single().execute()
            
#             if not current_progress.data:
#                 return Response(
#                     {"error": "Progress not found. Create progress first."}, 
#                     status=status.HTTP_404_NOT_FOUND
#                 )
            
#             completed_lessons = current_progress.data.get("completed_lessons", [])
            
#             # Add lesson if not already completed
#             if lesson_id not in completed_lessons:
#                 completed_lessons.append(lesson_id)
                
#                 # Get total lessons in path to calculate progress
#                 path_response = supabase.table("paths").select("lessons").eq("id", path_id).single().execute()
#                 total_lessons = len(path_response.data.get("lessons", []))
                
#                 # Calculate progress percentage
#                 path_progress = (len(completed_lessons) / total_lessons) * 100 if total_lessons > 0 else 0
                
#                 # Determine status
#                 if path_progress >= 100:
#                     status_value = "completed"
#                 elif path_progress > 0:
#                     status_value = "in_progress"
#                 else:
#                     status_value = "started"
                
#                 # Update progress
#                 update_data = {
#                     "completed_lessons": completed_lessons,
#                     "path_progress": path_progress,
#                     "status": status_value
#                 }
                
#                 response = supabase.table("user_path_progress").update(update_data).eq("user_id", user_id).eq("path_id", path_id).execute()
#                 return Response(response.data)
            
#             return Response(current_progress.data)
            
#         except Exception as e:
#             return Response(
#                 {"error": f"Error updating lesson progress: {str(e)}"}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )