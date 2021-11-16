from django.contrib import admin

from .models import Warehouses
from .models import Customers
from .models import SeasonalItems
from .models import SeasonalItemsPrice
from .models import AnotherItemsPrice
from .models import Orders


@admin.register(Warehouses)
class WarehousesAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "lat", "lon")
    list_edit = ("name", "address", "lat", "lon")


@admin.register(Customers)
class CustomersAdmin(admin.ModelAdmin):
    list_display = (
        "telegram_id",
        "phone_number",
        "first_name",
        "last_name",
        "passport_id",
        "birthday",
    )
    list_edit = (
        "telegram_id",
        "phone_number",
        "first_name",
        "last_name",
        "passport_id",
        "birthday",
    )


@admin.register(SeasonalItems)
class SeasonalItemsAdmin(admin.ModelAdmin):
    list_display = ("item_name",)
    list_edit = ("item_name",)


@admin.register(SeasonalItemsPrice)
class SeasonalItemsPriceAdmin(admin.ModelAdmin):
    list_display = (
        "item_name",
        "week_price",
        "month_price",
    )
    list_edit = (
        "item_name",
        "week_price",
        "month_price",
    )


@admin.register(AnotherItemsPrice)
class BerriesAdmin(admin.ModelAdmin):
    list_display = (
        "first_price",
        "next_price",
    )
    list_edit = (
        "first_price",
        "next_price",
    )


@admin.register(Orders)
class OrdersAdmin(admin.ModelAdmin):
    list_display = (
        "customer",
        "seasonal_item",
        "thing_type",
        "cell_size",
        "amount",
        "comment",
        "start_date",
        "end_date",
        "cost",
    )
    list_edit = (
        "thing_type",
        "cell_size",
        "amount",
        "comment",
        "start_date",
        "end_date",
        "cost",
    )
