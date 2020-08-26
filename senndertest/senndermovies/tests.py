from django.test import TestCase, Client
from .processing import (
    get_movies_with_id,
    get_movies_with_people,
    cache
)
from copy import deepcopy
import httpretty
import json
from django.urls import reverse
from senndertest.settings import CACHE_MOVIE_LIST_DURATION
from time import sleep
from datetime import datetime


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
        "films":
        [
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


class TestFilmsById(TestCase):

    def tearDown(self):
        cache.clear()

    def test_returns_good_format_using_live_api(self):
        movies_with_id = get_movies_with_id()
        self.assertNotEqual(movies_with_id, {})
        self.assertIsInstance(movies_with_id, dict)
        for id, title in movies_with_id.items():
            # It should be valid Bearer token id
            self.assertRegex(id, r'[\d|a-f]{8}-([\d|a-f]{4}-){3}[\d|a-f]{12}')
            self.assertIsInstance(title, str)

    @httpretty.activate
    def test_returns_empty_dict_if_not_200(self):
        mock_movies_api(status=400)

        movies_with_id = get_movies_with_id()
        self.assertEqual(movies_with_id, {})

    @httpretty.activate
    def test_accurately_converts_source_api(self):
        expected_output = {
            "2baf70d1-42bb-4437-b551-e5fed5a87abe": "Castle in the Sky",
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
        cache.clear()

    def test_returns_good_format_using_live_api(self):
        mock_movies_api()

        movies_with_people = get_movies_with_people()
        self.assertNotEqual(movies_with_people, {})
        self.assertIsInstance(movies_with_people, dict)
        for title, people in movies_with_people.items():
            self.assertIsInstance(title, str)
            self.assertIsInstance(people, list)
            for person in people:
                self.assertIsInstance(person, str)

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
            },            {
                "id": "f6ddf408-07fd-469b-8949-e09eac430a72",
                "films": [
                    "https://ghibliapi.herokuapp.com/films/2baf70d1-42bb-4437-b551-e5fed5a87abe",  # noqa
                ]
            },
        ]

        mock_people_api(body=json.dumps(wrong_people_body))

        movies_with_people = get_movies_with_people()
        self.assertEqual(movies_with_people, self.default_expected_output)

    def test_cache_ok(self):
        mock_movies_api()
        mock_people_api()

        start_time = datetime.now()
        response_to_be_cached = get_movies_with_people()
        first_call = datetime.now()
        get_movies_with_people()
        second_call = datetime.now()
        self.assertGreater(
            (first_call - start_time),
            (second_call - first_call) * 100
        )
        self.assertEqual(cache.currsize, 1)
        self.assertIn(response_to_be_cached, list(cache.items())[0])
        if CACHE_MOVIE_LIST_DURATION > 2:
            self.assertFalse(True, 'Please check if TESTING is set to True')
            sleep(CACHE_MOVIE_LIST_DURATION)
            self.assertEqual(cache.currsize, 0)


class TestFilmListView(TestCase):

    def setUp(self):
        self.client = Client()

    def tearDown(self):
        cache.clear()

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
        # All elements to be displayed are in the response !
        for movie, people_list in movies_with_people.items():
            self.assertContains(response, movie)
            for person in people_list:
                self.assertContains(response, person)
