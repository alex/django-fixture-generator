from django.contrib.auth.models import User

from fixture_generator import fixture_generator
from fixture_generator.tests.models import Author, Entry


@fixture_generator(Author)
def test_1():
    Author.objects.create(name="Tom Clancy")
    Author.objects.create(name="Daniel Pinkwater")

@fixture_generator(User)
def test_2():
    pass

@fixture_generator(Entry)
def test_3():
    Entry.objects.create(public=True)
    Entry.objects.create(public=False)