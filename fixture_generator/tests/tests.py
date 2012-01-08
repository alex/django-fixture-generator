import sys
from StringIO import StringIO

import django
from django.core.management import call_command
from django.test import TestCase

from fixture_generator import fixture_generator
from fixture_generator.management.commands.generate_fixture import (
    linearize_requirements, CircularDependencyError)


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

@fixture_generator(requires=["tests.test_func_7"])
def test_func_6():
    pass

@fixture_generator(requires=["tests.test_func_6"])
def test_func_7():
    pass

class LinearizeRequirementsTests(TestCase):
    def setUp(self):
        self.available_fixtures = {}
        fixtures = [
            "test_func_1", "test_func_2", "test_func_3", "test_func_4",
            "test_func_5", "test_func_6", "test_func_7",
        ]
        for fixture in fixtures:
            self.available_fixtures[("tests", fixture)] = globals()[fixture]

    def linearize_requirements(self, test_func):
        return linearize_requirements(self.available_fixtures, test_func)

    def test_basic(self):
        requirements, models = self.linearize_requirements(test_func_1)
        self.assertEqual(requirements, [test_func_1])
        self.assertEqual(models, [])

    def test_diamond(self):
        requirements, models = self.linearize_requirements(test_func_2)
        self.assertEqual(
            requirements,
            [test_func_5, test_func_3, test_func_4, test_func_2]
        )

    def test_circular(self):
        self.assertRaises(CircularDependencyError,
            linearize_requirements, self.available_fixtures, test_func_6
        )


class ManagementCommandTests(TestCase):
    def generate_fixture(self, fixture, error=False, **kwargs):
        stdout = StringIO()
        stderr = StringIO()
        run = lambda: call_command("generate_fixture", fixture, stdout=stdout, stderr=stderr, **kwargs)

        if error:
            # CommandError gets turned into SystemExit
            self.assertRaises(SystemExit, run)
        else:
            run()
        return stdout.getvalue(), stderr.getvalue()

    def test_basic(self):
        output, _ = self.generate_fixture("tests.test_1")
        self.assertEqual(output, """[{"pk": 1, "model": "tests.author", "fields": {"name": "Tom Clancy"}}, {"pk": 2, "model": "tests.author", "fields": {"name": "Daniel Pinkwater"}}]""")

    def test_auth(self):
        # All that we're checking for is that it doesn't hang on this call,
        # which would happen if the auth post syncdb hook goes and prompts the
        # user to create an account.
        output, _ = self.generate_fixture("tests.test_2")
        self.assertEqual(output, "[]")

    def test_all(self):
        if django.VERSION < (1, 3):
            return
        output, _ = self.generate_fixture("tests.test_3", use_base_manager=True)
        self.assertEqual(output, """[{"pk": 1, "model": "tests.entry", "fields": {"public": true}}, {"pk": 2, "model": "tests.entry", "fields": {"public": false}}]""")

    def test_nonexistant(self):
        out, err = self.generate_fixture("tests.test_255", error=True)
        # Has a leading shell color thingy.
        self.assertTrue("Error: Fixture generator 'tests.test_255' not found" in err)
        self.assertFalse(out)

        out, err = self.generate_fixture("xxx.xxx", error=True)
        self.assertTrue("Error: Fixture generator 'xxx.xxx' not found" in err)
        self.assertFalse(out)
