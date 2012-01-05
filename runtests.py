#!/usr/bin/env python
import sys

from os.path import dirname, abspath

from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES = {
            "default": {
                 "ENGINE": "django.db.backends.sqlite3",
                 "NAME": ":memory:",
            },
        },
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "fixture_generator",
            "fixture_generator.tests",
        ]
    )

from django.core.management import call_command


def runtests(*test_args):
    if not test_args:
        test_args = ["tests"]
    parent = dirname(abspath(__file__))
    sys.path.insert(0, parent)
    call_command("test", *test_args)


if __name__ == '__main__':
    runtests(*sys.argv[1:])

