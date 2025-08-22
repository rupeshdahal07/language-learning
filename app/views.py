import re
from django.shortcuts import render
from django.http import JsonResponse
from .supabase_client import supabase
from django.shortcuts import render, redirect
from typing import List
from django.http import JsonResponse
import json
from django.contrib.auth.decorators import login_required
from .helper import wrap_preeti_in_sentence, wrap_preeti_before_parenthesis, quiz_question_wrapper

@login_required
def dashboard(request):
    """
    Dashboard view to display overview of all system components
    """
    try:
        # Fetch counts from all tables
        fill_blanks_response = supabase.table("fill_blanks_level").select("id", count="exact").limit(0).execute()
        quiz_response = supabase.table("quiz_levels").select("id", count="exact").limit(0).execute()
        word_form_response = supabase.table("word_form_levels").select("id", count="exact").limit(0).execute()
        # users_response = supabase.table("users").select("id", count="exact").limit(0).execute()
        match_following_response = supabase.table("match_the_following_level").select("id", count="exact").limit(0).execute()
        
        # Get recent items (last 5 from each table)
        recent_fill_blanks = supabase.table("fill_blanks_level").select("*").order("created_at", desc=True).limit(5).execute()
        recent_quiz = supabase.table("quiz_levels").select("*").order("created_at", desc=True).limit(5).execute()
        recent_word_forms = supabase.table("word_form_levels").select("*").order("created_at", desc=True).limit(5).execute()
        # recent_users = supabase.table("users").select("*").order("created_at", desc=True).limit(5).execute()
        recent_match_following = supabase.table("match_the_following_level").select("*").order("created_at", desc=True).limit(5).execute()
        
        context = {
            'stats': {
                'fill_blanks_count': fill_blanks_response.count if fill_blanks_response.count else 0,
                'quiz_count': quiz_response.count if quiz_response.count else 0,
                'word_form_count': word_form_response.count if word_form_response.count else 0,
                # 'users_count': users_response.count if users_response.count else 0,
                'match_following_count': match_following_response.count if match_following_response.count else 0,
            },
            'recent_items': {
                'fill_blanks': recent_fill_blanks.data[:3] if recent_fill_blanks.data else [],
                'quiz': recent_quiz.data[:3] if recent_quiz.data else [],
                'word_forms': recent_word_forms.data[:3] if recent_word_forms.data else [],
                # 'users': recent_users.data[:3] if recent_users.data else [],
                'match_following': recent_match_following.data[:3] if recent_match_following.data else [],
            }
        }
        
    except Exception as e:
        context = {
            'error': f'Error loading dashboard data: {str(e)}',
            'stats': {
                'fill_blanks_count': 0,
                'quiz_count': 0,
                'word_form_count': 0,
                'users_count': 0,
                'match_following_count': 0,
            },
            'recent_items': {
                'fill_blanks': [],
                'quiz': [],
                'word_forms': [],
                'users': [],
                'match_following': [],
            }
        }
    
    return render(request, 'dashboard.html', context)



def users(request):
    return render(request, 'users_list.html')
def list_users(request):
    """
    API view to return users with pagination (infinite scroll friendly).
    """
    try:
        # Get pagination params
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 20))
        offset = (page - 1) * limit

        # Fetch paginated users
        response = supabase.table("users").select("*").order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        users = response.data

        # Get total count (to know when to stop scrolling)
        total_count = supabase.table("users").select("id", count="exact").execute().count

        return JsonResponse({
            "users": users,
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "has_more": offset + len(users) < total_count
        })

    except Exception as e:
        return JsonResponse({
            "users": [],
            "error": f"Error fetching data: {str(e)}",
            "total_count": 0,
            "has_more": False
        }, status=500)



def create_user(request):
    if request.method == 'POST':
        email: str = request.POST.get('email')
        display_name: str = request.POST.get('display_name')
        avatar_url: str = request.POST.get('avatar_url')

        user_data = [{
            
            "email": email,
            "display_name": display_name,
            "avatar_url": avatar_url,
            
        }]
        print(user_data)
        supabase.table("users").insert(user_data).execute()
        return render(request, 'user_form.html', {'success': 'Word inserted successfully.'})

    return render(request, 'user_form.html')

#-------------------path------------------------------------------------>>>
def create_path(request):
    # Fetch all lessons for selection
    lessons_response = supabase.table("lessons").select("id, data").order("created_at", desc=True).execute()
    lessons = lessons_response.data

    if request.method == 'POST':
        path_title = request.POST.get('path_title')
        selected_lesson_ids = request.POST.getlist('lessons')  # List of lesson IDs as strings

        # Insert into Supabase
        path_data = {
            "title": path_title,
            "lessons": selected_lesson_ids  # Store as array of strings
        }
        try:
            supabase.table("paths").insert(path_data).execute()
            return render(request, 'paths.html', {'success': 'Path created successfully!', 'lessons': lessons})
        except Exception as e:
            return render(request, 'paths.html', {'error': f'Error creating path: {str(e)}', 'lessons': lessons})

    return render(request, 'paths.html', {'lessons': lessons})

def list_paths(request):
    """
    View to display all paths from the database.
    """
    try:
        # Fetch all paths from Supabase
        response = supabase.table("paths").select("*").order("created_at", desc=True).execute()
        paths = response.data
        count = supabase.table("paths").select("id", count="exact").limit(0).execute()
        context = {
            'paths': paths,
            'total_count': count.count
        }
    except Exception as e:
        context = {
            'paths': [],
            'error': f'Error fetching data: {str(e)}',
            'total_count': 0
        }
    return render(request, 'path_list.html', context)

#--------------------Lession-------------------------------------------->>>
def create_lesson(request):
    if request.method == 'POST':
        lesson_title = request.POST.get('lessonTitle')
        lesson_description = request.POST.get('lessonDescription', '')

        # Collect all level configurations
        levels = []
        index = 0
        while True:
            level_type = request.POST.get(f'level_type_{index}')
            level_id = request.POST.get(f'level_id_{index}')
            sub_level_id = request.POST.get(f'sub_level_id_{index}')
            if level_type is None or level_id is None :
                break
            levels.append({
            'level_type': int(level_type),
            'level_id': int(level_id),
            'sub_level_id': int(sub_level_id)
            })
            index += 1

        # Prepare lesson data as JSON
        lesson_data = {
        'lesson_title': lesson_title,
        'lesson_description': lesson_description,
        'levels': levels
            }
    # Insert as JSONB (not as a string)
        supabase.table("lessons").insert({"data": lesson_data}).execute()
        
        print('Lesson JSON:', lesson_data)

        return redirect('create_lesson')  # Redirect after POST

    return render(request, 'lesson_form.html')

def get_level_ids(request):
    lesson_type = request.GET.get('type')
    level_ids = []
    
    if lesson_type == '5':
        table = "fill_blanks_level"
    elif lesson_type == '3':
        table = "match_the_following_level"
    elif lesson_type == '1':
        table = "quiz_levels"
    elif lesson_type == '4':
        table = "word_form_levels"
    else:
        return JsonResponse({'level_ids': []})

    if lesson_type in ['1','5']:
        response = supabase.table(table).select("id, data").execute()
        print(response)
        level_ids = []
        for row in response.data:
            label = row['data'].get('questionText', str(row['id']))
            level_ids.append({'value': row['id'], 'label': label})
        return JsonResponse({'level_ids': level_ids})

    if lesson_type == '3':
        response = supabase.table(table).select("id, data").execute()
        print(f'match the following:{response}')
        level_ids = []
        for row in response.data:
            # Get first pair for display label
            pairs = row['data'] if row['data'] else []
            if pairs and len(pairs) > 0:
                first_pair = pairs[0]
                label = f"{first_pair.get('nepali', '')} - {first_pair.get('japanese', '')}"
            else:
                label = f"Match Exercise {row['id']}"
            level_ids.append({'value': row['id'], 'label': label})
            
        return JsonResponse({'level_ids': level_ids})
        

    if lesson_type == '4':
        response = supabase.table(table).select("id, question").execute()
        print(response)
        level_ids = []
        for row in response.data:
            label = row.get('question', str(row['id']))
            level_ids.append({'value': row['id'], 'label': label})
        return JsonResponse({'level_ids': level_ids})

    return JsonResponse({'error': 'no level type found!'})
    
def list_lessons(request):
    """
    View to display all lessons from the database.
    """
    try:
        # Fetch all lessons from Supabase
        response = supabase.table("lessons").select("*").order("created_at", desc=True).execute()
        lessons = response.data
        count = supabase.table("lessons").select("id", count="exact").limit(0).execute()
        context = {
            'lessons': lessons,
            'total_count': count.count
        }
    except Exception as e:
        context = {
            'lessons': [],
            'error': f'Error fetching data: {str(e)}',
            'total_count': 0
        }
    return render(request, 'lesson_list.html', context)

#-------------------------lessonEnd--------------------------------->>>>>>>>>>>



def create_quiz(request):
    if request.method == 'POST':
        question_text = quiz_question_wrapper(request.POST.get('questionText'))
        correct_option = int(request.POST.get('correctOption'))

        # Collect all options dynamically
        options = []
        option_index = 0
        while True:
            opt = request.POST.get(f'option_{option_index}')
            if opt is None:
                break
            options.append(wrap_preeti_in_sentence(opt))
            option_index += 1

        # Create your quiz_data structure
        quiz_data = [{
            "data": {
                "questionText": question_text,
                "options": options,
                "correctOption": correct_option
            }
        }]
        print(quiz_data)
        supabase.table("quiz_levels").insert(quiz_data).execute()
        return render(request, 'quiz.html')

    return render(request, 'quiz.html')


# def create_quize_mix(request):
#     if request.method == 'POST':
#         question_text = request.POST.get('questionText')
#         correct_option = int(request.POST.get('correctOption'))
        
#         options = [
            
#             request.POST.get('option_0'),
#             request.POST.get('option_1'),
#             request.POST.get('option_2'),
#             request.POST.get('option_3')
#         ]
        
#         # Create your quiz_data structure
#         quiz_data = [{
#             "data": {
#                 "questionText": question_text,
#                 "options": options,
#                 "correctOption": correct_option
#             }
#         }]
#         print(quiz_data)
#         # Process the data...
#         supabase.table("quiz_levels").insert(quiz_data).execute()
#         return render(request, 'quiz.html')
        
#     return render(request, 'quiz.html')

def list_quiz_questions(request):
    """
    View to display all quiz questions from the database
    """
    try:
        # Fetch all quiz questions from Supabase
        response = supabase.table("quiz_levels").select("*").execute()
        count = supabase.table("quiz_levels").select("*", count="exact").execute()
        quiz_questions = response.data
        
        context = {
            'quiz_questions': quiz_questions,
            'total_count': count.count
        }
        
    except Exception as e:
        context = {
            'quiz_questions': [],
            'error': f'Error fetching data: {str(e)}',
            'total_count': 0
        }
    
    return render(request, 'quiz_list.html', context)




def create_fill_blank(request):
    if request.method == 'POST':
        question_text = request.POST.get('questionText')
        correct_option = request.POST.get('correctOption')
        audio_file = request.FILES.get('audio')
        options = []
        option_index = 0
        while True:
            opt = request.POST.get(f'option_{option_index}')
            if opt is None:
                break
            options.append(opt)
            option_index += 1
        letter_title = request.POST.get('letterTitle')
        topics = [
            request.POST.get('topic_0'),
            request.POST.get('topic_1'),
        ]
        meaning = request.POST.get('letterMeaning')

        # Improved validation: check for None or empty string in all fields
        if (
            not question_text or
            correct_option in [None, ''] or
            not all(options) or
            any(opt in [None, ''] for opt in options) or
            not letter_title or
            not all(topics) or
            any(t in [None, ''] for t in topics) or
            not meaning
        ):
            return render(request, 'fill_blank.html', {'error': 'All fields are required.'})
        
        if not audio_file or not options:
            return render(request, 'word_form.html', {'error': 'All fields are required.'})

        # 1. Upload audio file to Supabase Storage
        file_name = f"audio/{audio_file.name}"  # folder 'audio/' inside bucket
        try:
            res = supabase.storage.from_("audio").upload(file_name, audio_file.read())
        except Exception as e:
            return render(request, 'word_form.html', {'error': f'Upload failed: {str(e)}'})

        # 2. Build public URL (no signed URL needed)
        audio_url = f"http://64.227.141.251:8000/storage/v1/object/public/audio/{file_name}"


        fill_blank = [
            {
                "data": {
                    "questionText": question_text,
                    "options": options,
                    "correctOption": int(correct_option),
                    "audioUrl": audio_url,
                },
                "letter_info": {
                    "title": letter_title,
                    "topics": topics,
                    "meaning": meaning,
                    
                }
            }
        ]
        print(fill_blank)
        supabase.table("fill_blanks_level").insert(fill_blank).execute()
    return render(request, 'fill_blank.html')

def list_fill_blanks(request):
    """
    View to display all fill blank quiz questions from the database
    """
    try:
        # Fetch all fill blank questions from Supabase
        response = supabase.table("fill_blanks_level").select("*").execute()
        count = supabase.table("fill_blanks_level").select("id", count="exact").limit(0).execute().count
        fill_blanks = response.data
        
        context = {
            'fill_blanks': fill_blanks,
            'total_count': count
        }
        
    except Exception as e:
        context = {
            'fill_blanks': [],
            'error': f'Error fetching data: {str(e)}',
            'total_count': 0
        }
    
    return render(request, 'fill_blank_list.html', context)





def create_word_from_level(request):
    if request.method == 'POST':
        audio_file = request.FILES.get('audioFile')
        nepali_sound = request.POST.get('sound')
        if nepali_sound:
            nepali_sound = f'<font="Preeti font SDF">{nepali_sound}</font>'

        letter_1 = request.POST.get('letter_1')
        letter_2 = request.POST.get('letter_2')
        answer = []
        if letter_1 and letter_2:
            answer = [letter_1, letter_2]
        elif letter_1:
            answer = [letter_1]

        # Collect all options dynamically
        options = []
        option_index = 0
        while True:
            opt = request.POST.get(f'option_{option_index}')
            if opt is None:
                break
            options.append(opt)
            option_index += 1

        # Validation
        if not audio_file or not answer or not options:
            return render(request, 'word_form.html', {'error': 'All fields are required.'})

        # # 1. Upload audio file to Supabase Storage
        # file_name = f"audio/{audio_file.name}"  # folder 'audio/' inside bucket
        # try:
        #     res = supabase.storage.from_("audio").upload(file_name, audio_file.read())
            
        # except Exception as e:
        #     return render(request, 'word_form.html', {'error': f'Upload failed: {str(e)}'})
        
        # # 2. Generate signed URL
        # signed_url_res = supabase.storage.from_("audio").create_signed_url(file_name, 86400)
        # audio_url = signed_url_res['signedURL']   # this one is a dict


        # 1. Upload audio file to Supabase Storage
        file_name = f"audio/{audio_file.name}"  # folder 'audio/' inside bucket
        try:
            res = supabase.storage.from_("audio").upload(file_name, audio_file.read())
        except Exception as e:
            return render(request, 'word_form.html', {'error': f'Upload failed: {str(e)}'})

        # 2. Build public URL (no signed URL needed)
        audio_url = f"http://64.227.141.251:8000/storage/v1/object/public/audio/{file_name}"



        # 3. Insert into DB
        word_data = [{
            "audioUrl": audio_url,
            "answer": answer,
            "options": options,
            "sound": nepali_sound
        }]
        supabase.table("word_form_levels").insert(word_data).execute()

        return render(request, 'word_form.html', {'success': 'Word inserted successfully.'})

    return render(request, 'word_form.html')


def list_word_form_levels(request):
    """
    View to display all word form level questions from the database
    """
    try:
        # Fetch all word form levels from Supabase
        response = supabase.table("word_form_levels").select("*").order("created_at", desc=True).execute()
        word_form_levels = response.data
        
        context = {
            'word_form_levels': word_form_levels,
            'total_count': len(word_form_levels)
        }
        
    except Exception as e:
        context = {
            'word_form_levels': [],
            'error': f'Error fetching data: {str(e)}',
            'total_count': 0
        }
    
    return render(request, 'word_form_list.html', context)



def create_match_following(request):
    if request.method == 'POST':
        # Collect all the pairs
        match_pairs = []
        pair_index = 0
        
        while True:
            nepali_key = f'nepali_{pair_index}'
            japanese_key = f'japanese_{pair_index}'
            
            nepali_value = request.POST.get(nepali_key)
            japanese_value = request.POST.get(japanese_key)
            
            # Break if no more pairs found
            if not nepali_value and not japanese_value:
                break
                
            # Only add pairs that have both values
            if nepali_value and japanese_value:
            # Only wrap in Preeti font if nepali_value is likely Preeti (not plain ASCII/romaji)
                if re.fullmatch(r'[A-Za-z0-9\s\.\-\,\']+', nepali_value.strip()) and len(nepali_value.strip()) > 1:
                    nepali_display = nepali_value.strip()
                else:
                    nepali_display = f'<font face="Preeti font  SDF">{nepali_value.strip()}</font>'
                pair_dict = {
                    "nepali": nepali_display,
                    "japanese": japanese_value.strip()
                }
                match_pairs.append(pair_dict)
            
            pair_index += 1
        
        # Create the match_data structure
        match_data = [{
            "data": match_pairs
        }]
        
        print("Match Following Data:", match_data)
        
        # Insert into database
        try:
            supabase.table("match_the_following_level").insert(match_data).execute()
            return render(request, 'match_the_following.html', {'success': 'Match exercise created successfully!'})
        except Exception as e:
            return render(request, 'match_the_following.html', {'error': f'Error creating exercise: {str(e)}'})
            
    return render(request, 'match_the_following.html')

def list_match_following(request):
    """
    View to display all 'match the following' exercises from the database.
    """
    try:
        # Fetch all match the following exercises from Supabase
        response = supabase.table("match_the_following_level").select("*").order("created_at", desc=True).execute()
        match_following_levels = response.data
        total_count = supabase.table("match_the_following_level").select("id", count="exact").limit(0).execute()
        context = {
            'match_following_levels': match_following_levels,
            'total_count': total_count
        }
    except Exception as e:
        context = {
            'match_following_levels': [],
            'error': f'Error fetching data: {str(e)}',
            'total_count': 0
        }
    return render(request, 'match_the_following_list.html', context)