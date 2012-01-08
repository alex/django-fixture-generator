from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=100)


class EntryManager(models.Manager):
    def get_query_set(self):
        return super(EntryManager, self).get_query_set().filter(public=True)

class Entry(models.Model):
    public = models.BooleanField()

    objects = EntryManager()