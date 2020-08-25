from django.test import TestCase
from .processing import get_movies_with_id, get_movies_with_people
import httpretty
import json


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


class TestFilmsById(TestCase):

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
        httpretty.register_uri(
            httpretty.GET,
            films_uri,
            status=400,
        )

        movies_with_id = get_movies_with_id()
        self.assertEqual(movies_with_id, {})

    @httpretty.activate
    def test_accurately_converts_source_api(self):
        expected_output = {
            "2baf70d1-42bb-4437-b551-e5fed5a87abe": "Castle in the Sky",
            "12cfb892-aac0-4c5b-94af-521852e46d6a": "Grave of the Fireflies",
            "12cfb892-aac0-4c5b-94af-521432e45c6b": "Film without people",
        }
        httpretty.register_uri(
            httpretty.GET,
            films_uri,
            body=film_body,
        )

        movies_with_id = get_movies_with_id()
        self.assertEqual(movies_with_id, expected_output)


class TestFilmsWithPeople(TestCase):

    def test_returns_good_format_using_live_api(self):
        httpretty.register_uri(
            httpretty.GET,
            films_uri,
            body=film_body,
            status=200,
        )
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
        httpretty.register_uri(
            httpretty.GET,
            films_uri,
            body=film_body,
            status=200,
        )
        httpretty.register_uri(
            httpretty.GET,
            people_uri,
            status=400,
        )

        movies_with_people = get_movies_with_people()
        self.assertEqual(movies_with_people, {})

    @httpretty.activate
    def test_accurately_converts_source_api(self):
        expected_output = {
            "Castle in the Sky": [
                "Ashitaka",
                "Lusheeta Toel Ul Laputa",
            ],
            "Grave of the Fireflies": [
                "Ashitaka",
            ],
            "Film without people": [],
        }
        httpretty.register_uri(
            httpretty.GET,
            films_uri,
            body=film_body,
            status=200,
        )
        httpretty.register_uri(
            httpretty.GET,
            people_uri,
            body=people_body,
        )

        movies_with_people = get_movies_with_people()
        self.assertIn("Film without people", expected_output)
        self.assertEqual(movies_with_people, expected_output)


class TestFilmListView(TestCase):
    pass
