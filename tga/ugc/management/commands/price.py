prices = {
    "лыжи": {
        "week_price": 100,
        "month_price": 300
    },
    "сноуборд": {
        "week_price": 100,
        "month_price": 300
    },
    "велосипед": {
        "week_price": 150,
        "month_price": 400
    },
    "колеса": {
        "week_price": 100,
        "month_price": 400
    },
    "square_meters": {
        "first_price": 599,
        "next_price": 150
    }

}

def get_think_price(seasonal_item, period_extension, period, amount):
    if period_extension == "нед.":
        period_extension = "week_price"
    else:
        period_extension = "month_price"

    return prices[seasonal_item][period_extension] * int(period) * int(amount)


def get_meter_price(period, square_meters):
    first_price = prices["square_meters"]["first_price"]
    next_price = prices["square_meters"]["next_price"]
    if square_meters == 1:
        return first_price * period
    else:
        return (first_price + next_price * (int(square_meters) - 1)) * int(period)
