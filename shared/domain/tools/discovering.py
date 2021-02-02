import inspect
import os
import pkgutil
from importlib.util import spec_from_file_location, module_from_spec


def get_all_packages(from_package):
    all_packages = []
    for importer, modname, ispkg in pkgutil.walk_packages(
            path=from_package.__path__, onerror=lambda x: None, prefix=from_package.__name__ + '.'):
        if ispkg:
            all_packages.append(importer.find_module(modname).load_module(modname))
    return all_packages


def get_all_modules(from_package):
    all_modules = []
    for importer, modname, ispkg in pkgutil.walk_packages(
            path=from_package.__path__, onerror=lambda x: None, prefix=from_package.__name__ + '.'):
        if not ispkg:
            mod = importer.find_module(modname)
            if mod is not None:
                all_modules.append(mod.load_module(modname))
    return all_modules


def _cls_to_string(cls):
    return f'{cls.__module__}.{cls.__name__}'


def get_all_subclasses(from_package, cls):
    subclasses = set()
    for mod in get_all_modules(from_package):
        for name, obj in inspect.getmembers(mod):
            if not inspect.isclass(obj):
                continue
            if _cls_to_string(obj) == _cls_to_string(cls):
                continue
            if _cls_to_string(cls) in [_cls_to_string(c) for c in obj.mro()]:
                subclasses.add(obj)
    return list(subclasses)


def get_class_annotations(cls):
    annotations = None
    for i in inspect.getmembers(cls):
        if i[0] == '__annotations__':
            annotations = i[1]
            break
    if annotations is None:
        raise Exception('EEEK')
    return annotations


def load_python_module_by_file_absolute_path(abs_file):
    module_name = os.path.basename(abs_file).replace('.py', '')
    spec = spec_from_file_location(module_name, abs_file)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
