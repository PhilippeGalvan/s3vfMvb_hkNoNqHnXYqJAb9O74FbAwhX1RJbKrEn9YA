import httpretty
import json
from redis import StrictRedis

from django.conf import settings


films_uri = 'https://ghibliapi.herokuapp.com/films'
people_uri = 'https://ghibliapi.herokuapp.com/people'

film_body = json.dumps([
    {
        "id": "2baf70d1-42bb-4437-b551-e5fed5a87abe",
        "title": "Castle in the Sky",
        "description": "Description",
        "director": "Hayao Miyazaki",
        "producer": "Isao Takahata",
        "release_date": "1986",
        "rt_score": "95",
    },
    {
        "id": "12cfb892-aac0-4c5b-94af-521852e46d6a",
        "title": "Grave of the Fireflies",
        "description": "Description",
        "director": "Isao Takahata",
        "producer": "Toru Hara",
        "release_date": "1988",
        "rt_score": "97",
    },
    {
        "id": "12cfb892-aac0-4c5b-94af-521432e45c6b",
        "title": "Film without people",
        "description": "Description",
        "director": "John Doe",
        "producer": "Toru Hara",
        "release_date": "2020",
        "rt_score": "100",
    }
])

people_body = json.dumps([
    {
        "id": "ba924631-068e-4436-b6de-f3283fa848f0",
        "name": "Ashitaka",
        "gender": "male",
        "age": "late teens",
        "eye_color": "brown",
        "hair_color": "brown",
        "films": [
            "https://ghibliapi.herokuapp.com/films/2baf70d1-42bb-4437-b551-e5fed5a87abe",  # noqa
            "https://ghibliapi.herokuapp.com/films/12cfb892-aac0-4c5b-94af-521852e46d6a",  # noqa
        ],
        "species": "https://ghibliapi.herokuapp.com/species/af3910a6-429f-4c74-9ad5-dfe1c4aa04f2",  # noqa
        "url": "https://ghibliapi.herokuapp.com/people/ba924631-068e-4436-b6de-f3283fa848f0",  # noqa
    },
    {
        "id": "598f7048-74ff-41e0-92ef-87dc1ad980a9",
        "name": "Lusheeta Toel Ul Laputa",
        "gender": "Female",
        "age": "13",
        "eye_color": "Black",
        "hair_color": "Black",
        "films": [
        "https://ghibliapi.herokuapp.com/films/2baf70d1-42bb-4437-b551-e5fed5a87abe",  # noqa
        ],
        "species": "https://ghibliapi.herokuapp.com/species/af3910a6-429f-4c74-9ad5-dfe1c4aa04f2",  # noqa
        "url": "https://ghibliapi.herokuapp.com/people/598f7048-74ff-41e0-92ef-87dc1ad980a9"  # noqa
    },
    {
        "id": "030555b3-4c92-4fce-93fb-e70c3ae3df8b",
        "name": "Yakul",
        "age": "Unknown",
        "gender": "male",
        "eye_color": "Grey",
        "hair_color": "Brown",
        "films": [],
        "species": "https://ghibliapi.herokuapp.com/species/6bc92fdd-b0f4-4286-ad71-1f99fb4a0d1e",  # noqa
        "url": "https://ghibliapi.herokuapp.com/people/030555b3-4c92-4fce-93fb-e70c3ae3df8b"  # noqa
    }
])

cache_payloads_ok = [
    {
        'some_movie_to_cache': [
            'person1',
            'person2',
        ],
        'some_other_movie': [
            'person1'
        ],
        'some_characterless_movie': []
    },
    {},
    {
        'override_done': ['terminator']
    }
]


conn = StrictRedis(settings.REDIS_HOST)


def reset_cache(redis_conn: StrictRedis = conn):
    nb_keys_removed = redis_conn.hdel(
        settings.REDIS_HASH_CACHE,
        settings.REDIS_HASH_CACHE_KEY
    )
    return nb_keys_removed


def get_movie_cache_basic():
    return json.loads(conn.hget(
        settings.REDIS_HASH_CACHE,
        settings.REDIS_HASH_CACHE_KEY
    ).decode('utf-8'))


def set_movie_cache_basic(payload):
    nb_keys_set = conn.hset(
        settings.REDIS_HASH_CACHE,
        settings.REDIS_HASH_CACHE_KEY,
        payload,
    )
    return nb_keys_set


def mock_people_api(status=200, body=None, method=httpretty.GET):

    if not body:
        body = people_body if status == 200 else '{"message": "HTTPretty :)"}'

    httpretty.register_uri(
        method,
        people_uri,
        body=people_body,
        status=status,
    )


def mock_movies_api(status=200, body=None, method=httpretty.GET):

    if not body:
        body = film_body if status == 200 else '{"message": "HTTPretty :)"}'

    httpretty.register_uri(
        method,
        films_uri,
        body=film_body,
        status=status,
    )
