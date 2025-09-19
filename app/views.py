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
import random

def ServiceLesson(result, level_type, lesson_id ):
    if result.data and len(result.data) > 0:
            level_id = result.data[0]['id']  # This is the inserted quiz_data id
            print("Inserted level_id:", level_id)

    lessons_data = {"level_id": level_id , "level_type": level_type, "sub_level_id": 0}
    # Fetch the existing row
    row = supabase.table("lessons").select("data").eq("id", lesson_id).single().execute()
    current_data = row.data["data"]
    if not current_data:
        current_data = []
    current_data.append(lessons_data)
    supabase.table("lessons").update({"data": current_data}).eq("id", lesson_id).execute()


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
    if request.method == 'POST':
        path_title = request.POST.get('path_title')

        # Step 1: Create the path with empty lessons array
        path_data = {
            "title": path_title,
            "lessons": []
        }
        try:
            path_result = supabase.table("paths").insert(path_data).execute()
            if not path_result.data or len(path_result.data) == 0:
                return render(request, 'paths.html', {'error': 'Path creation failed.'})
            path_id = path_result.data[0]['id']

            # Step 2: Create 5 lessons and collect their IDs
            lesson_ids = []
            lesson_name = ['Alphabets', 'Vocabs', 'Kanji', 'Conversations', 'Grammar', 'Embassy_Kanji_Meanings', 'Embassy_Special_Meanings', 'Embassy_Sample_Questions']
            lesson_type = [2, 4, 16, 1, 8, 32, 64, 128]
            for i in range(0, 5):
                lesson_data = {
                    "path_id": path_id,
                    "lesson_title": f"Path {path_id}: Lesson-{i+1}: {lesson_name[i]} ",
                    "lesson_description": lesson_name[i],
                    "data": [],
                    "lesson_type": lesson_type[i],
                    "image_url": None
                }
                lesson_result = supabase.table("lessons").insert([lesson_data]).execute()
                print("Lesson insert result:", lesson_result.data)
                if lesson_result.data and len(lesson_result.data) > 0:
                    lesson_ids.append(lesson_result.data[0]['id'])
                else:
                    print(f"Lesson {i+1} insert failed!")

            # Step 3: Update the path with the lesson IDs
            print("Collected lesson_ids:", lesson_ids)
            print("Path insert result:", path_result.data)
            
            # Direct update without fetching current lessons since we just created the path
            update_result = supabase.table("paths").update({"lessons": lesson_ids}).eq("id", path_id).execute()
            print("Update result:", update_result)

            return render(request, 'paths.html', {'success': 'Path and 5 lessons created successfully!'})
        except Exception as e:
            return render(request, 'paths.html', {'error': f'Error creating path: {str(e)}'})

    return render(request, 'paths.html')

def list_paths(request):
    """
    View to display all paths from the database.
    """
    try:
        # Fetch all paths from Supabase
        response = supabase.table("paths").select("*").order("created_at").execute()
        paths = response.data
        lesson_data = []
        # for path in paths:
        #     lessons = path.get('lessons', [])
        #     path_lessons = []
        #     for lesson_id in lessons:
        #         data = supabase.table('lessons').select('*').eq('id', lesson_id).single().execute()
        #         if data.data:
        #             path_lessons.append(data.data)
        #     lesson_data.append({'path_id': path['id'], 'lessons': path_lessons})
        count = supabase.table("paths").select("id", count="exact").limit(0).execute()
        
        context = {
            'paths': paths,
            'lesson_data': lesson_data,  # Changed from 'lessons' to 'lesson_data'
            'total_count': count.count
        }
    except Exception as e:
        context = {
            'paths': [],
            'lesson_data': [],  # Changed from 'lessons' to 'lesson_data'
            'error': f'Error fetching data: {str(e)}',
            'total_count': 0
        }
    return render(request, 'path_list.html', context)

def path_detail(request, id):
    data = supabase.table('lessons').select('*').order("created_at").eq('path_id', id).execute()

    context = {
        'lesson_data': data.data,  
    }
    return render(request, 'path_detail.html', context=context)

def lesson_detail(request, id):
    try:
        # Fetch the lesson data
        lesson_response = supabase.table('lessons').select('*').eq('id', id).single().execute()
        lesson = lesson_response.data
        
        if not lesson:
            return render(request, 'lesson_detail.html', {'error': 'Lesson not found'})
        
        lesson_questions = []
        
        # Iterate through each level in the lesson data
        for level_data in lesson.get('data', []):
            level_type = level_data.get('level_type')
            level_id = level_data.get('level_id')
            sub_level_id = level_data.get('sub_level_id', 0)
            
            # Determine which table to query based on level_type
            table_map = {
                0: 'letters',           # Letters/Alphabet
                1: 'quiz_levels',       # Quiz questions
                2: 'word_game_level',   # Word games
                3: 'match_the_following_level',  # Match the following
                4: 'word_form_levels',  # Word form exercises
                5: 'fill_blanks_level', # Fill in the blanks
                6: 'information_level', # Information levels
                7: 'meaning_level',     # Meaning exercises
                8: 'quiz_levels',       # Additional quiz type
                9: 'rearrange_words_level',  # Rearrange words
                10: 'conversation_level',     # Conversations
                11: 'combined_words_level'   # Combined words
            }
            
            table_name = table_map.get(level_type)
            if not table_name:
                continue
                
            try:
                # For letters, we need to handle sub_level_id differently
                if level_type == 0 and sub_level_id > 0:
                    question_response = supabase.table(table_name).select('*').eq('id', sub_level_id).execute()
                else:
                    question_response = supabase.table(table_name).select('*').eq('id', level_id).execute()
                
                if question_response.data:
                    for question in question_response.data:
                        question['level_type'] = level_type
                        question['level_type_name'] = get_level_type_name(level_type)
                        lesson_questions.append(question)
                        
            except Exception as e:
                print(f"Error fetching data from {table_name}: {str(e)}")
                continue
        
        context = {
            'lesson': lesson,
            'lesson_questions': lesson_questions,
            'total_questions': len(lesson_questions)
        }
        
    except Exception as e:
        context = {
            'lesson': None,
            'lesson_questions': [],
            'error': f'Error fetching lesson data: {str(e)}',
            'total_questions': 0
        }
    
    return render(request, 'lesson_detail.html', context)

def get_level_type_name(level_type):
    """Helper function to get human-readable level type names"""
    type_names = {
        0: 'Letters/Alphabet',
        1: 'Quiz Questions',
        2: 'Word Games',
        3: 'Match the Following',
        4: 'Word Form Exercises',
        5: 'Fill in the Blanks',
        6: 'Information Levels',
        7: 'Meaning Exercises',
        8: 'Quiz Questions (Type 2)',
        9: 'Rearrange Words',
        10: 'Conversations',
        11: 'Combined Words'
    }
    return type_names.get(level_type, 'Unknown Type')



#--------------------Lession-------------------------------------------->>>
def create_individual_lesson(request):
    """
    Allow users to create a lesson not tied to any path (path_id=None).
    """
    if request.method == 'POST':
        lesson_title = request.POST.get('lessonTitle')
        lesson_description = request.POST.get('lessonDescription', '')
        image_file = request.FILES.get('image')
        lesson_type = request.POST.getlist('lessonCategory')
        lesson_type = sum(int(val) for val in lesson_type)

        # Handle image upload
        image_url = None
        if image_file:
            file_name = f"images/{image_file.name}"
            try:
                supabase.storage.from_("images").upload(file_name, image_file.read())
                image_url = f"/storage/v1/object/public/images/{file_name}"
            except Exception as e:
                return render(request, 'lesson_form_indivisual.html', {'error': f'Image upload failed: {str(e)}'})

        

        # Prepare lesson data
        lesson_data = [{
            
            'lesson_title': lesson_title,
            'lesson_description': lesson_description,
            'lesson_type': lesson_type,
            'image_url': image_url
        }]
        supabase.table("lessons").insert(lesson_data).execute()
        return render(request, 'lesson_form_indivisual.html', {'success': 'Lesson created successfully.'})

    return render(request, 'lesson_form_indivisual.html')

# def create_lesson(request):
#     if request.method == 'POST':
#         lesson_title = request.POST.get('lessonTitle')
#         lesson_description = request.POST.get('lessonDescription', '')
#         image_file = request.FILES.get('image')
#         lesson_type = request.POST.getlist('lessonCategory')

#         lesson_type = sum(int(val) for val in lesson_type)

#          # ------uploading the image to supabase bucket
#         image_url = None
#         if image_file:
#             # return render(request, 'word_form.html', {'error': 'All fields are required.'})

#             # 1. Upload image file to Supabase Storage
#             file_name = f"images/{image_file.name}"  # folder 'image/' inside bucket
#             try:
#                 res = supabase.storage.from_("images").upload(file_name, image_file.read())
#             except Exception as e:
#                 return render(request, 'word_form.html', {'error': f'Upload failed: {str(e)}'})

#             # # 2. Build public URL (no signed URL needed)
#             image_url = f"/storage/v1/object/public/images/{file_name}"

#         # Collect all level configurations
#         levels = []
#         index = 0
#         while True:
#             level_type = request.POST.get(f'level_type_{index}')
#             level_id = request.POST.get(f'level_id_{index}')
#             sub_level_id = request.POST.get(f'sub_level_id_{index}')
#             if level_type is None or level_id is None :
#                 break
#             levels.append({
#             'level_type': int(level_type),
#             'level_id': int(level_id),
#             'sub_level_id': int(sub_level_id)
#             })
#             index += 1

#         # Prepare lesson data as JSON
#         lesson_data = [{
#         'lesson_title': lesson_title,
#         'lesson_description': lesson_description,
#         'data': levels,
#         'lesson_type': lesson_type,
#         'image_url': image_url
#             }]
#     # Insert as JSONB (not as a string)
#         supabase.table("lessons").insert(lesson_data).execute()
        
#         print('Lesson JSON:', lesson_data)

#         return redirect('create_lesson')  # Redirect after POST

#     return render(request, 'lesson_form.html')

def get_level_ids(request):
    lesson_type = request.GET.get('type')
    level_ids = []
    
    if lesson_type == '5':
        table = "fill_blanks_level"
    elif lesson_type == '0':
        table = "letters"
    elif lesson_type == '1':
        table = "quiz_levels"
    elif lesson_type == '2':
        table = "word_game_level"
    elif lesson_type == '3':
        table = "match_the_following_level"
    elif lesson_type == '4':
        table = "word_form_levels"
    elif lesson_type == '6':
        table = "information_level"
    elif lesson_type == '7':
        table = "meaning_level"
    elif lesson_type == '8':
        table = "quiz_lev   els"
    elif lesson_type == '11':  # Combined words
        table = "combined_words_level"
    else:
        return JsonResponse({'level_ids': []})

    if lesson_type in ['1', '2', '3', '4', '5','6', '8']:
        response = supabase.table(table).select("id, title").execute()
        print(response)
        level_ids = []
        for row in response.data:
            label = row.get('title', str(row['id']))
            level_ids.append({'value': row['id'], 'label': label})
        return JsonResponse({'level_ids': level_ids})
    
    if lesson_type == '0':
        response = supabase.table(table).select("id, letter_name").execute()
        print(response)
        level_ids = []
        for row in response.data:
            label = row.get('letter_name', str(row['id']))
            level_ids.append({'value': row['id'], 'label': label})
        return JsonResponse({'level_ids': level_ids})
    
    if lesson_type == '6':
        response = supabase.table(table).select("id, created_at").execute()
        print(response)
        level_ids = []
        for row in response.data:
            label = row.get(str(row['id']))
            level_ids.append({'value': row['id'], 'label': label})
        return JsonResponse({'level_ids': level_ids})
    
    if lesson_type == '7':
        response = supabase.table(table).select("id, word").execute()
        print(response)
        level_ids = []
        for row in response.data:
            label = row.get('word', str(row['id']))
            level_ids.append({'value': row['id'], 'label': label})
        return JsonResponse({'level_ids': level_ids})

    return JsonResponse({'error': 'no level type found!'})
    
def list_lessons(request):
    """
    View to display all lessons from the database, with optional filtering by path.
    """
    try:
        path_id = request.GET.get('path_id')
        paths_response = supabase.table("paths").select("id, title").order("created_at", desc=True).execute()
        paths = paths_response.data

        path_id = request.GET.get('path_id')
        query = supabase.table("lessons").select("*").order("created_at", desc=True)
        count_query = supabase.table("lessons").select("id", count="exact").limit(0)
        if path_id:
            query = query.eq("path_id", path_id)
            count_query = count_query.eq("path_id", path_id)
        response = query.execute()
        lessons = response.data
        count = count_query.execute()
        context = {
            'lessons': lessons,
            'total_count': count.count,
            'selected_path_id': path_id,
            'paths': paths
        }
    except Exception as e:
        context = {
            'lessons': [],
            'error': f'Error fetching data: {str(e)}',
            'total_count': 0,
            'selected_path_id': path_id if 'path_id' in locals() else None
        }
    return render(request, 'lesson_list.html', context)

def delete_lesson(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lesson_id = data.get('id')
            supabase.table("lessons").delete().eq("id", lesson_id).execute()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


def edit_lesson(request, lesson_id):
    lesson = supabase.table("lessons").select("*").eq("id", lesson_id).single().execute().data
    if not lesson:
        return render(request, 'lesson_form.html', {'error': 'Lesson not found.'})

    if request.method == 'POST':
        lesson_title = request.POST.get('lessonTitle')
        lesson_description = request.POST.get('lessonDescription', '')
        # Update logic for levels if needed

        update_data = {
            'lesson_title': lesson_title,
            'lesson_description': lesson_description,
            # Add other fields as needed
        }
        supabase.table("lessons").update(update_data).eq("id", lesson_id).execute()
        return redirect('list_lessons')

    return render(request, 'lesson_form.html', {'lesson': lesson})



def get_lesson(request, id):
    lessons = supabase.table("lessons").select("*").eq("path_id", id).execute().data
    # Each lesson in 'lessons' will have its 'id' and other fields
    return JsonResponse({'lessons': lessons}, safe=False)

#-------------------------lessonEnd--------------------------------->>>>>>>>>>>



def create_quiz(request):
    paths = supabase.table('paths').select("id, title").execute()
    lessons = supabase.table('lessons').select("id, lesson_title").execute()
    

    lesson_ids = []
    for row in lessons.data:
        title = row.get('lesson_title', str(row['id']))
        lesson_ids.append({'id': row['id'], 'title': title})

    path_ids = []
    for row in paths.data:
        title = row.get('title', str(row['id']))
        path_ids.append({'id': row['id'], 'title': title})
        # return JsonResponse({'level_ids': path_ids})
    
    if request.method == 'POST':
        question_text = request.POST.get('questionText')
        correct_option = int(request.POST.get('correctOption'))
        question_type = request.POST.get('languagePair')
        title_text = request.POST.get('titleText')

        path_id = request.POST.get('path_id')
        lesson_id = request.POST.get('lesson_id')

        # Collect all options dynamically
        options = []
        option_index = 0
        while True:
            opt = request.POST.get(f'option_{option_index}')
            if opt is None:
                break
            options.append(wrap_preeti_in_sentence(opt))
            option_index += 1

        if question_type =='english_nepali':
            question_text = re.sub(r"<(.*?)>", r'<font="Preeti font  SDF">\1</font>', question_text)
        #elif question_type == 'english_japanese':
            
        elif question_type == 'nepali':
            question_text = f'<font="Preeti font  SDF">{question_text}</font>'
        # Create your quiz_data structure
        quiz_data = [{
            "data": {
                "questionText": question_text,
                "options": options,
                "correctOption": correct_option,
                
            },
            "title": title_text
        }]

        result = supabase.table("quiz_levels").insert(quiz_data).execute()
        print(quiz_data)
        if result.data and len(result.data) > 0:
            level_id = result.data[0]['id']  # This is the inserted quiz_data id
            print("Inserted quiz level_id:", level_id)

        #add to lessons
        lessons_data = {"level_id": level_id, "level_type": 1, "sub_level_id": 0}
        # Fetch the existing row
        row = supabase.table("lessons").select("data").eq("id", lesson_id).single().execute()
        current_data = row.data["data"]
        if not current_data:
            current_data = []
        current_data.append(lessons_data)
        supabase.table("lessons").update({"data": current_data}).eq("id", lesson_id).execute()

        return render(request, 'quiz.html', {'success': 'Word inserted successfully.', 'path_ids': path_ids, 'lesson_ids': lesson_ids} )

    return render(request, 'quiz.html', {'path_ids': path_ids, 'lesson_ids': lesson_ids})


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
    paths = supabase.table('paths').select("id, title").execute()
    lessons = supabase.table('lessons').select("id, lesson_title").execute()
    

    lesson_ids = []
    for row in lessons.data:
        title = row.get('lesson_title', str(row['id']))
        lesson_ids.append({'id': row['id'], 'title': title})

    path_ids = []
    for row in paths.data:
        title = row.get('title', str(row['id']))
        path_ids.append({'id': row['id'], 'title': title})

    if request.method == 'POST':
        question_text = request.POST.get('questionText')
        correct_option = request.POST.get('correctOption')
        # audio_file = request.FILES.get('audio')
        image_file = request.FILES.get('image')
        path_id = request.POST.get('path_id')
        lesson_id = request.POST.get('lesson_id')
        title = request.POST.get('titleText')
        

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
            # request.POST.get('topic_1'),
        ]
        meaning = request.POST.get('letterMeaning')
        if meaning:
            meaning = re.sub(r"<(.*?)>", r'<font="Preeti font  SDF">\1</font>', meaning)

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
        
        # if not audio_file or not options:
        #     return render(request, 'word_form.html', {'error': 'All fields are required.'})

        # # 1. Upload audio file to Supabase Storage
        # file_name = f"audio/{audio_file.name}"  # folder 'audio/' inside bucket
        # try:
        #     res = supabase.storage.from_("audio").upload(file_name, audio_file.read())
        # except Exception as e:
        #     return render(request, 'word_form.html', {'error': f'Upload failed: {str(e)}'})

        # # 2. Build public URL (no signed URL needed)
        # audio_url = f"http://64.227.141.251:8000/storage/v1/object/public/audio/{file_name}"

        # ------uploading the image to supabase bucket
        image_url = None
        if image_file:
            # return render(request, 'word_form.html', {'error': 'All fields are required.'})

        # 1. Upload image file to Supabase Storage
            file_name = f"images/{image_file.name}"  # folder 'image/' inside bucket
            try:
                res = supabase.storage.from_("images").upload(file_name, image_file.read())
            except Exception as e:
                return render(request, 'word_form.html', {'error': f'Upload failed: {str(e)}'})

            # # 2. Build public URL (no signed URL needed)
            image_url = f"/storage/v1/object/public/images/{file_name}"


        fill_blank = [
            {
                "data": {
                    "questionText": question_text,
                    "options": options,
                    "correctOption": int(correct_option),
                    
                    # "audioUrl": audio_url,
                },
                "letter_info": {
                    "title": letter_title,
                    "topics": topics,
                    "meaning": meaning,
                    
                },
                "imageUrl": image_url,
                "title": title
            }
        ]
        print(fill_blank)
        result = supabase.table("fill_blanks_level").insert(fill_blank).execute()
        ServiceLesson(result, 5, lesson_id )
    return render(request, 'fill_blank.html', {'path_ids': path_ids, 'lesson_ids': lesson_ids})

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
    paths = supabase.table('paths').select("id, title").execute()
    lessons = supabase.table('lessons').select("id, lesson_title").execute()
    

    lesson_ids = []
    for row in lessons.data:
        title = row.get('lesson_title', str(row['id']))
        lesson_ids.append({'id': row['id'], 'title': title})

    path_ids = []
    for row in paths.data:
        title = row.get('title', str(row['id']))
        path_ids.append({'id': row['id'], 'title': title})

    if request.method == 'POST':
        audio_file = request.FILES.get('audioFile')
        image_file = request.FILES.get('imageFile')
        meaning = request.POST.get('sound')
        path_id = request.POST.get('path_id')
        lesson_id = request.POST.get('lesson_id')
        romaji = request.POST.get('romaji')

        if meaning:
            meaning = re.sub(r"<(.*?)>", r'<font="Preeti font  SDF">\1</font>', meaning)

        
        answer = []
        count = 1
        while True:
            letter = request.POST.get(f'letter_{count}')
            if letter is None:
                break
            answer.append(letter)
            count += 1
        

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
        if  not answer or not options:
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
        audio_url = ''
        if audio_file:
            file_name = f"word-form-audio/{audio_file.name}"  # folder 'audio/' inside bucket
            try:
                res = supabase.storage.from_("word-form-audio").upload(file_name, audio_file.read())
            except Exception as e:
                return render(request, 'word_form.html', {'error': f'Upload failed: {str(e)}'})

            # 2. Build public URL (no signed URL needed)
            audio_url = f"/storage/v1/object/public/word-form-audio/{file_name}"

        image_url = None
        if image_file:
            # return render(request, 'word_form.html', {'error': 'All fields are required.'})

            # 1. Upload image file to Supabase Storage
            file_name = f"images/{image_file.name}"  # folder 'image/' inside bucket
            try:
                res = supabase.storage.from_("images").upload(file_name, image_file.read())
            except Exception as e:
                return render(request, 'word_form.html', {'error': f'Upload failed: {str(e)}'})

            # # 2. Build public URL (no signed URL needed)
            image_url = f"/storage/v1/object/public/images/{file_name}"

        # 3. Insert into DB
        word_data = [{
            "audioUrl": audio_url,
            "imageUrl": image_url,
            "answer": answer,
            "options": options,
            "sound": meaning,
            "romaji": romaji
        }]
        result = supabase.table("word_form_levels").insert(word_data).execute()
        ServiceLesson(result, 4, lesson_id )

        return render(request, 'word_form.html', {'success': 'Word inserted successfully.', 'path_ids': path_ids, 'lesson_ids': lesson_ids})

    return render(request, 'word_form.html', {'path_ids': path_ids, 'lesson_ids': lesson_ids})


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
    paths = supabase.table('paths').select("id, title").execute()
    lessons = supabase.table('lessons').select("id, lesson_title").execute()
    

    lesson_ids = []
    for row in lessons.data:
        title = row.get('lesson_title', str(row['id']))
        lesson_ids.append({'id': row['id'], 'title': title})

    path_ids = []
    for row in paths.data:
        title = row.get('title', str(row['id']))
        path_ids.append({'id': row['id'], 'title': title})

    if request.method == 'POST':
        # Collect all the pairs
        match_pairs = []
        pair_index = 0
        
        path_id = request.POST.get('path_id')
        lesson_id = request.POST.get('lesson_id')
        word_type = request.POST.get('language_type')
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
                # if re.fullmatch(r'[A-Za-z0-9\s\.\-\,\']+', nepali_value.strip()) and len(nepali_value.strip()) > 1:
                #     nepali_display = nepali_value.strip()

                if word_type =='nepali_word':
                    nepali_value = f'<font face="Preeti font  SDF">{nepali_value.strip()}</font>'

                pair_dict = {
                    "nepali": nepali_value,
                    "japanese": japanese_value.strip()
                }
                match_pairs.append(pair_dict)
            
            pair_index += 1
        
        # Create the match_data structure
        match_data = [{
            "data": match_pairs,
            "title": request.POST.get('titleText')
        }]
        
        print("Match Following Data:", match_data)
        
        # Insert into database
        try:
            result = supabase.table("match_the_following_level").insert(match_data).execute()
            ServiceLesson(result, 3, lesson_id )
            return render(request, 'match_the_following.html', {'success': 'Match exercise created successfully!', 'path_ids': path_ids, 'lesson_ids': lesson_ids})
        except Exception as e:
            return render(request, 'match_the_following.html', {'error': f'Error creating exercise: {str(e)}'})
            
    return render(request, 'match_the_following.html', {'path_ids': path_ids, 'lesson_ids': lesson_ids})


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




def create_word_game(request):
    paths = supabase.table('paths').select("id, title").execute()
    lessons = supabase.table('lessons').select("id, lesson_title").execute()
    
    lesson_ids = []
    for row in lessons.data:
        title = row.get('lesson_title', str(row['id']))
        lesson_ids.append({'id': row['id'], 'title': title})

    path_ids = []
    for row in paths.data:
        title = row.get('title', str(row['id']))
        path_ids.append({'id': row['id'], 'title': title})

    if request.method == 'POST':
        title = request.POST.get('title')
        options = []
        for i in range(5):
            opt = request.POST.get(f'option_{i}')
            if opt is not None:
                options.append(opt)

        path_id = request.POST.get('path_id')
        lesson_id = request.POST.get('lesson_id')

        valid_words = []
        words_count = 0
        while True:
            words = request.POST.get(f'valid_{words_count}')
            if words is None:
                break
            valid_words.append(words)
            words_count +=1

        data = [{
            'options':options,
            'valid_words': valid_words,
            'title': title
        }]
        print(data)
        result = supabase.table("word_game_level").insert(data).execute()
        ServiceLesson(result, 2, lesson_id )
        return render(request, 'word_game.html', {'success': 'Word inserted successfully.', 'path_ids': path_ids, 'lesson_ids': lesson_ids})
    
    return render(request, 'word_game.html', {'path_ids': path_ids, 'lesson_ids': lesson_ids})

def list_word_games(request):
    """
    View to display all word game levels from the database.
    """
    try:
        response = supabase.table("word_game_level").select("*").order("created_at", desc=True).execute()
        word_games = response.data
        total_count = len(word_games)
        context = {
            'word_games': word_games,
            'total_count': total_count
        }
    except Exception as e:
        context = {
            'word_games': [],
            'error': f'Error fetching data: {str(e)}',
            'total_count': 0
        }
    return render(request, 'word_game_list.html', context)


def create_letters(request):
    paths = supabase.table('paths').select("id, title").execute()
    lessons = supabase.table('lessons').select("id, lesson_title").execute()

    lesson_ids = []
    for row in lessons.data:
        title = row.get('lesson_title', str(row['id']))
        lesson_ids.append({'id': row['id'], 'title': title})

    path_ids = []
    for row in paths.data:
        title = row.get('title', str(row['id']))
        path_ids.append({'id': row['id'], 'title': title})

    if request.method == 'POST':
        english_letter = request.POST.get('letter_name')
        nepali_letter = request.POST.get('nepali_letter')
        japanese_letter = request.POST.get('japanese_letter')
        letter_collection = request.POST.get('japanese_character_type')
        audio_file = request.FILES.get('audio')
        title = request.FILES.get('title')

        onyomi = request.POST.get('onyomi')
        kunyomi = request.POST.get('kunyomi')

        path_id = request.POST.get('path_id')
        lesson_id = request.POST.get('lesson_id')

        if nepali_letter:
            nepali_letter = f'<font="Preeti font  SDF">{nepali_letter}</font>'

         # 1. Upload audio file to Supabase Storage
        audio_url = None
        if audio_file:
            file_name = f"letter-audio/{audio_file.name}"  # folder 'audio/' inside bucket
            try:
                res = supabase.storage.from_("letter-audio").upload(file_name, audio_file.read())
            except Exception as e:
                return render(request, 'word_form.html', {'error': f'Upload failed: {str(e)}'})

            # 2. Build public URL (no signed URL needed)
            audio_url = f"/storage/v1/object/public/letter-audio/{file_name}"

        data = [{
            'collection_id': letter_collection,
            'letter_name': english_letter,
            'nepali_text': nepali_letter,
            'japanese_text': japanese_letter,
            'letter_info': {'onyomi': onyomi, 'kunyomi': kunyomi},
            'audio': audio_url,
            'title': title
        }]
        print(data)
        result = supabase.table('letters').insert(data).execute()
        
        if result.data and len(result.data) > 0:
            level_id = result.data[0]['id']  # This is the inserted quiz_data id
            print("Inserted letter level_id:", level_id)

        #add to lessons
        lessons_data = {"level_id": int(letter_collection), "level_type": 0, "sub_level_id": level_id}
        # Fetch the existing row
        row = supabase.table("lessons").select("data").eq("id", lesson_id).single().execute()
        current_data = row.data["data"]
        if not current_data:
            current_data = []
        current_data.append(lessons_data)
        supabase.table("lessons").update({"data": current_data}).eq("id", lesson_id).execute()

        return render(request, 'letters_tracing.html', {'success': 'Word inserted successfully.', 'path_ids': path_ids, 'lesson_ids': lesson_ids})
    
    return render(request, 'letters_tracing.html', {'path_ids': path_ids, 'lesson_ids': lesson_ids})

def list_letters(request):
    """
    View to display all letters from the database with pagination.
    """
    try:
        # Get pagination params
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))
        offset = (page - 1) * limit

        # Get search/filter params
        search = request.GET.get('search', '').strip()
        collection_id = request.GET.get('collection_id', '').strip()

        # Build query
        query = supabase.table("letters").select("*").order("created_at", desc=True)
        count_query = supabase.table("letters").select("id", count="exact").limit(0)

        # Apply filters
        if search:
            query = query.ilike("letter_name", f"%{search}%")
            count_query = count_query.ilike("letter_name", f"%{search}%")
        
        if collection_id:
            query = query.eq("collection_id", collection_id)
            count_query = count_query.eq("collection_id", collection_id)

        # Apply pagination
        query = query.range(offset, offset + limit - 1)

        # Execute queries
        response = query.execute()
        count_response = count_query.execute()

        letters = response.data
        total_count = count_response.count

        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        has_previous = page > 1
        has_next = page < total_pages

        context = {
            'letters': letters,
            'current_page': page,
            'total_pages': total_pages,
            'total_count': total_count,
            'has_previous': has_previous,
            'has_next': has_next,
            'previous_page': page - 1 if has_previous else None,
            'next_page': page + 1 if has_next else None,
            'search': search,
            'collection_id': collection_id,
            'limit': limit
        }

    except Exception as e:
        context = {
            'letters': [],
            'error': f'Error fetching data: {str(e)}',
            'current_page': 1,
            'total_pages': 0,
            'total_count': 0,
            'has_previous': False,
            'has_next': False,
            'search': '',
            'collection_id': '',
            'limit': 10
        }

    return render(request, 'lists/list_letters.html', context)



def delete_letter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            letter_id = data.get('id')
            supabase.table("letters").delete().eq("id", letter_id).execute()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

def information_level(request):
    paths = supabase.table('paths').select("id, title").execute()
    lessons = supabase.table('lessons').select("id, lesson_title").execute()
    

    lesson_ids = []
    for row in lessons.data:
        title = row.get('lesson_title', str(row['id']))
        lesson_ids.append({'id': row['id'], 'title': title})

    path_ids = []
    for row in paths.data:
        title = row.get('title', str(row['id']))
        path_ids.append({'id': row['id'], 'title': title})

    if request.method == 'POST':
        title = request.POST.get('letterTitle')
        meaning = request.POST.get('letterMeaning')
        if meaning:
            meaning = re.sub(r"<(.*?)>", r'<font="Preeti font  SDF">\1</font>', meaning)
        Onyomi = request.POST.get('topic_0')
        Kunyomi = request.POST.get('topic_1')
        image_file = request.FILES.get('image')
        audio_file = request.FILES.get('audio')
        kanji = request.FILES.get('kanji')

        path_id = request.POST.get('path_id')
        lesson_id = request.POST.get('lesson_id')
        
        use_cases = []
        usecase_count = 0
        while True:
            use_case = request.POST.get(f'option_{usecase_count}')
            if use_case is None:
                break
            use_case = re.sub(r"<(.*?)>", r'<font="Preeti font  SDF">\1</font>', use_case)
            use_cases.append(use_case)
            usecase_count += 1
        

        # ------uploading the image to supabase bucket
        image_url = None
        if image_file:
            # return render(request, 'word_form.html', {'error': 'All fields are required.'})

            # 1. Upload image file to Supabase Storage
            file_name = f"images/{image_file.name}"  # folder 'image/' inside bucket
            try:
                res = supabase.storage.from_("images").upload(file_name, image_file.read())
            except Exception as e:
                return render(request, 'word_form.html', {'error': f'Upload failed: {str(e)}'})

            # # 2. Build public URL (no signed URL needed)
            image_url = f"/storage/v1/object/public/images/{file_name}"
        
        audio_url = None
        if audio_file:
            file_name = f"information-level-audio/{audio_file.name}"
            try:
                supabase.storage.from_("information-level-audio").upload(file_name, audio_file.read())
                audio_url = f"/storage/v1/object/public/information-level-audio/{file_name}"
            except Exception as e:
                return render(request, 'information_level.html', {
                    'error': f'Audio upload failed: {str(e)}',
                    'path_ids': path_ids,
                    'lesson_ids': lesson_ids
                })

        data = [{
            "letter_info": {"title": kanji, "topics":[Onyomi, Kunyomi], "meaning": meaning},
            "use_cases": use_cases,
            "image_url": image_url,
            "title": title,
            "audio_url": audio_url
        }]

        print(data)
        result = supabase.table('information_level').insert(data).execute()
        ServiceLesson(result, 6, lesson_id )
    return render(request, 'information_level.html', {'path_ids': path_ids, 'lesson_ids': lesson_ids})

def information_level2(request):
    paths = supabase.table('paths').select("id, title").execute()
    lessons = supabase.table('lessons').select("id, lesson_title").execute()
    

    lesson_ids = []
    for row in lessons.data:
        title = row.get('lesson_title', str(row['id']))
        lesson_ids.append({'id': row['id'], 'title': title})

    path_ids = []
    for row in paths.data:
        title = row.get('title', str(row['id']))
        path_ids.append({'id': row['id'], 'title': title})

    if request.method == 'POST':
        title = request.POST.get('title')
        question = request.POST.get('letterTitle')
        meaning = request.POST.get('letterMeaning')
        if meaning:
            meaning = re.sub(r"<(.*?)>", r'<font="Preeti font  SDF">\1</font>', meaning)
        romaji = request.POST.get('romaji')
        nepali_meaning = request.POST.get('nepali_meaning')
        nepali_meaning = f'<font="Preeti font  SDF">{nepali_meaning}</font>'  
        # Onyomi = request.POST.get('topic_0')
        # Kunyomi = request.POST.get('topic_1')
        image_file = request.FILES.get('image')
        
        path_id = request.POST.get('path_id')
        lesson_id = request.POST.get('lesson_id')

        use_cases = []
        usecase_count = 0
        while True:
            use_case = request.POST.get(f'option_{usecase_count}')
            if use_case is None:
                break
            use_cases.append(use_case)
            usecase_count += 1
        

        # ------uploading the image to supabase bucket
        image_url = None
        if image_file:
            # return render(request, 'word_form.html', {'error': 'All fields are required.'})

            # 1. Upload image file to Supabase Storage
            file_name = f"images/{image_file.name}"  # folder 'image/' inside bucket
            try:
                res = supabase.storage.from_("images").upload(file_name, image_file.read())
            except Exception as e:
                return render(request, 'word_form.html', {'error': f'Upload failed: {str(e)}'})

            # # 2. Build public URL (no signed URL needed)
            image_url = f"/storage/v1/object/public/images/{file_name}"

        data = [{
            "letter_info": {
                "title": question,
                "romaji": romaji,
                "meaning": meaning,
                "nepali_meaning": nepali_meaning
            },
            "use_cases": use_cases,
            "image_url": image_url,
            "title": title,
        }]

        print(data)
        result = supabase.table('information_level').insert(data).execute()
        ServiceLesson(result, 6, lesson_id )
    return render(request, 'info_level2.html', {'path_ids': path_ids, 'lesson_ids': lesson_ids})


def create_meaning_level(request):
    paths = supabase.table('paths').select("id, title").execute()
    lessons = supabase.table('lessons').select("id, lesson_title").execute()
    

    lesson_ids = []
    for row in lessons.data:
        title = row.get('lesson_title', str(row['id']))
        lesson_ids.append({'id': row['id'], 'title': title})

    path_ids = []
    for row in paths.data:
        title = row.get('title', str(row['id']))
        path_ids.append({'id': row['id'], 'title': title})

    if request.method == 'POST':
        typ = request.POST.get('type')
        word = request.POST.get('word')
        meaning = request.POST.get('meaning')
        structure = request.POST.get('structure')
        usage = request.POST.get('usage')
        examples = []
        index = 1
        while True:
            japanese = request.POST.get(f'examples_japanese_{index}')
            english = request.POST.get(f'examples_english_{index}')
            if japanese is None and english is None:
                break
            if (japanese and japanese.strip()) or (english and english.strip()):
                examples.append({'japanese': japanese or '', 'english': english or ''})
            index += 1
        
        tips = request.POST.get('tips')
        path_id = request.POST.get('path_id')
        lesson_id = request.POST.get('lesson_id')

        data = [{
            "type": typ,
            "word": word,
            "meaning": meaning,
            "structure": structure,
            "usage": usage,
            "examples": examples,
            "tips": tips
        }]

        print(data)
        result = supabase.table('meaning_level').insert(data).execute()
        ServiceLesson(result, 7, lesson_id )
        return render(request, 'meaning_level.html', {'success': 'Data inserted successfully.', 'path_ids': path_ids, 'lesson_ids': lesson_ids})

    return render(request, 'meaning_level.html', {'path_ids': path_ids, 'lesson_ids': lesson_ids})


def create_rearrange(request):
    paths = supabase.table('paths').select("id, title").execute()
    lessons = supabase.table('lessons').select("id, lesson_title").execute()
    
    lesson_ids = []
    for row in lessons.data:
        title = row.get('lesson_title', str(row['id']))
        lesson_ids.append({'id': row['id'], 'title': title})

    path_ids = []
    for row in paths.data:
        title = row.get('title', str(row['id']))
        path_ids.append({'id': row['id'], 'title': title})

    if request.method == 'POST':
        path_id = request.POST.get('path_id')
        lesson_id = request.POST.get('lesson_id')
        
        # Answer data
        answer_nepali = request.POST.get('answer_nepali')
        answer_romaji = request.POST.get('answer_romaji')
        answer_english = request.POST.get('answer_english')
        answer_japanese = request.POST.get('answer_japanese')
        
        # Format Nepali text with Preeti font
        if answer_nepali:
            answer_nepali = f'<font="Preeti font  SDF">{answer_nepali}</font>'
        
        # Collect romaji question words
        # romaji_words = []
        # romaji_index = 0
        # while True:
        #     word = request.POST.get(f'romaji_word_{romaji_index}')
        #     if word is None:
        #         break
        #     if word.strip():
        #         romaji_words.append(word.strip())
        #     romaji_index += 1
        # random.shuffle(romaji_words)
        
        # Collect Japanese question words
        japanese_words = []
        japanese_index = 0
        while True:
            word = request.POST.get(f'japanese_word_{japanese_index}')
            if word is None:
                break
            if word.strip():
                japanese_words.append(word.strip())
            japanese_index += 1
        random.shuffle(japanese_words)

        # Validate required fields
        if not all([answer_romaji, answer_english, answer_japanese])  or not japanese_words:
            return render(request, 'rearrange.html', {
                'error': 'All fields are required.',
                'path_ids': path_ids,
                'lesson_ids': lesson_ids
            })
        
        # Create rearrange data structure
        rearrange_data = [{
            
                "data": {
                    "options": japanese_words ,
                    "correctAnswer": answer_japanese ,
                    
                },
                "rearrange_info": {
                    "englishmeaning": answer_english ,
                    "romanjimeaning": answer_romaji,
                    "nepalimeaning": answer_nepali
                },
                "title": answer_english  # Using English as title
            
        }]
        
        print("Rearrange Data:", rearrange_data)
        
        try:
            result = supabase.table("rearrange_words_level").insert(rearrange_data).execute()
            ServiceLesson(result, 9, lesson_id)  
            return render(request, 'rearrange.html', {
                'success': 'Rearrange exercise created successfully!',
                'path_ids': path_ids,
                'lesson_ids': lesson_ids
            })
        except Exception as e:
            return render(request, 'rearrange.html', {
                'error': f'Error creating exercise: {str(e)}',
                'path_ids': path_ids,
                'lesson_ids': lesson_ids
            })
    
    return render(request, 'rearrange.html', {'path_ids': path_ids, 'lesson_ids': lesson_ids})


@login_required
def create_conversation(request):
    paths = supabase.table('paths').select("id, title").execute()
    lessons = supabase.table('lessons').select("id, lesson_title").execute()

    lesson_ids = [{'id': row['id'], 'title': row.get('lesson_title', str(row['id']))} for row in lessons.data]
    path_ids = [{'id': row['id'], 'title': row.get('title', str(row['id']))} for row in paths.data]

    if request.method == 'POST':
        conversation_title = request.POST.get('conversation_title')
        path_id = request.POST.get('path_id')
        lesson_id = request.POST.get('lesson_id')

        # Collect all turns
        turns = []
        idx = 0
        while True:
            role = request.POST.get(f'role_{idx}')
            speaker = request.POST.get(f'speaker_{idx}')
            english = request.POST.get(f'english_{idx}')
            nepali = request.POST.get(f'nepali_{idx}')
            romaji = request.POST.get(f'romaji_{idx}')
            japanese = request.POST.get(f'japanese_{idx}')
            if not any([role, speaker, english, nepali, romaji, japanese]):
                break
            turns.append({
                "role": role,
                "speaker": speaker,
                "english": english,
                "nepali": f'<font="Preeti font  SDF">{nepali}</font>',
                "romaji": romaji,
                "japanese": japanese,
            })
            idx += 1

        if not conversation_title or not turns:
            return render(request, 'converstion.html', {
                'error': 'All fields are required.',
                'path_ids': path_ids,
                'lesson_ids': lesson_ids
            })

        # Save to Supabase
        conversation_data = [{
            "conversation_title": conversation_title,
            "data": turns
        }]
        try:
            print(conversation_data)
            result = supabase.table("conversation_level").insert(conversation_data).execute()
            ServiceLesson(result, 10, lesson_id)
            return render(request, 'converstion.html', {
                'success': 'Conversation rearrange exercise created successfully!',
                'path_ids': path_ids,
                'lesson_ids': lesson_ids
            })
        except Exception as e:
            return render(request, 'converstion.html', {
                'error': f'Error creating exercise: {str(e)}',
                'path_ids': path_ids,
                'lesson_ids': lesson_ids
            })

    return render(request, 'converstion.html', {'path_ids': path_ids, 'lesson_ids': lesson_ids})

# Add these edit views to your existing views.py file

def edit_quiz(request, quiz_id):
    """Edit quiz question"""
    try:
        # Fetch existing quiz
        quiz_response = supabase.table("quiz_levels").select("*").eq("id", quiz_id).single().execute()
        quiz = quiz_response.data
        
        # Get paths and lessons for dropdowns
        paths = supabase.table('paths').select("id, title").execute()
        lessons = supabase.table('lessons').select("id, lesson_title").execute()
        
        lesson_ids = [{'id': row['id'], 'title': row.get('lesson_title', str(row['id']))} for row in lessons.data]
        path_ids = [{'id': row['id'], 'title': row.get('title', str(row['id']))} for row in paths.data]
        
        if request.method == 'POST':
            question_text = request.POST.get('questionText')
            correct_option = int(request.POST.get('correctOption'))
            question_type = request.POST.get('languagePair')
            title_text = request.POST.get('titleText')

            # Collect options
            options = []
            option_index = 0
            while True:
                opt = request.POST.get(f'option_{option_index}')
                if opt is None:
                    break
                options.append(wrap_preeti_in_sentence(opt))
                option_index += 1

            # Apply text formatting based on type
            if question_type == 'english_nepali':
                question_text = re.sub(r"<(.*?)>", r'<font="Preeti font  SDF">\1</font>', question_text)
            elif question_type == 'nepali':
                question_text = f'<font="Preeti font  SDF">{question_text}</font>'

            # Update quiz data
            quiz_data = {
                "data": {
                    "questionText": question_text,
                    "options": options,
                    "correctOption": correct_option,
                },
                "title": title_text
            }

            supabase.table("quiz_levels").update(quiz_data).eq("id", quiz_id).execute()
            return redirect('list_quiz_questions')

        context = {
            'quiz': quiz,
            'path_ids': path_ids,
            'lesson_ids': lesson_ids,
            'is_edit': True
        }
        return render(request, 'quiz.html', context)
        
    except Exception as e:
        return render(request, 'quiz.html', {'error': f'Quiz not found: {str(e)}'})

def edit_fill_blank(request, fill_blank_id):
    """Edit fill blank question"""
    try:
        # Fetch existing fill blank
        fill_blank_response = supabase.table("fill_blanks_level").select("*").eq("id", fill_blank_id).single().execute()
        fill_blank = fill_blank_response.data
        
        # Get paths and lessons for dropdowns
        paths = supabase.table('paths').select("id, title").execute()
        lessons = supabase.table('lessons').select("id, lesson_title").execute()
        
        lesson_ids = [{'id': row['id'], 'title': row.get('lesson_title', str(row['id']))} for row in lessons.data]
        path_ids = [{'id': row['id'], 'title': row.get('title', str(row['id']))} for row in paths.data]
        
        if request.method == 'POST':
            question_text = request.POST.get('questionText')
            correct_option = request.POST.get('correctOption')
            image_file = request.FILES.get('image')

            options = []
            option_index = 0
            while True:
                opt = request.POST.get(f'option_{option_index}')
                if opt is None:
                    break
                options.append(opt)
                option_index += 1

            letter_title = request.POST.get('letterTitle')
            topics = [request.POST.get('topic_0')]
            meaning = request.POST.get('letterMeaning')
            if meaning:
                meaning = re.sub(r"<(.*?)>", r'<font="Preeti font  SDF">\1</font>', meaning)

            # Handle image upload
            image_url = fill_blank.get('imageUrl')  # Keep existing image if no new one
            if image_file:
                file_name = f"images/{image_file.name}"
                try:
                    supabase.storage.from_("images").upload(file_name, image_file.read())
                    image_url = f"/storage/v1/object/public/images/{file_name}"
                except Exception as e:
                    return render(request, 'fill_blank.html', {'error': f'Upload failed: {str(e)}'})

            # Update fill blank data
            fill_blank_data = {
                "data": {
                    "questionText": question_text,
                    "options": options,
                    "correctOption": int(correct_option),
                },
                "letter_info": {
                    "title": letter_title,
                    "topics": topics,
                    "meaning": meaning,
                },
                "imageUrl": image_url,
                "title": question_text
            }

            supabase.table("fill_blanks_level").update(fill_blank_data).eq("id", fill_blank_id).execute()
            return redirect('list_fill_blanks')

        context = {
            'fill_blank': fill_blank,
            'path_ids': path_ids,
            'lesson_ids': lesson_ids,
            'is_edit': True
        }
        return render(request, 'fill_blank.html', context)
        
    except Exception as e:
        return render(request, 'fill_blank.html', {'error': f'Fill blank not found: {str(e)}'})

def edit_word_form(request, word_form_id):
    """Edit word form level"""
    try:
        # Fetch existing word form
        word_form_response = supabase.table("word_form_levels").select("*").eq("id", word_form_id).single().execute()
        word_form = word_form_response.data
        
        # Get paths and lessons for dropdowns
        paths = supabase.table('paths').select("id, title").execute()
        lessons = supabase.table('lessons').select("id, lesson_title").execute()
        
        lesson_ids = [{'id': row['id'], 'title': row.get('lesson_title', str(row['id']))} for row in lessons.data]
        path_ids = [{'id': row['id'], 'title': row.get('title', str(row['id']))} for row in paths.data]
        
        if request.method == 'POST':
            audio_file = request.FILES.get('audioFile')
            image_file = request.FILES.get('imageFile')
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

            # Collect options
            options = []
            option_index = 0
            while True:
                opt = request.POST.get(f'option_{option_index}')
                if opt is None:
                    break
                options.append(opt)
                option_index += 1

            # Handle audio upload
            audio_url = word_form.get('audioUrl')  # Keep existing audio if no new one
            if audio_file:
                file_name = f"word-form-audio/{audio_file.name}"
                try:
                    supabase.storage.from_("word-form-audio").upload(file_name, audio_file.read())
                    audio_url = f"/storage/v1/object/public/word-form-audio/{file_name}"
                except Exception as e:
                    return render(request, 'word_form.html', {'error': f'Upload failed: {str(e)}'})
                
            image_url = word_form.get('imageUrl')  # Keep existing image if no new one
            if image_file:
                file_name = f"images/{image_file.name}"
                try:
                    supabase.storage.from_("images").upload(file_name, image_file.read())
                    image_url = f"/storage/v1/object/public/images/{file_name}"
                except Exception as e:
                    return render(request, 'word_form.html', {'error': f'Upload failed: {str(e)}'})

            # Update word form data
            word_data = {
                "audioUrl": audio_url,
                "answer": answer,
                "options": options,
                "sound": nepali_sound
            }

            supabase.table("word_form_levels").update(word_data).eq("id", word_form_id).execute()
            return redirect('list_word_form_levels')

        context = {
            'word_form': word_form,
            'path_ids': path_ids,
            'lesson_ids': lesson_ids,
            'is_edit': True
        }
        return render(request, 'word_form.html', context)
        
    except Exception as e:
        return render(request, 'word_form.html', {'error': f'Word form not found: {str(e)}'})

def edit_match_following(request, match_id):
    """Edit match the following exercise"""
    try:
        # Fetch existing match exercise
        match_response = supabase.table("match_the_following_level").select("*").eq("id", match_id).single().execute()
        match_exercise = match_response.data
        
        # Get paths and lessons for dropdowns
        paths = supabase.table('paths').select("id, title").execute()
        lessons = supabase.table('lessons').select("id, lesson_title").execute()
        
        lesson_ids = [{'id': row['id'], 'title': row.get('lesson_title', str(row['id']))} for row in lessons.data]
        path_ids = [{'id': row['id'], 'title': row.get('title', str(row['id']))} for row in paths.data]
        
        if request.method == 'POST':
            # Collect all the pairs
            match_pairs = []
            pair_index = 0
            word_type = request.POST.get('language_type')
            
            while True:
                nepali_key = f'nepali_{pair_index}'
                japanese_key = f'japanese_{pair_index}'
                
                nepali_value = request.POST.get(nepali_key)
                japanese_value = request.POST.get(japanese_key)
                
                if not nepali_value and not japanese_value:
                    break
                    
                if nepali_value and japanese_value:
                    if word_type == 'nepali_word':
                        nepali_value = f'<font face="Preeti font  SDF">{nepali_value.strip()}</font>'

                    pair_dict = {
                        "nepali": nepali_value,
                        "japanese": japanese_value.strip()
                    }
                    match_pairs.append(pair_dict)
                
                pair_index += 1
            
            # Update match data
            match_data = {
                "data": match_pairs,
                "title": request.POST.get('titleText')
            }
            
            supabase.table("match_the_following_level").update(match_data).eq("id", match_id).execute()
            return redirect('list_match_following')

        context = {
            'match_exercise': match_exercise,
            'path_ids': path_ids,
            'lesson_ids': lesson_ids,
            'is_edit': True
        }
        return render(request, 'match_the_following.html', context)
        
    except Exception as e:
        return render(request, 'match_the_following.html', {'error': f'Match exercise not found: {str(e)}'})

def edit_letter(request, letter_id):
    """Edit letter"""
    try:
        # Fetch existing letter
        letter_response = supabase.table("letters").select("*").eq("id", letter_id).single().execute()
        letter = letter_response.data
        
        # Get paths and lessons for dropdowns
        paths = supabase.table('paths').select("id, title").execute()
        lessons = supabase.table('lessons').select("id, lesson_title").execute()
        
        lesson_ids = [{'id': row['id'], 'title': row.get('lesson_title', str(row['id']))} for row in lessons.data]
        path_ids = [{'id': row['id'], 'title': row.get('title', str(row['id']))} for row in paths.data]
        
        if request.method == 'POST':
            english_letter = request.POST.get('letter_name')
            nepali_letter = request.POST.get('nepali_letter')
            japanese_letter = request.POST.get('japanese_letter')
            letter_collection = request.POST.get('japanese_character_type')
            audio_file = request.FILES.get('audio')

            onyomi = request.POST.get('onyomi')
            kunyomi = request.POST.get('kunyomi')

            if nepali_letter:
                nepali_letter = f'<font="Preeti font  SDF">{nepali_letter}</font>'

            # Handle audio upload
            audio_url = letter.get('audio')  # Keep existing audio if no new one
            if audio_file:
                file_name = f"audio/{audio_file.name}"
                try:
                    supabase.storage.from_("letter-audio").upload(file_name, audio_file.read())
                    audio_url = f"/storage/v1/object/public/letter-audio/{file_name}"
                except Exception as e:
                    return render(request, 'letters_tracing.html', {'error': f'Upload failed: {str(e)}'})

            # Update letter data
            data = {
                'collection_id': letter_collection,
                'letter_name': english_letter,
                'nepali_text': nepali_letter,
                'japanese_text': japanese_letter,
                'letter_info': {'onyomi': onyomi, 'kunyomi': kunyomi},
                'audio': audio_url,
            }

            supabase.table('letters').update(data).eq("id", letter_id).execute()
            return redirect('list_letters')

        context = {
            'letter': letter,
            'path_ids': path_ids,
            'lesson_ids': lesson_ids,
            'is_edit': True
        }
        return render(request, 'letters_tracing.html', context)
        
    except Exception as e:
        return render(request, 'letters_tracing.html', {'error': f'Letter not found: {str(e)}'})
    


def edit_word_game(request, word_game_id):
    try:
        # Fetch existing word game
        print(f'word_game_id:{word_game_id}')
        word_game_response = supabase.table("word_game_level").select("*").eq("id", word_game_id).single().execute()
        
        # Check if word game exists
        if not word_game_response.data:
            return render(request, 'word_game.html', {
                'error': 'Word game not found.',
                'path_ids': [],
                'lesson_ids': [],
                'is_edit': False
            })
            
        word_game = word_game_response.data
        print(f'word game data: {word_game}')

        # Get paths and lessons for dropdowns
        paths = supabase.table('paths').select("id, title").execute()
        lessons = supabase.table('lessons').select("id, lesson_title").execute()

        lesson_ids = [{'id': row['id'], 'title': row.get('lesson_title', str(row['id']))} for row in lessons.data]
        path_ids = [{'id': row['id'], 'title': row.get('title', str(row['id']))} for row in paths.data]

        if request.method == 'POST':
            title = request.POST.get('title')
            
            # Collect options (filter out empty ones)
            options = []
            for i in range(5):
                opt = request.POST.get(f'option_{i}')
                if opt and opt.strip():
                    options.append(opt.strip())
                    
            # Collect valid words (filter out empty ones)
            valid_words = []
            idx = 0
            while True:
                word = request.POST.get(f'valid_{idx}')
                if word is None:
                    break
                if word.strip():
                    valid_words.append(word.strip())
                idx += 1

            # Validation
            if not title or len(options) < 3 or len(valid_words) < 2:
                return render(request, 'word_game.html', {
                    'error': 'Title, at least 3 options, and at least 2 valid words are required.',
                    'word_game': word_game,
                    'path_ids': path_ids,
                    'lesson_ids': lesson_ids,
                    'is_edit': True
                })

            update_data = {
                'title': title,
                'options': options,
                'valid_words': valid_words
            }
            
            supabase.table("word_game_level").update(update_data).eq("id", word_game_id).execute()
            return redirect('list_word_games')

        context = {
            'word_game': word_game,
            'path_ids': path_ids,
            'lesson_ids': lesson_ids,
            'is_edit': True
        }
        return render(request, 'word_game.html', context)
        
    except Exception as e:
        # Get paths and lessons for error case too
        try:
            paths = supabase.table('paths').select("id, title").execute()
            lessons = supabase.table('lessons').select("id, lesson_title").execute()
            lesson_ids = [{'id': row['id'], 'title': row.get('lesson_title', str(row['id']))} for row in lessons.data]
            path_ids = [{'id': row['id'], 'title': row.get('title', str(row['id']))} for row in paths.data]
        except:
            lesson_ids = []
            path_ids = []
            
        return render(request, 'word_game.html', {
            'error': f'Word game not found: {str(e)}',
            'path_ids': path_ids,
            'lesson_ids': lesson_ids,
            'is_edit': False
        })
    


def create_combined_words(request):
    paths = supabase.table('paths').select("id, title").execute()
    lessons = supabase.table('lessons').select("id, lesson_title").execute()
    
    lesson_ids = []
    for row in lessons.data:
        title = row.get('lesson_title', str(row['id']))
        lesson_ids.append({'id': row['id'], 'title': title})

    path_ids = []
    for row in paths.data:
        title = row.get('title', str(row['id']))
        path_ids.append({'id': row['id'], 'title': title})

    if request.method == 'POST':
        # Basic info
        title = request.POST.get('title')
        letter_info_title = request.POST.get('letter_info_title')
        letter_info_meaning = request.POST.get('letter_info_meaning')
        letter_info_meaning = re.sub(r"<(.*?)>", r'<font="Preeti font  SDF">\1</font>', letter_info_meaning)
        
        # Collect individual letters/words dynamically
        nepali_letters = []
        japanese_letters = []
        letter_index = 0
        
        while True:
            nepali_letter = request.POST.get(f'nepali_letter_{letter_index}')
            japanese_letter = request.POST.get(f'japanese_letter_{letter_index}')
            
            if nepali_letter is None or japanese_letter is None:
                break
                
            if nepali_letter.strip() and japanese_letter.strip():
                nepali_letters.append(nepali_letter.strip())
                japanese_letters.append(japanese_letter.strip())
            
            letter_index += 1
        
        # Get combined words
        combined_nepali_words = request.POST.get('combined_nepali_words')
        combined_japanese_words = request.POST.get('combined_japanese_words')
        
        # Meaning data
        romaji = request.POST.get('romaji')
        english = request.POST.get('english')
        japanese_meaning = request.POST.get('japanese_meaning')
        
        # Image upload
        image_file = request.FILES.get('image')
        
        # Use cases
        use_cases = []
        usecase_count = 0
        while True:
            use_case = request.POST.get(f'use_case_{usecase_count}')
            if use_case is None:
                break
            if use_case.strip():
                # Wrap text inside < > with Preeti font
                formatted = re.sub(r"<(.*?)>", r'<font="Preeti font  SDF">\1</font>', use_case.strip())
                use_cases.append(formatted)
            usecase_count += 1

        path_id = request.POST.get('path_id')
        lesson_id = request.POST.get('lesson_id')

        # Validation
        if not all([letter_info_title, letter_info_meaning, combined_nepali_words, 
                   combined_japanese_words, romaji, english, japanese_meaning]) or \
           len(nepali_letters) < 2 or len(japanese_letters) < 2:
            return render(request, 'combined_words.html', {
                'error': 'All required fields must be filled and at least 2 letters are required.',
                'path_ids': path_ids,
                'lesson_ids': lesson_ids
            })

        # Handle image upload
        image_url = None
        if image_file:
            file_name = f"images/{image_file.name}"
            try:
                res = supabase.storage.from_("images").upload(file_name, image_file.read())
                image_url = f"/storage/v1/object/public/images/{file_name}"
            except Exception as e:
                return render(request, 'combined_words.html', {
                    'error': f'Image upload failed: {str(e)}',
                    'path_ids': path_ids,
                    'lesson_ids': lesson_ids
                })

        # Format Nepali text with Preeti font
        formatted_nepali_letters = [f'(<font="Preeti font  SDF">{letter}</font>)' for letter in nepali_letters]
        formatted_combined_nepali = f'(<font="Preeti font  SDF">{combined_nepali_words}</font>)'

        # Create combined words structure
        combined_words_structure = {
            "nepaliLetters": formatted_nepali_letters,
            "japaneseLetters": japanese_letters,
            "combinedNepaliWords": formatted_combined_nepali,
            "combinedJapaneseWords": combined_japanese_words
        }

        # Create data structure
        combined_words_data = [{
            "letter_info": {
                "title": letter_info_title,
                "meaning": letter_info_meaning,
                "combinedWords": combined_words_structure
            },
            "use_cases": use_cases,
            "image_url": image_url,
            "title": letter_info_title,
            "meaning": {
                "romaji": romaji,
                "english": english,
                "japanese": japanese_meaning
            }
        }]

        print("Combined Words Data:", combined_words_data)
        
        try:
            result = supabase.table("combined_words_level").insert(combined_words_data).execute()
            ServiceLesson(result, 11, lesson_id)
            return render(request, 'combined_words.html', {
                'success': 'Combined words exercise created successfully!',
                'path_ids': path_ids,
                'lesson_ids': lesson_ids
            })
        except Exception as e:
            return render(request, 'combined_words.html', {
                'error': f'Error creating exercise: {str(e)}',
                'path_ids': path_ids,
                'lesson_ids': lesson_ids
            })

    return render(request, 'combined_words.html', {'path_ids': path_ids, 'lesson_ids': lesson_ids})

def list_combined_words(request):
    """
    View to display all combined words exercises from the database.
    """
    try:
        response = supabase.table("combined_words_level").select("*").order("created_at", desc=True).execute()
        combined_words = response.data
        total_count = len(combined_words)
        
        context = {
            'combined_words': combined_words,
            'total_count': total_count
        }
    except Exception as e:
        context = {
            'combined_words': [],
            'error': f'Error fetching data: {str(e)}',
            'total_count': 0
        }
    return render(request, 'combined_word_list.html', context)

def edit_combined_words(request, combined_words_id):
    """Edit combined words exercise"""
    try:
        # Fetch existing combined words
        combined_words_response = supabase.table("combined_words_level").select("*").eq("id", combined_words_id).single().execute()
        combined_words = combined_words_response.data
        
        # Get paths and lessons for dropdowns
        paths = supabase.table('paths').select("id, title").execute()
        lessons = supabase.table('lessons').select("id, lesson_title").execute()
        
        lesson_ids = [{'id': row['id'], 'title': row.get('lesson_title', str(row['id']))} for row in lessons.data]
        path_ids = [{'id': row['id'], 'title': row.get('title', str(row['id']))} for row in paths.data]
        
        if request.method == 'POST':
            # Get all form data
            title = request.POST.get('title')
            letter_info_title = request.POST.get('letter_info_title')
            letter_info_meaning = request.POST.get('letter_info_meaning')
            
            # Collect individual letters/words dynamically
            nepali_letters = []
            japanese_letters = []
            letter_index = 0
            
            while True:
                nepali_letter = request.POST.get(f'nepali_letter_{letter_index}')
                japanese_letter = request.POST.get(f'japanese_letter_{letter_index}')
                
                if nepali_letter is None or japanese_letter is None:
                    break
                    
                if nepali_letter.strip() and japanese_letter.strip():
                    nepali_letters.append(nepali_letter.strip())
                    japanese_letters.append(japanese_letter.strip())
                
                letter_index += 1
            
            combined_nepali_words = request.POST.get('combined_nepali_words')
            combined_japanese_words = request.POST.get('combined_japanese_words')
            
            romaji = request.POST.get('romaji')
            english = request.POST.get('english')
            japanese_meaning = request.POST.get('japanese_meaning')
            
            image_file = request.FILES.get('image')
            
            # Collect use cases
            use_cases = []
            usecase_count = 0
            while True:
                use_case = request.POST.get(f'use_case_{usecase_count}')
                if use_case is None:
                    break
                if use_case.strip():
                    use_cases.append(use_case.strip())
                usecase_count += 1

            # Handle image upload (keep existing if no new image)
            image_url = combined_words.get('image_url')
            if image_file:
                file_name = f"images/{image_file.name}"
                try:
                    supabase.storage.from_("images").upload(file_name, image_file.read())
                    image_url = f"/storage/v1/object/public/images/{file_name}"
                except Exception as e:
                    return render(request, 'combined_words.html', {
                        'error': f'Image upload failed: {str(e)}',
                        'combined_words': combined_words,
                        'path_ids': path_ids,
                        'lesson_ids': lesson_ids,
                        'is_edit': True
                    })

            # Format Nepali text
            formatted_nepali_letters = [f'(<font="Preeti font  SDF">{letter}</font>)' for letter in nepali_letters]
            formatted_combined_nepali = f'(<font="Preeti font  SDF">{combined_nepali_words}</font>)'

            # Update data structure
            update_data = {
                "letter_info": {
                    "title": letter_info_title,
                    "meaning": letter_info_meaning,
                    "combinedWords": {
                        "nepaliLetters": formatted_nepali_letters,
                        "japaneseLetters": japanese_letters,
                        "combinedNepaliWords": formatted_combined_nepali,
                        "combinedJapaneseWords": combined_japanese_words
                    }
                },
                "use_cases": use_cases,
                "image_url": image_url,
                "title": title,
                "meaning": {
                    "romaji": romaji,
                    "english": english,
                    "japanese": japanese_meaning
                }
            }

            supabase.table("combined_words_level").update(update_data).eq("id", combined_words_id).execute()
            return redirect('list_combined_words')

        context = {
            'combined_words': combined_words,
            'path_ids': path_ids,
            'lesson_ids': lesson_ids,
            'is_edit': True
        }
        return render(request, 'combined_words.html', context)
        
    except Exception as e:
        return render(request, 'combined_words.html', {'error': f'Combined words not found: {str(e)}'})


def create_sentence_level(request):
    paths = supabase.table('paths').select("id, title").execute()
    lessons = supabase.table('lessons').select("id, lesson_title").execute()
    
    lesson_ids = []
    for row in lessons.data:
        title = row.get('lesson_title', str(row['id']))
        lesson_ids.append({'id': row['id'], 'title': title})

    path_ids = []
    for row in paths.data:
        title = row.get('title', str(row['id']))
        path_ids.append({'id': row['id'], 'title': title})

    if request.method == 'POST':
        title = request.POST.get('title')
        grammar_point = request.POST.get('grammar_point')
        example_for = request.POST.get('example_for')
        form = request.POST.get('form_0')
        # forms = []
        # option_count = 0
        # while True:
        #     option = request.POST.get(f'form_{option_count}')
        #     if option is None:
        #         break
        #     forms.append(option)
        #     option_count += 1
        sentence_japanese = request.POST.get('sentence_japanese')
        sentence_romaji = request.POST.get('sentence_romaji')
        sentence_english = request.POST.get('sentence_english')
        sentence_nepali = request.POST.get('sentence_nepali')
        image_text = request.POST.get('image_text')
        image_file = request.FILES.get('image_file')
        audio_file = request.FILES.get('audio_file')
        path_id = request.POST.get('path_id')
        lesson_id = request.POST.get('lesson_id')

        image_url = None
        if image_file:
            file_name = f"images/{image_file.name}"
            try:
                supabase.storage.from_("images").upload(file_name, image_file.read())
                image_url = f"/storage/v1/object/public/images/{file_name}"
            except Exception as e:
                return render(request, 'sentence_level.html', {
                    'error': f'Image upload failed: {str(e)}',
                    'path_ids': path_ids,
                    'lesson_ids': lesson_ids
                })

        audio_url = None
        if audio_file:
            file_name = f"audio/{audio_file.name}"
            try:
                supabase.storage.from_("audio").upload(file_name, audio_file.read())
                audio_url = f"/storage/v1/object/public/audio/{file_name}"
            except Exception as e:
                return render(request, 'sentence_level.html', {
                    'error': f'Audio upload failed: {str(e)}',
                    'path_ids': path_ids,
                    'lesson_ids': lesson_ids
                })

        # Prepare data for insertion
        sentence_data = [{
            "data": {
                "title": title,
                "forms": form,
                "grammar_point": grammar_point,
                "example_for": example_for,
                "sentence_japanese": sentence_japanese,
                "sentence_romaji": sentence_romaji,
                "sentence_english": sentence_english,
                "sentence_nepali": sentence_nepali,
                "image_text": image_text
            },
            "image_url": image_url,
            "audio_url": audio_url
        }]
        print(sentence_data)

        # Insert into Supabase
        try:
            result = supabase.table("sentence_level").insert(sentence_data).execute()
            # # Optionally, add to lesson's data array
            #ServiceLesson(result, 12, lesson_id)
            return render(request, 'sentence_level.html', {
                'success': 'Sentence created successfully.',
                'path_ids': path_ids,
                'lesson_ids': lesson_ids
            })
        except Exception as e:
            return render(request, 'sentence_level.html', {
                'error': f'Failed to save sentence: {str(e)}',
                'path_ids': path_ids,
                'lesson_ids': lesson_ids
            })

    return render(request, 'sentence_level.html', {'path_ids': path_ids, 'lesson_ids': lesson_ids})