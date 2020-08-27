import redis
import requests
import json
from typing import Dict

from django.conf import settings


conn = redis.StrictRedis(settings.REDIS_HOST)


def get_movies_with_id() -> Dict[str, str]:
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
) -> Dict[str, list]:
    """
    Get the dict of movies with people if it exists in the cache
    else returns an empty dict {}.
    """  # noqa
    cache = conn.hget(
        settings.REDIS_HASH_CACHE,
        settings.REDIS_HASH_CACHE_KEY
    )
    return json.loads(cache.decode('utf-8')) if cache else {}


def set_cache_movies_with_people(
    payload: Dict[str, list],
    redis_conn: redis.StrictRedis = conn,
) -> bool:
    """
    Set the dict of movies with people even if it already exists in the cache
    and returns True if the cache exists, False otherwise.
    """
    nb_keys_set = redis_conn.hset(
        settings.REDIS_HASH_CACHE,
        settings.REDIS_HASH_CACHE_KEY,
        json.dumps(payload)
    )
    redis_conn.expire(
        settings.REDIS_HASH_CACHE,
        settings.CACHE_LIFE_SECONDS,
    )
    return bool(nb_keys_set)


def get_movies_with_people(redis_conn: redis.StrictRedis = conn) -> Dict[str, list]:  # noqa
    """
    Get all the movies with the characters associated with it.
    It returns the result as a dictionnary of characters indexed by film name
    if the API returns a valid result. Otherwise it returns an empty dict.
    """
    cache_movie_lock = redis.lock.Lock(
        conn,
        'get_movie_lock',
        blocking_timeout=3
    )

    # Lock is not placed here to avoid unnecessary overhead
    # It isn't DRY, can be challenged !
    # We could remove this part and start at the lock
    # if we consider the operation as cheap
    cached_data = get_cached_movies_with_people(redis_conn)
    if cached_data:
        return cached_data

    # Start lock here because the lock is taken
    # only when cached_data is being retrieved from the distant API
    # See: https://en.wikipedia.org/wiki/Thundering_herd_problem
    with cache_movie_lock:
        # If the thread was locked then it needs to check if another client
        # successfully cached information otherwise it tries to retrieve it
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
                    # Sometime the API send back a wrong id without contextual  # noqa
                    # information and impossible to reach by id with the people API  # noqa
                    if all(key in person for key in ("films", "name")):
                        for movie in person['films']:
                            movie_id = movie.split('/')[-1]
                            movie_name = movies_by_id[movie_id]
                            if movie_name in movies:
                                movies[movie_name].append(person['name'])
                            else:
                                movies[movie_name] = [person['name']]

        set_cache_movies_with_people(payload=movies, redis_conn=redis_conn)
        # End lock
    return movies
