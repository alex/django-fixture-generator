def fixture_generator(*models, **kwargs):
    requires = kwargs.pop("requires", [])
    if kwargs:
        raise TypeError("fixture_generator got an unexpected keyword argument:"
            " %r", iter(kwargs).next())
    def inner(func):
        func.models = models
        func.requires = requires
        func.__fixture_gen__ = True
        return func
    return inner
