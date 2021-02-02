import magic


def get_file_name(absolute_file_path):
    return absolute_file_path.split('/')[-1]


def get_mimetype(absolute_file_path):
    return magic.from_file(absolute_file_path, mime=True)
