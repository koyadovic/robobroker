import importlib
import os
import unittest
import shutil

from shared.domain.tools.discovering import get_all_subclasses


base_dir = os.path.dirname(os.path.abspath(__file__))


def _create_file(path, contents=None):
    contents = contents or ''
    with open(path, 'w') as f:
        f.write(contents)
        f.flush()


def _create_package(name):
    os.makedirs(os.path.join(base_dir, name), exist_ok=True)
    _create_file(os.path.join(os.path.join(base_dir, name), '__init__.py'))


def _remove_package(name):
    shutil.rmtree(os.path.join(base_dir, name))


def _get_empty_class(name):
    return f'''class {name}:\n    pass\n'''


def _get_subclass(super_package, super_name, name):
    return f'''from {super_package} import {super_name}\n\n\nclass {name}({super_name}):\n    pass\n'''


class TestDiscoveringTools(unittest.TestCase):
    def setUp(self) -> None:
        _create_package('test_package')

    def tearDown(self) -> None:
        _remove_package('test_package')

    def test_import_subclasses(self):
        _create_file(f'{base_dir}/test_package/base.py', _get_empty_class('A'))
        _create_file(f'{base_dir}/test_package/sub_a.py', _get_subclass('.base', 'A', 'SubA'))
        os.sync()
        # time.sleep(2)
        base_package = importlib.import_module('shared.domain.tools.test_package')
        superclass = getattr(importlib.import_module('shared.domain.tools.test_package.base'), 'A')
        self.assertEqual(len(get_all_subclasses(base_package, superclass)), 1)

    def test_import_subclasses_2(self):
        _create_package('test_package_2')
        _create_file(f'{base_dir}/test_package_2/base.py', _get_empty_class('A'))
        _create_file(f'{base_dir}/test_package_2/sub_a.py', _get_subclass('.base', 'A', 'SubA'))
        _create_file(f'{base_dir}/test_package_2/sub_a_2.py', _get_subclass('.base', 'A', 'SubA2'))
        os.sync()
        # time.sleep(2)
        base_package = importlib.import_module('shared.domain.tools.test_package_2')
        superclass = getattr(importlib.import_module('shared.domain.tools.test_package_2.base'), 'A')
        self.assertEqual(len(get_all_subclasses(base_package, superclass)), 2)
        _remove_package('test_package_2')


if __name__ == '__main__':
    unittest.main()
