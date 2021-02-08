from shared.domain.tools import filelocks
from shared.domain.tools.discovering import load_python_module_by_file_absolute_path
from shared.domain.tools.serializations import serialize_function
from shared.domain.tools.text_files import get_files_that_contains_string

from datetime import datetime

import threading
import atexit
import signal
import pytz
import os
import re
import sys
import time


_LAST_EXECUTION_STRING = ''

_ALL_EXECUTABLES = {}
_ADDED_EXECUTABLES = {}

_FILE_LOCK = '/tmp/.dia_periodic_tasks'


"""
.---------------- minute (0 - 59)
|  .------------- hour (0 - 23)
|  |  .---------- day of month (1 - 31)
|  |  |  .------- month (1 - 12)
|  |  |  |  .---- day of week (0 - 6) monday - sunday
|  |  |  |  |
*  *  *  *  * user-name  function
"""


def schedule(minute='*', hour='*', day='*', month='*', weekday='*', unique_name=None, priority=0):
    def decorator(func):
        string_regex = _to_complete_regex(minute, hour, day, month, weekday)
        if string_regex not in _ALL_EXECUTABLES:
            _ALL_EXECUTABLES[string_regex] = []
        if string_regex not in _ADDED_EXECUTABLES:
            _ADDED_EXECUTABLES[string_regex] = []

        func_serialized = serialize_function(func)
        func_serialized = '.'.join(func_serialized.split('.')[-2:])
        func.priority = priority

        if func_serialized not in _ADDED_EXECUTABLES[string_regex]:
            _ALL_EXECUTABLES[string_regex].append(func)
            _ADDED_EXECUTABLES[string_regex].append(func_serialized)
        _ALL_EXECUTABLES[string_regex].sort(key=lambda f: f.priority, reverse=True)

        def wrapper():
            return func()

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.unique_name = unique_name
        func.unique_name = unique_name
        return wrapper
    return decorator


def start_periodic_tasks_main_loop():
    _i('Starting ...')
    _autodiscover_scheduled_tasks()
    _main_loop()


def execute_minute_tick():
    """
    Call this function if want to manage minute tick call from outside. (Celery or whatever)
    """
    global _LAST_EXECUTION_STRING
    now = pytz.utc.localize(datetime.utcnow())
    string = _datetime_to_string_for_regex_test(now)
    if _LAST_EXECUTION_STRING != string:
        for string_regex, callbacks in _ALL_EXECUTABLES.items():
            if re.compile(string_regex).search(string) is not None:
                _i(f'Launching tasks')
                thread = threading.Thread(target=_execute_all_callbacks, args=[callbacks])
                thread.start()
        _LAST_EXECUTION_STRING = string


def _autodiscover_scheduled_tasks():
    self_directory = os.path.dirname(__file__)
    src_directory = os.path.dirname(os.path.dirname(self_directory))
    files_using_decorator = get_files_that_contains_string(src_directory, f'@{schedule.__name__}(', recursive=True)
    for abs_file in files_using_decorator:
        module = load_python_module_by_file_absolute_path(abs_file)
        _i(f'> Found scheduled tasks on {module.__file__}')


def _main_loop():
    global _LAST_EXECUTION_STRING
    with filelocks.acquire_single_access(_FILE_LOCK, exit_if_locked=True):
        original_sigint_handler = signal.getsignal(signal.SIGINT)
        original_sigterm_handler = signal.getsignal(signal.SIGTERM)

        main_thread = threading.main_thread().ident
        current_thread = threading.current_thread().ident

        if main_thread == current_thread:
            signal.signal(signal.SIGTERM, _signal_terminate)
            signal.signal(signal.SIGINT, _signal_terminate)

        atexit.register(_cleanup)
        _i(f'Started periodic tasks server.')
        try:
            while True:
                execute_minute_tick()
                time.sleep(1.0)
        finally:
            if main_thread == current_thread:
                signal.signal(signal.SIGTERM, original_sigterm_handler)
                signal.signal(signal.SIGINT, original_sigint_handler)


def _execute_all_callbacks(callbacks):
    _i(f'Executing each task')
    for callback in callbacks:
        try:
            name = callback.unique_name if hasattr(callback, 'unique_name') else callback.__name__
            with filelocks.acquire_single_access(f'/tmp/.dia_task_{name}', raise_exception_if_locked=True):
                _i(f'Executing {callback.__name__}.')
                callback()
        except filelocks.CannotAcquireLock:
            _i(f'WARN: ignoring execution of {callback.__name__}. Is currently executing')
            pass
    _i(f'Finished executing tasks')


def _datetime_to_string_for_regex_test(dt: datetime):
    return f'{dt.minute}:{dt.hour}:{dt.day}:{dt.month}:{dt.weekday()}'


def _to_complete_regex(m, h, dom, mon, dow):
    return f'^{_to_regex(m)}:{_to_regex(h)}:{_to_regex(dom)}:{_to_regex(mon)}:{_to_regex(dow)}$'


def _to_regex(n):
    if n == '*':
        return r'\d+'
    return str(n)


def _signal_terminate(signo, frame):
    _cleanup()


def _cleanup(*args):
    try:
        os.rmdir(_FILE_LOCK + '.lock/')
    except FileNotFoundError:
        pass
    sys.exit(0)


def _i(text):
    pass
    # print(f'{text}')


if _ADDED_EXECUTABLES == {}:
    _autodiscover_scheduled_tasks()
