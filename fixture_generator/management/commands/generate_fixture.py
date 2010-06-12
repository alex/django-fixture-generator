import os
from optparse import make_option

from django.core.management import BaseCommand, call_command
from django.conf import settings
from django.db import router
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule


FIXTURE_DATABASE = "__fixture_gen__"

class CircularDependencyError(Exception):
    """
    Raised when there is a circular dependency in fixture requirements.
    """
    pass

def linearize_requirements(available_fixtures, fixture, seen=None):
    if seen is None:
        seen = set([fixture])
    models = set(fixture.models)
    requirements = []
    for requirement in fixture.requires:
        app_label, fixture_name = requirement.rsplit(".", 1)
        fixture_func = available_fixtures[(app_label, fixture_name)]
        if fixture_func in seen:
            raise CircularDependencyError
        r, m = linearize_requirements(
            available_fixtures,
            fixture_func,
            seen | set([fixture_func])
        )
        requirements.extend([req for req in r if req not in requirements])
        models.update(m)
    requirements.append(fixture)
    return requirements, models


class FixtureRouter(object):
    def __init__(self, models):
        self.models = models
    
    def db_for_read(self, *args, **kwargs):
        return FIXTURE_DATABASE
    
    def db_for_write(self, *args, **kwargs):
        return FIXTURE_DATABASE
    
    def allow_relation(self, *args, **kwargs):
        return True
    
    def allow_syncdb(self, db, model):
        if db == FIXTURE_DATABASE:
            return model in self.models


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("--format", default="json", dest="format",
            help="Specifies the output serialization format for fixtures."),
        make_option("--indent", default=None, dest="indent", type="int",
            help="Specifies the indent level to use when pretty-printing output"),
    )
    args = "app_label.fixture"
    
    def handle(self, fixture, **options):
        available_fixtures = {}
        for app in settings.INSTALLED_APPS:
            try:
                fixture_gen = import_module(".fixture_gen", app)
            except ImportError:
                if module_has_submodule(import_module(app), "fixture_gen"):
                   raise
                continue
            for obj in fixture_gen.__dict__.values():
                if getattr(obj, "__fixture_gen__", False):
                    available_fixtures[(app.rsplit(".", 1)[-1], obj.__name__)] = obj
        app_label, fixture_name = fixture.rsplit(".", 1)
        fixture = available_fixtures[(app_label, fixture_name)]
        
        requirements, models = linearize_requirements(available_fixtures, fixture)
        
        settings.DATABASES[FIXTURE_DATABASE] = {
            "ENGINE": "sqlite3",
            "NAME": "fixture_gen.db",
        }
        old_routers = router.routers
        router.routers = [FixtureRouter(models)]
        try:
            call_command("syncdb", db=FIXTURE_DATABASE)
            for fixture_func in requirements:
                fixture_func()
            call_command("dumpdata",
                *["%s.%s" % (m._meta.app_label, m._meta.object_name) for m in models],
                **dict(options, verbosity=0, db=FIXTURE_DATABASE)
            )
        finally:
            del settings.DATABASES["__fixture_gen__"]
            router.routers = old_routers
            os.remove("fixture_gen.db")
