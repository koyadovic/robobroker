import os
import sys
import time


class CannotAcquireLock(Exception):
    pass


def is_locked(f_name):
    return os.path.exists(f_name + '.lock')


def _acquire(f_name, exit_if_locked=False, raise_exception_if_locked=False):
    while True:
        try:
            os.makedirs(f_name + '.lock/', exist_ok=False)
            break
        except OSError as e:
            if raise_exception_if_locked:
                raise CannotAcquireLock()
            if exit_if_locked:
                print(f'ERROR: {f_name} is locked. '
                      f'If you are sure that there is no code using it, you can remove. Exiting ... ')
                sys.exit(0)
            time.sleep(0.05)


def _release(f_name):
    try:
        os.rmdir(f_name + '.lock')
    except FileNotFoundError:
        pass


class acquire_single_access:
    def __init__(self, f_name, exit_if_locked=False, raise_exception_if_locked=False):
        self.f_name = f_name
        self.exit_if_locked = exit_if_locked
        self.raise_exception_if_locked = raise_exception_if_locked

    def __enter__(self):
        _acquire(self.f_name,
                 exit_if_locked=self.exit_if_locked,
                 raise_exception_if_locked=self.raise_exception_if_locked)

    def __exit__(self, exc_type, exc_val, exc_tb):
        _release(self.f_name)


class lock_open:
    def __init__(self, f_name, *args, **kwargs):
        self.f_name = f_name
        self.args = args
        self.kwargs = kwargs

    def __enter__(self):
        _acquire(self.f_name)
        self._file = open(self.f_name, *self.args, **self.kwargs)
        return self._file

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self._file.flush()
            self._file.close()
        finally:
            _release(self.f_name)
