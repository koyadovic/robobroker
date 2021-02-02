import os
from subprocess import Popen, PIPE
from typing import List


class TextFileError(Exception):
    pass


def _new_proc(args):
    return Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)


def _check_return_code(rc, err, code_validator=lambda rc: rc == 0):
    if not code_validator(rc):
        raise TextFileError(f'Return code {rc}', err.decode('utf8'))


def find(filename: str, regex: str) -> List[str]:
    # regex could be '^1,'
    proc = _new_proc(['grep', '-E', regex, filename])
    output, err = proc.communicate()
    parsed = output.decode('utf8').strip()
    _check_return_code(proc.returncode, err, code_validator=lambda rc: rc in [0, 1])
    if parsed == '':
        return []
    return parsed.split('\n')


def string_replace(filename: str, regex: str, new: str, replace_all=False):
    """
    NOTE: Be careful, this operation overwrite the file
    """
    regex_param = f's/{regex}/{new}/'
    if replace_all:
        regex_param += 'g'
    proc = _new_proc(['sed', '-i', '-e', regex_param, filename])
    output, err = proc.communicate()
    _check_return_code(proc.returncode, err)


def lines(filename: str):
    proc = _new_proc(['wc', '-l', filename])
    output, err = proc.communicate()
    _check_return_code(proc.returncode, err)
    parsed = output.decode('utf8').strip()
    return int(parsed.split(' ')[0])


def last_n_lines(filename, n):
    proc = _new_proc(['tail', '-n', str(n), filename])
    output, err = proc.communicate()
    _check_return_code(proc.returncode, err)
    parsed = output.decode('utf8').strip()
    return parsed.split('\n')


def get_files_that_contains_string(directory, string, recursive=False):
    files = []
    directory_contents = os.listdir(directory)
    for f_name in directory_contents:
        absolute_path = directory + os.sep + f_name
        if os.path.isfile(absolute_path):
            try:
                with open(absolute_path, 'r') as f:
                    if string in f.read():
                        files.append(absolute_path)
            except UnicodeDecodeError:
                pass
        elif recursive and os.path.isdir(absolute_path):
            files += get_files_that_contains_string(absolute_path, string, recursive=recursive)
    return files
