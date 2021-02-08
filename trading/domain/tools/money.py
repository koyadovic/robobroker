import math


def two_decimals_floor(num):
    return '{:.2f}'.format(
        math.floor(num * 100.0) / 100.0
    )
