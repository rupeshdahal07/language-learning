from django.urls import path
from .views import UserPathProgressView, UserLessonProgressView, UserLevelProgressView, UserRegistration, LearnDataView

urlpatterns = [
    # User Path Progress CRUD operations
    path('user-path-progress/', UserPathProgressView.as_view(), name='user-path-progress'),
    path('user-lesson-progress/', UserLessonProgressView.as_view(), name='user-lesson-progress'),
    path('user-level-progress/', UserLevelProgressView.as_view(), name='user-level-progress'),
    path('user-create/', UserRegistration.as_view(), name='user-create'),
    path('learn-data/', LearnDataView.as_view(), name='learn_data'),
    # Bulk operations for adding completed lessons
    #path('user-path-progress/add-lesson/', UserPathProgressBulkView.as_view(), name='user-path-progress-add-lesson'),
]