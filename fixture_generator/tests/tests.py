import sys
from StringIO import StringIO

from django.core.management import call_command
from django.test import TestCase

from fixture_generator import fixture_generator
from fixture_generator.management.commands.generate_fixture import linearize_requirements


@fixture_generator()
def test_func_1():
    pass

@fixture_generator(requires=["tests.test_func_3", "tests.test_func_4"])
def test_func_2():
    pass

@fixture_generator(requires=["tests.test_func_5"])
def test_func_3():
    pass

@fixture_generator(requires=["tests.test_func_5"])
def test_func_4():
    pass

@fixture_generator()
def test_func_5():
    pass

class LinearizeRequirementsTests(TestCase):
    def setUp(self):
        self.available_fixtures = {}
        fixtures = [
            "test_func_1", "test_func_2", "test_func_3", "test_func_4",
            "test_func_5"
        ]
        for fixture in fixtures:
            self.available_fixtures[("tests", fixture)] = globals()[fixture]
    
    def test_basic(self):
        requirements, models = linearize_requirements(self.available_fixtures, test_func_1)
        self.assertEqual(requirements, [test_func_1])
        self.assertEqual(models, set())
    
    def test_diamond(self):
        requirements, models = linearize_requirements(self.available_fixtures, test_func_2)
        self.assertEqual(
            requirements,
            [test_func_5, test_func_3, test_func_4, test_func_2]
        )

class ManagementCommandTests(TestCase):
    def test_basic(self):
        sys.stdout = StringIO()
        stuff = call_command("generate_fixture", "tests.test_1")
        output = sys.stdout.getvalue().strip()
        sys.stdout = sys.__stdout__
        
        self.assertEqual(output, """[{"pk": 1, "model": "tests.author", "fields": {"name": "Tom Clancy"}}, {"pk": 2, "model": "tests.author", "fields": {"name": "Daniel Pinkwater"}}]""")
