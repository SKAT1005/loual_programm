import os

import django
from telebot import types

from const import bot

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loual_programm.settings')
django.setup()
from app.models import Product, Stocks, Category, Orders


def go_to_menu():
    markup = types.InlineKeyboardMarkup()
    menu = types.InlineKeyboardButton(text='Главное меню', callback_data='menu')
    markup.add(menu)
    return markup

def go_to_order():
    markup = types.InlineKeyboardMarkup()

def catalog(page, type='products', category=None):
    markup = types.InlineKeyboardMarkup()
    menu = types.InlineKeyboardButton(text='Главное меню', callback_data='menu')
    markup.add(menu)
    start = 5 * (int(page) - 1)
    end = 5 * int(page)
    if type == 'stock':
        products = Stocks.objects.all()
        n = 'stock_detail'
    else:
        type = f'products|{category}'
        n = f'product|{category}'
        products = Product.objects.all()
    for product in products[start:end]:
        ticket_button = types.InlineKeyboardButton(text=f'{product.name} {product.price}/{product.unit}', callback_data=f'{n}|{product.id}|{page}')
        markup.add(ticket_button)
    if start > 0:
        last = types.InlineKeyboardButton(text='<<<', callback_data=f'{type}|{int(page) - 1}')
        markup.add(last)
    if end < len(products):
        next = types.InlineKeyboardButton(text='>>>', callback_data=f'{type}|{int(page) + 1}')
        markup.add(next)
    return markup



def menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    history = types.InlineKeyboardButton(text='История покупок', callback_data='history')
    catalog = types.InlineKeyboardButton(text='Каталог', callback_data='categorys')
    orders = types.InlineKeyboardButton(text='Список заказов', callback_data='orders')
    cart = types.InlineKeyboardButton(text='Моя корзина', callback_data='cart')
    lottery = types.InlineKeyboardButton(text='Лотерея', callback_data='lottery')
    stock = types.InlineKeyboardButton(text='Акции', callback_data='stock|1')
    manager = types.InlineKeyboardButton(text='Чат с менеджером', url='https://t.me/marigeraa')
    inst = types.InlineKeyboardButton(text='Наш инстаграм', url='https://www.instagram.com/volosy.mari/')
    markup.add(catalog, cart, stock, lottery, history, manager, inst)
    return markup

def categorys():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for cat in Category.objects.all():
        n = types.InlineKeyboardButton(text=cat.name, callback_data=f'products|{cat.id}|1')
        markup.add(n)
    return markup
def cart(user):
    markup = types.InlineKeyboardMarkup(row_width=1)
    total_amount = 0
    menu = types.InlineKeyboardButton(text='Главное меню', callback_data='menu')
    markup.add(menu)
    if user.cart.all():
        # buy = types.InlineKeyboardButton(text='Оплатить корзину', callback_data='buy')
        # markup.add(buy)
        for i in user.cart.all():
            total_amount += i.price()
            prod = types.InlineKeyboardButton(text=f"{i.product.name} {i.price()} рублей", callback_data=f'dell|{i.id}')
            markup.add(prod)
    return markup


def stock(product):
    markup = types.InlineKeyboardMarkup(row_width=1)
    ticket_button = types.InlineKeyboardButton(text=f'{product.name} {product.price}/{product.unit}', callback_data=f'stock_detail|{product.id}|1')
    markup.add(ticket_button)
    return markup

def buy(total_amount, sale):
    n = (100-sale)/100
    markup = types.InlineKeyboardMarkup(row_width=1)
    price = types.LabeledPrice(label=f'Оплата корзины', amount=int(total_amount*n) * 100)
    url = bot.create_invoice_link(title=f'Оплата корзины', description='Оплата корзины', currency='rub',
                                prices=[price], provider_token='1744374395:TEST:29e1d9bdf65ab963a2f4',
                                payload='test-invoice-payload')
    pay = types.InlineKeyboardButton('Оплатить', url=url)
    menu = types.InlineKeyboardButton(text='Главное меню', callback_data='menu')
    markup.add(pay, menu)
    return markup


def collet(chat_id, order_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    view_user = types.InlineKeyboardButton('Посмотерь аккаунт пользователя', url=f'tg://user?id={chat_id}')
    collect = types.InlineKeyboardButton(text='Заказ собран', callback_data=f'collect|{chat_id}|{order_id}')
    markup.add(view_user, collect)
    return markup

def take_order(order_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    view_user = types.InlineKeyboardButton('Забрал заказ', callback_data=f'take_order|{order_id}')
    markup.add(view_user)
    return markup

def product(product, page, category=None,type='products'):
    if type == 'products':
        n = f'products|{category}'
    markup = types.InlineKeyboardMarkup(row_width=1)
    menu = types.InlineKeyboardButton(text='Главное меню', callback_data='menu')
    back = types.InlineKeyboardButton(text='Назад', callback_data=f'{n}|{page}')
    add_to_cart = types.InlineKeyboardButton(text='Добавить в корзину', callback_data=f'add_to_cart|{product.id}|{page}{type}')
    markup.add(add_to_cart, back, menu)
    return markup