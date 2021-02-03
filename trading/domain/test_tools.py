import random
from datetime import datetime, timedelta

from trading.domain.entities import CryptocurrencyPrice


def generate_currency_prices(phases, symbol=None, now=None):
    now = now or datetime.utcnow()

    generated_prices = []

    all_deltas = []
    for phase in phases:
        td = phase.get('timedelta')
        all_deltas.append(td)

    current_dt = now
    for td in all_deltas:
        current_dt -= td
    for phase in phases:
        td = phase.get('timedelta')
        start_price = phase.get('start_price')
        end_price = phase.get('end_price')

        five_minutes_iterations = int(((current_dt + td) - current_dt).total_seconds() / 300)
        current_iteration = 0
        for _ in range(five_minutes_iterations):
            current_price = (((end_price - start_price) / five_minutes_iterations) * current_iteration) + start_price

            noise = current_price * 0.005
            rand_a = int((current_price - noise) * 100)
            rand_b = int((current_price + noise) * 100)
            final_price = random.randint(rand_a, rand_b) / 100
            currency_price = CryptocurrencyPrice(
                symbol=symbol,
                instant=current_dt,
                sell_price=final_price,
                buy_price=final_price
            )
            generated_prices.append(currency_price)
            current_iteration += 1
            current_dt += timedelta(seconds=300)

    return generated_prices
