import datetime

from django.db import models

n = datetime.datetime.now() - datetime.timedelta(days=2)
class User(models.Model):
    chat_id = models.CharField(max_length=32, verbose_name='ID чата телеграмма')
    name = models.CharField(max_length=128, blank=True, null=True, verbose_name='Имя пользователя')
    birthday = models.CharField(max_length=32, blank=True, null=True, verbose_name='Дата рождения')
    phone_number = models.CharField(max_length=16, blank=True, null=True, verbose_name='Номер телефона')
    cart = models.ManyToManyField('Cart', blank=True, verbose_name='Корзина')
    date = models.CharField(blank=True, max_length=64)
    bonus = models.IntegerField(default=0, verbose_name='Бонусы')
    orders = models.ManyToManyField('Orders', blank=True, verbose_name='Заказы')
    history = models.ManyToManyField('History', blank=True, verbose_name='История покупок')
    total_amount = models.IntegerField(default=0, verbose_name='Общая сумма покупок')
    is_seller = models.BooleanField(default=False, verbose_name='Является ли пользователь продавцом')
    can_use_lottery = models.BooleanField(default=False, verbose_name='Может ли использовать лоотерею?')
    last_lottery_time = models.DateTimeField(default=n, verbose_name='Последняя дата использования лотереи')


class History(models.Model):
    date = models.DateTimeField(auto_now_add=True, verbose_name='Дата покупки')
    amount = models.IntegerField(default=0, verbose_name='Сумма покупки')
    detail = models.TextField(default='История отсутствует т.к покупка совершалась в магазине', verbose_name='Инфопрмация о покупке')

class Orders(models.Model):
    products = models.ManyToManyField('Cart', blank=True, verbose_name='Товар')
    status = models.CharField(max_length=128, default='Собирается', verbose_name='Статус заказа')
    date = models.CharField(max_length=32, verbose_name='Дата и время, на которое сделан заказ')
class Cart(models.Model):
    product = models.ForeignKey('Product', blank=True, null=True, on_delete=models.CASCADE, verbose_name='Товар')
    stocks = models.ForeignKey('Stocks', blank=True, null=True, on_delete=models.CASCADE, verbose_name='Акция')
    count = models.FloatField(default=1, verbose_name='кол-во')

    def price(self):
        if self.product:
            unit = self.product.unit
            if unit == 'кг':
                return round(self.product.price * self.count/1000, 2)
            else:
                return self.count*self.product.price
        else:
            unit = self.stocks.unit
            if unit == 'кг':
                return round(self.stocks.price * self.count / 1000, 2)
            else:
                return self.count * self.stocks.price

class Category(models.Model):
    name = models.CharField(max_length=128, verbose_name='Название категории')

    def __str__(self):
        return self.name
class Stocks(models.Model):
    name = models.CharField(max_length=64, verbose_name='Название')
    text = models.TextField(verbose_name='Описание акции')
    price = models.IntegerField(default=0, verbose_name='Цена товара')
    unit = models.CharField(max_length=64, verbose_name='Еденица измерения товара (кг/шт)')
    image = models.ImageField(blank=True, verbose_name='Фотография')
    is_send_message = models.BooleanField(default=False, verbose_name='Нужно ли сделать рассылку пользователям?')
    need_add_to_cart = models.BooleanField(default=False, verbose_name='Нужно ли сразу кидать товар в корзину?')

class Lottery(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название приза')
    rare = models.IntegerField(default=1, verbose_name='Частота выпадения')


class Bonus(models.Model):
    bonus = models.IntegerField(default=1000, verbose_name='Приветственный бонус')
    birthday_bonus = models.IntegerField(default=1000, verbose_name='Бонус на день рождения')
class Product(models.Model):
    category = models.ForeignKey('Category', blank=True, null=True, on_delete=models.CASCADE, verbose_name='Категория')
    name = models.CharField(max_length=64, verbose_name='Название')
    price = models.IntegerField(default=0, verbose_name='Цена товара')
    unit = models.CharField(max_length=64, verbose_name='Еденица измерения товара (кг/шт)')
    image = models.ImageField(blank=True, verbose_name='Фотография')
    need_add_to_cart = models.BooleanField(default=False, verbose_name='Нужно ли сразу кидать товар в корзину?')


class Rank(models.Model):
    name = models.CharField(max_length=64, verbose_name='Название ранга')
    price = models.IntegerField(default=0, verbose_name='Сумма, до которой действителен ранг')
    sale = models.IntegerField(verbose_name='Скидка на этом ранге')

