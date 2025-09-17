
from django.urls import path
from . import views

urlpatterns = [
   path('', views.feed_page, name='index'),
   path('post/', views.post, name='post'),

]