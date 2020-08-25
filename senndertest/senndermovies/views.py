from django.shortcuts import render
from .processing import get_movies_with_people


def movie_list(request):
    """Renders all movies with the corresponding characters as a plain list"""
    context = {
        'movie_list': get_movies_with_people()
    }
    return render(request, 'senndermovies/movies_nested_list.html', context)
