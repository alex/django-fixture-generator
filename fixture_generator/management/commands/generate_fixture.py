import os
from optparse import make_option

from django.core.management import BaseCommand, call_command
from django.conf import settings
from django.db import router, connections
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
    
    def db_for_read(self, model, instance=None, **hints):
        return FIXTURE_DATABASE
    
    def db_for_write(self, model, instance=None, **hints):
        return FIXTURE_DATABASE
    
    def allow_relation(self, *args, **kwargs):
        return True
    
    def allow_syncdb(self, db, model):
        return True


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("--format", default="json", dest="format",
            help="Specifies the output serialization format for fixtures."),
        make_option("--indent", default=None, dest="indent", type="int",
            help="Specifies the indent level to use when pretty-printing output"),
        make_option("--default", default=False, dest="default_settings", type="string", 
            help="Use default settings for generating test database"),
    )
    args = "app_label.fixture"
    
    def handle(self, fixture, **options):
        default_settings = options.get('default_settings', False)

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
       
        if not default_settings:
            settings.DATABASES[FIXTURE_DATABASE] = {
                "ENGINE": "sqlite3",
                "NAME": "fixture_gen.db",
            }
            old_routers = router.routers
            router.routers = [FixtureRouter(models)]
 
        # Creates tests databases for populating them with the fixtures
        elif default_settings:
            from django.test.simple import DjangoTestSuiteRunner
            self.test_runner = DjangoTestSuiteRunner(verbosity=0)
            self.old_config = self.test_runner.setup_databases()
            
        try:
            # migrate_all=True is for south, Django just absorbs it
            # create_test_db already executes syncdb 
            if not default_settings:
                call_command("syncdb", database=FIXTURE_DATABASE, verbosity=0,
                    interactive=False, migrate_all=True)
            for fixture_func in requirements:
                fixture_func()
            if not default_settings:
                call_command("dumpdata",
                    *["%s.%s" % (m._meta.app_label, m._meta.object_name) for m in models],
                    **dict(options, verbosity=0, database=FIXTURE_DATABASE)
                )
            else:
                for alias in connections._connections:
                    call_command("dumpdata",
                        *["%s.%s" % (m._meta.app_label, m._meta.object_name) for m in models],
                        **dict(options, verbosity=0, database=alias)
                    )
        except Exception, error:
            print error
        finally:
            if not default_settings:
                os.remove("fixture_gen.db")
                del settings.DATABASES[FIXTURE_DATABASE]
                del connections._connections[FIXTURE_DATABASE]
                router.routers = old_routers
            elif default_settings:
                self.test_runner.teardown_databases(self.old_config)

