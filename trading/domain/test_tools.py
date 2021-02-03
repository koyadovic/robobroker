import random
from datetime import datetime


def generate_currency_data(phases):
    now = datetime.utcnow()

    generated_prices = []

    all_deltas = []
    for phase in phases:
        td = phase.get('timedelta')
        all_deltas.append(td)

    start_dt = now
    for td in all_deltas:
        start_dt -= td
    for phase in phases:
        td = phase.get('timedelta')
        start_price = phase.get('start_price')
        end_price = phase.get('end_price')

        five_minutes_iterations = int(((start_dt + td) - start_dt).total_seconds() / 300)
        current_iteration = 0
        for _ in range(five_minutes_iterations):
            current_price = (((end_price - start_price) / five_minutes_iterations) * current_iteration) + start_price

            noise = current_price * 0.005
            rand_a = int((current_price - noise) * 100)
            rand_b = int((current_price + noise) * 100)
            final_price = random.randint(rand_a, rand_b) / 100
            generated_prices.append(final_price)
            current_iteration += 1
        # TODO hay que generar desde start_dt a start_dt + td precios fluctuantes desde start_price a end_price

    return generated_prices
