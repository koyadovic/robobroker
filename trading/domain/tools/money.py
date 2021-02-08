import math


def two_decimals_floor(num):
    return '{:.2f}'.format(
        math.floor(num * 100.0) / 100.0
    )


def eight_decimals_floor(num):
    return '{:.2f}'.format(
        math.floor(num * 100000000.0) / 100000000.0
    )
