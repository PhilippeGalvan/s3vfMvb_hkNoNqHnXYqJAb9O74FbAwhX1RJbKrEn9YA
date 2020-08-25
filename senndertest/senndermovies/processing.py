import requests

def get_movies_with_id():
    """
    Get all the movies from the ghibli API.
    It returns a dictionnary containing all films name indexed by id
    if the API returns a valid result. Otherwise it returns an empty dict.
    """

    response = requests.get(
        'https://ghibliapi.herokuapp.com/films'
    )
    raw_movies = response.json() if response.status_code == 200 else []
    return {movie['id']: movie['title'] for movie in raw_movies}


def get_movies_with_people():
    """
    Get all the movies with the characters associated with it.
    It returns the result as a dictionnary of characters indexed by film name
    if the API returns a valid result. Otherwise it returns an empty dict.
    """

    movies_by_id = get_movies_with_id()
    movies = {}
    if movies_by_id:
        response = requests.get(
            'https://ghibliapi.herokuapp.com/people'
        )
        people_w_movie = response.json() if response.status_code == 200 else []
        for person in people_w_movie:
            for movie in person['films']:
                movie_id = movie.split('/')[-1]
                movie_name = movies_by_id[movie_id]
                if movie_name in movies:
                    movies[movie_name].append(person['name'])
                else:
                    movies[movie_name] = [person['name']]
    return movies

