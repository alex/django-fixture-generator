``django-fixture-generator``
============================

Requires Django 1.2.

 * Add ``"fixture_generator"`` to your ``INSTALLED_APPS`` setting.
 * Create a ``fixture_gen.py`` file in one of your apps.  It should look
   something like:
   
    from fixture_generator import fixture_generator
    
    from django.contrib.auth.models import User, Groups
    
    @fixture_generator(User, requires=["my_app.test_groups"])
    def test_users():
        muggles, wizards = Group.objects.order_by("name")
        simon = User.objects.create(username="simon")
        adrian = User.objects.create(username="adrian")
        jacob = User.objects.create(username="jacob")
        
        simon.groups.add(wizards)
        adrian.groups.add(muggles)
        jacob.groups.add(muggles)
    
    
    @fixture_generator(Group)
    def test_groups():
        Group.objects.create(name="Muggles")
        Group.objects.create(name="Wizards")
 
 * Run ``manage.py generate_fixture my_app.test_users``.
 * Save the resulting fixture somewhere.
