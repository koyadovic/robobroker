def property_cached(fn):
    """
    Use:
    @property_cached
    def mi_expense_property(self):
        ... a lot of processing ...

    it only will be calculated once.
    """
    attr_name = "_cached_" + fn.__name__

    @property
    def _property_cached(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)

    return _property_cached
