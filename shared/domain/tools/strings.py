import unidecode


def strip_accents(accented_string):
    unaccented_string = unidecode.unidecode(accented_string)
    return unaccented_string
