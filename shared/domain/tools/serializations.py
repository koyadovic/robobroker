import importlib


def serialize_function(function):
    return f'{function.__module__}.{function.__name__}'


def deserialize_function(serialized_function):
    parts = serialized_function.split('.')
    module = '.'.join(parts[0:-1])
    func_name = parts[-1]
    return getattr(importlib.import_module(module), func_name)
