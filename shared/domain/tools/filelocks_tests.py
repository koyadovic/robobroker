import os
import unittest

from shared.domain.tools.filelocks import acquire_single_access, lock_open


class TestFileLocks(unittest.TestCase):
    def test_acquire_single_access(self):
        with acquire_single_access('testfile.txt'):
            self.assertTrue(os.path.exists('testfile.txt.lock'))

    def test_lock_open(self):
        with lock_open('testfile.txt', 'w') as f:
            self.assertTrue(os.path.exists('testfile.txt.lock'))
            f.write('test')
        with open('testfile.txt') as f:
            var = f.read()
            self.assertEqual(var, 'test')
        os.remove('testfile.txt')


if __name__ == '__main__':
    unittest.main()
