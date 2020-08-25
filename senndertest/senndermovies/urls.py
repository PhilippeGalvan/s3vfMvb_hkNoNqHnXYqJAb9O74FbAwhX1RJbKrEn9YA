from django.urls import path, include
from .views import movie_list


urlpatterns = [
    path('', movie_list, name='movie_list'),
]
