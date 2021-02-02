_text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})


def is_bytes_binary(b: bytes):
    return bool(b.translate(None, _text_chars))


def is_file_binary(file_path: str):
    contents = open(file_path, 'rb').read(1024)
    return is_bytes_binary(contents)
