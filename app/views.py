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
            lesson_name = ['Conversations','Alphabets', 'Vocabs', 'Grammar', 'Kanji']
            lesson_type = [1, 2, 4, 8, 16]
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
        image_file = request.FILES.get('image')
        lesson_type = request.POST.getlist('lessonCategory')

        lesson_type = sum(int(val) for val in lesson_type)

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
        lesson_data = [{
        'lesson_title': lesson_title,
        'lesson_description': lesson_description,
        'data': levels,
        'lesson_type': lesson_type,
        'image_url': image_url
            }]
    # Insert as JSONB (not as a string)
        supabase.table("lessons").insert(lesson_data).execute()
        
        print('Lesson JSON:', lesson_data)

        return redirect('create_lesson')  # Redirect after POST

    return render(request, 'lesson_form.html')

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
        if not image_file or not options:
            return render(request, 'word_form.html', {'error': 'All fields are required.'})

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
                "title": question_text
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
        nepali_sound = request.POST.get('sound')
        path_id = request.POST.get('path_id')
        lesson_id = request.POST.get('lesson_id')

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
        audio_url = f"/storage/v1/object/public/audio/{file_name}"


        # 3. Insert into DB
        word_data = [{
            "audioUrl": audio_url,
            "answer": answer,
            "options": options,
            "sound": nepali_sound
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
        options = [
            request.POST.get('option_0'),
            request.POST.get('option_1'),
            request.POST.get('option_2'),
            request.POST.get('option_3'),
            request.POST.get('option_4'),
        ]

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

        onyomi = request.POST.get('onyomi')
        kunyomi = request.POST.get('kunyomi')

        path_id = request.POST.get('path_id')
        lesson_id = request.POST.get('lesson_id')

        if nepali_letter:
            nepali_letter = f'<font="Preeti font  SDF">{nepali_letter}</font>'

         # 1. Upload audio file to Supabase Storage
        audio_url = None
        if audio_file:
            file_name = f"audio/{audio_file.name}"  # folder 'audio/' inside bucket
            try:
                res = supabase.storage.from_("audio").upload(file_name, audio_file.read())
            except Exception as e:
                return render(request, 'word_form.html', {'error': f'Upload failed: {str(e)}'})

            # 2. Build public URL (no signed URL needed)
            audio_url = f"/storage/v1/object/public/audio/{file_name}"

        data = [{
            'collection_id': letter_collection,
            'letter_name': english_letter,
            'nepali_text': nepali_letter,
            'japanese_text': japanese_letter,
            'letter_info': {'onyomi': onyomi, 'kunyomi': kunyomi},
            'audio': audio_url,
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
        Onyomi = request.POST.get('topic_0')
        Kunyomi = request.POST.get('topic_1')
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
            "letter_info": {"title": title, "topics":[Onyomi, Kunyomi], "meaning": meaning},
            "use_cases": use_cases,
            "image_url": image_url
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
        title = request.POST.get('letterTitle')
        meaning = request.POST.get('letterMeaning')
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
                "title": title,
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
        examples = request.POST.getlist('examples')
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