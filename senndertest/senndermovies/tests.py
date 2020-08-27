import json
import httpretty
from redis import StrictRedis
from copy import deepcopy
from datetime import datetime
from time import sleep

from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings

from .processing import (
    get_movies_with_id,
    get_movies_with_people,
    get_cached_movies_with_people,
    set_cache_movies_with_people,
)

from .utils_tests import (
    reset_cache,
    mock_movies_api,
    mock_people_api,
    people_body,
    get_movie_cache_basic,
    set_movie_cache_basic,
    conn,
    cache_payloads_ok,
)


class TestFilmsById(TestCase):

    def tearDown(self):
        reset_cache()

    @httpretty.activate
    def test_returns_empty_dict_if_not_200(self):
        mock_movies_api(status=400)

        movies_with_id = get_movies_with_id()
        self.assertEqual(movies_with_id, {})

    @httpretty.activate
    def test_accurately_converts_source_api(self):
        expected_output = {
            "2baf70d1-42bb-4437-b551-e5fed5a87abe": "Castle in the Sky",  # noqa
            "12cfb892-aac0-4c5b-94af-521852e46d6a": "Grave of the Fireflies",
            "12cfb892-aac0-4c5b-94af-521432e45c6b": "Film without people",
        }
        mock_movies_api()

        movies_with_id = get_movies_with_id()
        self.assertEqual(movies_with_id, expected_output)


class TestFilmsWithPeople(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.default_expected_output = {
            "Castle in the Sky": [
                "Ashitaka",
                "Lusheeta Toel Ul Laputa",
            ],
            "Grave of the Fireflies": [
                "Ashitaka",
            ],
            "Film without people": [],
        }

    def tearDown(self):
        reset_cache()

    @httpretty.activate
    def test_returns_empty_dict_if_people_api_not_200(self):
        mock_movies_api()
        mock_people_api(status=400)

        movies_with_people = get_movies_with_people()
        self.assertEqual(movies_with_people, {})

    @httpretty.activate
    def test_accurately_converts_source_api(self):
        mock_movies_api()
        mock_people_api()

        movies_with_people = get_movies_with_people()
        self.assertIn("Film without people", self.default_expected_output)
        self.assertEqual(movies_with_people, self.default_expected_output)

    @httpretty.activate
    def test_wrong_id_in_api_response(self):
        """
            This test is for an edge case where the API returns
            a person without necessary infos (`name` and `films`)
        """
        mock_movies_api()
        wrong_people_body = deepcopy(json.loads(people_body))
        wrong_people_body += [
            {
                "id": "f6ddf408-07fd-469b-8949-e09eac430a70",
                "length": 0
            },
            {
                "id": "f6ddf408-07fd-469b-8949-e09eac430a71",
                "name": 'test_name'
            },
            {
                "id": "f6ddf408-07fd-469b-8949-e09eac430a72",
                "films": [
                    "https://ghibliapi.herokuapp.com/films/2baf70d1-42bb-4437-b551-e5fed5a87abe",  # noqa
                ]
            },
        ]

        mock_people_api(body=json.dumps(wrong_people_body))

        movies_with_people = get_movies_with_people()
        self.assertEqual(movies_with_people, self.default_expected_output)

    @httpretty.activate
    def test_cache_filled(self):
        mock_movies_api()
        mock_people_api()

        self.assertEqual(conn.exists(settings.REDIS_HASH_CACHE), 0)
        movies_with_people = get_movies_with_people()
        self.assertEqual(conn.exists(settings.REDIS_HASH_CACHE), 1)
        self.assertEqual(
            movies_with_people,
            json.loads(conn.hget(
                settings.REDIS_HASH_CACHE,
                settings.REDIS_HASH_CACHE_KEY
            ).decode('utf-8'))  # noqa
        )

    @httpretty.activate
    def test_cache_read(self):
        # I don't see how to check that I'm returning a cached version except
        # with logging or timing (which is more an hint than a proof)
        mock_movies_api()
        mock_people_api()

        start_time = datetime.now()
        get_movies_with_people()
        first_call = datetime.now()
        get_movies_with_people()
        second_call = datetime.now()
        self.assertGreater(
            first_call - start_time,
            5*(second_call - first_call)
        )


class TestSetMovieCache(TestCase):

    def setUp(self):
        self.conn = StrictRedis(settings.REDIS_HOST)

    def tearDown(self):
        reset_cache()

    def test_set_cache_full_and_empty_ok(self):
        i = 0
        for payload in cache_payloads_ok:
            self.assertEqual(
                conn.exists(settings.REDIS_HASH_CACHE),
                bool(i) * 1
            )
            set_cache_movies_with_people(payload, self.conn)
            self.assertEqual(
                conn.exists(settings.REDIS_HASH_CACHE),
                1
            )
            self.assertEqual(payload, get_movie_cache_basic())
            i += 1

    def test_set_cache_expire(self):
        test_cache_ttl = 1
        with self.settings(CACHE_LIFE_SECONDS=test_cache_ttl):
            self.assertEqual(settings.CACHE_LIFE_SECONDS, test_cache_ttl)
            set_cache_movies_with_people(cache_payloads_ok[0], self.conn)
            self.assertEqual(conn.exists(settings.REDIS_HASH_CACHE), 1)
            sleep(settings.CACHE_LIFE_SECONDS)
            self.assertEqual(conn.exists(settings.REDIS_HASH_CACHE), 0)

    # For a future evolution with a serializer like pickle that should fail.
    # In the current usecase, that should never happen because we create
    # payloads based on external json APIs only using strings and integers
    def test_set_cache_not_serializable_payload(self):
        from datetime import datetime
        payload = {
            'dict_with_datetime': [
                datetime.now(),
                datetime.now(),
            ]
        }
        self.assertEqual(conn.exists(settings.REDIS_HASH_CACHE), 0)
        with self.assertRaises(TypeError) as e:
            set_cache_movies_with_people(payload, self.conn)
        self.assertIn('not JSON serializable', str(e.exception))
        self.assertEqual(conn.exists(settings.REDIS_HASH_CACHE), 0)


class TestGetMovieCache(TestCase):

    def setUp(self):
        self.conn = StrictRedis(settings.REDIS_HOST)

    def tearDown(self):
        reset_cache()

    def test_get_cache_ok(self):
        for cache_payload in cache_payloads_ok:
            set_movie_cache_basic(json.dumps(cache_payload))
            self.assertEqual(conn.exists(settings.REDIS_HASH_CACHE), 1)
            cache_content = get_cached_movies_with_people()
            self.assertEqual(conn.exists(settings.REDIS_HASH_CACHE), 1)
            self.assertEqual(cache_content, cache_payload)

    def test_get_on_an_empty_cache(self):
        self.assertEqual(conn.exists(settings.REDIS_HASH_CACHE), 0)
        cache_content = get_cached_movies_with_people()
        self.assertEqual(cache_content, {})


class TestFilmListView(TestCase):

    def setUp(self):
        self.client = Client()

    def tearDown(self):
        reset_cache()

    @httpretty.activate
    def test_response_ok(self):
        mock_movies_api()
        mock_people_api()

        response = self.client.get(reverse('movie_list'))
        movies_with_people = get_movies_with_people()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(movies_with_people, response.context['movie_list'])
        self.assertTemplateUsed(
            response,
            'senndermovies/movies_nested_list.html'
        )
