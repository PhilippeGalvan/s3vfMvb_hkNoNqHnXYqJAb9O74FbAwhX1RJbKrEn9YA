import redis
import requests
import json
from senndertest.settings import (
    REDIS_HOST,
    REDIS_HASH_CACHE,
    REDIS_HASH_CACHE_KEY,
)


conn = redis.StrictRedis(REDIS_HOST)


def get_movies_with_id() -> dict:
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


def get_cached_movies_with_people(
    redis_conn: redis.StrictRedis = conn,
) -> dict:
    if redis_conn.exists(REDIS_HASH_CACHE):
        return json.loads(
            conn.hget(REDIS_HASH_CACHE, REDIS_HASH_CACHE_KEY).decode('utf-8')
        )
    else:
        return {}


def set_cache_movies_with_people(
    redis_conn: redis.StrictRedis = conn,
    cache_life_seconds: int = 60,
    payload: dict = {},
) -> bool:
    redis_conn.hset(
        REDIS_HASH_CACHE,
        REDIS_HASH_CACHE_KEY,
        json.dumps(payload)
    )
    redis_conn.expire(
        REDIS_HASH_CACHE,
        cache_life_seconds
    )
    return True if redis_conn.exists(REDIS_HASH_CACHE) else False


def get_movies_with_people(redis_conn: redis.StrictRedis = conn) -> dict:
    """
    Get all the movies with the characters associated with it.
    It returns the result as a dictionnary of characters indexed by film name
    if the API returns a valid result. Otherwise it returns an empty dict.
    """

    cached_data = get_cached_movies_with_people(redis_conn)
    if cached_data:
        return cached_data

    movies = {}
    movies_by_id = get_movies_with_id()

    if movies_by_id:
        response = requests.get(
            'https://ghibliapi.herokuapp.com/people'
        )
        people_w_movie = response.json()
        if response.status_code == 200:
            movies = {name: [] for id, name in movies_by_id.items()}
            for person in people_w_movie:
                # Sometime the API send back a wrong id without contextual
                # information and impossible to reach by id with the people API
                if all(key in person for key in ("films", "name")):
                    for movie in person['films']:
                        movie_id = movie.split('/')[-1]
                        movie_name = movies_by_id[movie_id]
                        if movie_name in movies:
                            movies[movie_name].append(person['name'])
                        else:
                            movies[movie_name] = [person['name']]

    set_cache_movies_with_people(redis_conn, payload=movies)
    return movies
