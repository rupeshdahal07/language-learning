
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('path/create/', views.create_path, name='create_path'),
    path('paths/list', views.list_paths, name='list_paths'),

    path('create-quiz/', views.create_quiz, name='quiz'),
    # path('create-quiz-mix/', views.create_quize_mix, name='quiz_mix'),
    path('quiz/list/', views.list_quiz_questions, name='list_quiz_questions'),

    path('fill-in-the-blanks/', views.create_fill_blank, name="fill_blank" ),
    path('fill-blank/list/', views.list_fill_blanks, name='list_fill_blanks'),

    path('create-word-from-level/', views.create_word_from_level, name='create_word_from_level'),
    path('word-form/list/', views.list_word_form_levels, name='list_word_form'),

    path('user-from/', views.create_user, name='create_user'),
    path('users/', views.users, name='users'),
    path('users/list/', views.list_users, name='list_users'),

    path('create-lesson/', views.create_lesson, name='create_lesson'),
    path('create-lesson/list/', views.list_lessons, name='lesson_list'),
    path('delete_lesson/', views.delete_lesson, name='delete_lesson'),
    path('lessons/<int:lesson_id>/edit/', views.edit_lesson, name='edit_lesson'),
    path('get_lesson/<int:id>/', views.get_lesson, name='get_lesson'),

    path('get-level-ids/', views.get_level_ids, name='get_level_ids'),

    path('match-the-following/create/', views.create_match_following, name='match_the_following' ),
    path('match-the-following/list/', views.list_match_following, name='match_the_following_list' ),

    path('word-game/create/', views.create_word_game, name='create_word_game'),

    path('letters/create/', views.create_letters, name='create_letter'),
    path('letters/list/', views.list_letters, name='list_letters'),

    path('information-level/', views.information_level, name='information_level'),
    path('information-level2/', views.information_level2, name='information_level2'),

    path('meaning-level/create', views.create_meaning_level, name='create_meaning_level'),

    path('edit-quiz/<int:quiz_id>/', views.edit_quiz, name='edit_quiz'),
    path('edit-fill-blank/<int:fill_blank_id>/', views.edit_fill_blank, name='edit_fill_blank'),
    path('edit-word-form/<int:word_form_id>/', views.edit_word_form, name='edit_word_form'),
    path('edit-match-following/<int:match_id>/', views.edit_match_following, name='edit_match_following'),
    path('edit-letter/<int:letter_id>/', views.edit_letter, name='edit_letter'),


    path('create-rearrange/', views.create_rearrange, name='create_rearrange'),

]
