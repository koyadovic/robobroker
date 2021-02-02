def profit_difference_percentage(origin, destination):
    return ((destination - origin) / origin) * 100


def to_profit(prices):
    profit = []
    last = None
    for price in prices:
        if last is None:
            profit.append(0)
        else:
            profit.append(profit_difference_percentage(last, price))
        last = price
    return profit


def mean(values):
    return sum(values) / len(values)

