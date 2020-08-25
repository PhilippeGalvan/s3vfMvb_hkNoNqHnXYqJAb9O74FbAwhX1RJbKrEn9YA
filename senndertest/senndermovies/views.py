from django.shortcuts import render
from .processing import get_movies_with_people


def movie_list(request):
    context = {
        'movie_list': get_movies_with_people()
    }
    return render(request, 'senndermovies/movies_nested_list.html', context)
