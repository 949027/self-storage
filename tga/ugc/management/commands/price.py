from ugc.models import Warehouses, SeasonalItems, Customers, SeasonalItemsPrice, AnotherItemsPrice


def get_think_price(seasonal_item, period_extension, period, amount):
    item = SeasonalItems.objects.filter(item_name__contains=seasonal_item)
    if period_extension == "нед.":
        week_price = SeasonalItemsPrice.objects.get(item_name=item[0]).week_price
        return week_price * int(period) * int(amount)
    else:
        month_price = SeasonalItemsPrice.objects.get(item_name=item[0]).month_price
        return month_price * int(period) * int(amount)


def get_meter_price(period, square_meters):
    prices = AnotherItemsPrice.objects.all()[0]
    first_price = prices.first_price
    next_price = prices.next_price
    if square_meters == 1:
        return first_price * period
    else:
        return (first_price + next_price * (int(square_meters) - 1)) * int(period)


def get_think_button_prices(seasonal_item, period_extension, period, amount):
    buttons = []
    for button in range(1, period+1):
        price = get_think_price(seasonal_item, period_extension, button, amount)
        buttons.append(f"{button} {period_extension} {int(price)} p.")
    return buttons


def get_another_button_prices(period, square_meters):
    buttons = []
    for button in range(1, period+1):
        price = get_meter_price(button, square_meters)
        buttons.append(f"{button} мес. {int(price)} p.")
    return buttons
