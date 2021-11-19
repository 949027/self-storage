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
