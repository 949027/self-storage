from django.db import models


class Warehouses(models.Model):
    name = models.CharField(
        max_length=256,
        verbose_name="Наименование склада",
    )
    address = models.TextField(
        verbose_name="Адрес склада",
    )
    lat = models.FloatField(verbose_name="Широта", blank=True, null=True)
    lon = models.FloatField(verbose_name="Долгота", blank=True, null=True)

    def __str__(self):
        return f"Склад {self.name}"

    class Meta:
        verbose_name = "Склад"
        verbose_name_plural = "Склады"


class Customers(models.Model):
    telegram_id = models.PositiveIntegerField(
        verbose_name="ID пользователя в телеграмме",
        unique=True,
    )
    phone_number = models.CharField(
        max_length=256,
        blank=True,
        default="",
        verbose_name="Номер телефона заказчика",
    )
    first_name = models.CharField(
        max_length=256,
        blank=True,
        default="",
        verbose_name="Имя заказчика",
    )
    last_name = models.CharField(
        max_length=256,
        blank=True,
        default="",
        verbose_name="Фамилия заказчика",
    )
    passport_id = models.CharField(
        max_length=12,
        verbose_name="Паспортные данные заказчика",
    )
    birthday = models.DateField(
        verbose_name="Дата рождения заказчика",
    )

    def __str__(self):
        return f"Заказчик {self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Заказчик"
        verbose_name_plural = "Заказчики"


# class StorageThingsTypes(models.Model):
#     TYPE_CHOICES = [
#         ("сезонные вещи", "сезонные вещи"),
#         ("другое", "другое"),
#     ]
#     thing_type = models.CharField(
#         max_length=256,
#         choices=TYPE_CHOICES,
#         verbose_name="Что хранить",
#     )
#
#     def __str__(self):
#         return self.thing_type
#
#     class Meta:
#         verbose_name = "Тип вещей для хранения"
#         verbose_name_plural = "Типы вещей для хранения"


class SeasonalItems(models.Model):
    SEASONAL_ITEMS_CHOICES = [
        ("лыжи", "лыжи"),
        ("сноуборд", "сноуборд"),
        ("велосипед", "велосипед"),
        ("колеса", "колеса"),
    ]
    item_name = models.CharField(
        max_length=256,
        choices=SEASONAL_ITEMS_CHOICES,
        verbose_name="Наименование вещи",
    )

    def __str__(self):
        return self.item_name

    class Meta:
        verbose_name = "Сезонная вещь"
        verbose_name_plural = "Сезонные вещи"


class SeasonalItemsPrice(models.Model):
    item_name = models.ForeignKey(
        to="ugc.SeasonalItems",
        verbose_name="Наименование вещи",
        on_delete=models.PROTECT,
    )
    week_price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Стоимость хранения в неделю",
    )
    month_price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Стоимость хранения в месяц",
    )

    def __str__(self):
        return "стоимость"

    class Meta:
        verbose_name = "Стоимость хранения сезонной вещи"
        verbose_name_plural = "Стоимость хранения сезонной вещи"


class AnotherItemsPrice(models.Model):
    first_price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Стоимость первого кв.м.",
    )
    next_price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Стоимость последующих кв.м.",
    )

    def __str__(self):
        return "стоимость"

    class Meta:
        verbose_name = "Стоимость хранения другого"
        verbose_name_plural = "Стоимость хранения другого"


class Orders(models.Model):
    TYPE_CHOICES = [
        ("сезонные вещи", "сезонные вещи"),
        ("другое", "другое"),
    ]
    customer = models.ForeignKey(
        to="ugc.Customers",
        verbose_name="Заказчик",
        on_delete=models.PROTECT,
    )
    warehouse = models.ForeignKey(
        to="ugc.Warehouses",
        verbose_name="Склад",
        on_delete=models.PROTECT,
    )
    seasonal_item = models.ForeignKey(
        to="ugc.SeasonalItems",
        blank=True,
        null=True,
        verbose_name="Сезонная вещь",
        on_delete=models.SET_NULL,
    )
    thing_type = models.CharField(
        max_length=256,
        choices=TYPE_CHOICES,
        verbose_name="Что хранить",
    )
    cell_size = models.PositiveIntegerField(
        # для Другое
        blank=True,
        null=True,
        verbose_name="Габаритность ячейки",
    )
    amount = models.PositiveIntegerField(
        # для Сезонные вещи
        blank=True,
        null=True,
        verbose_name="Количество вещей",
    )
    comment = models.TextField(
        verbose_name="Комментарий к заказу",
    )
    start_date = models.DateField(
        verbose_name="Дата бронирования с",
    )
    end_date = models.DateField(
        verbose_name="Дата бронирования по",
    )
    cost = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Стоимость заказа",
    )

    def __str__(self):
        return f"Заказ № {self.pk}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
