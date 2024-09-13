import datetime
import os
import random
import re
import threading
import time

import telebot
import django
import qrcode
from django.utils import formats
from telebot import types

import buttons
from const import bot

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loual_programm.settings')
django.setup()

from app.models import User, History, Cart, Product, Lottery, Bonus, Rank, Orders, Stocks, Category


def get_qr(chat_id):
    url = f"https://t.me/{bot.get_me().username}?start={chat_id}"

    # Создание объекта QR-кода
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    # Кодирование ссылки в QR-код
    qr.add_data(url)
    qr.make(fit=True)

    # Создание изображения QR-кода
    img = qr.make_image(fill_color="black", back_color="white")

    # Сохранение изображения QR-кода
    img.save("qrcode.png")


def format_number(number):
    """Форматирует число в формате 10.000"""

    if isinstance(number, (int, float)):
        return f"{number:,.0f}".replace(",", ".")


def get_status(client, mn='Статус пользователя', mm='Скидка пользователя', nn='Бонусы пользователя'):
    total_amount = client.total_amount
    rangs = Rank.objects.order_by('-price')
    print(rangs)
    text = ''
    sale = 0
    for rang in rangs:
        if total_amount < rang.price:
            n = rang.price - total_amount
            n = format_number(n)
            sale = rang.sale
            text = f'{mn}: {rang.name}\n' \
                   f'{mm}: {rang.sale}%\n' \
                   f'{nn}: {client.bonus}\n\n' \
                   f'Для повышения размера скидки осталось совершить покупки на сумму {n}₽'
    if not text:
        rang = rangs.last()
        sale = rang.sale
        text = f'{mn}: {rang.name}\n' \
               f'{mm}: {rang.sale}%\n' \
               f'{nn}: {client.bonus}\n\n' \
               f'У вас максимальный уровень!'
    return text, sale


def register_buy_amount(message, chat_id, client):
    text, sale = get_status(client)
    try:
        error = 'Введите число, которое больше нуля'
        mes = message.text.split()
        if mes == 1:
            amount = float(mes[0].replace(',', '.'))
            bonus = 0
        else:
            amount = float(mes[0].replace(',', '.'))
            bonus = int(mes[1])
            if client.bonus < bonus:
                error = 'У клиента недостаточно бонусов на счету\n\n'
                text += '\nВведите сумму покупки пользователя с учетом скидки.\n' \
                       'Если клиент хочет списать бонусы, введите количество бонусов после суммы покупки, разделяя их пробелом'
                error += text
                raise Exception
    except Exception:
        msg = bot.send_message(chat_id=chat_id, text=error,
                               reply_markup=buttons.go_to_menu())
        bot.register_next_step_handler(msg, register_buy_amount, chat_id, client)
    else:
        client.bonus += round(amount*sale/100, 2)-bonus
        client.total_amount += amount
        history = History.objects.create(amount=amount)
        timestamp = datetime.datetime.now().timestamp() - client.last_lottery_time.timestamp()
        if timestamp >= 60 * 60 * 24:
            client.can_use_lottery = True
        client.history.add(history)
        client.save()
        bot.send_message(chat_id=chat_id, text='Покупка успешно оформлена')
        amount = format_number(amount)
        bot.send_message(chat_id=client.chat_id,
                         text=f'Вы совершили покупку на {amount} ₽. Спасибо, что пользуетесь услугами нашего магазина')
        menu(chat_id=chat_id)


def bonus_programm(chat_id, client):
    text, sale = get_status(client)
    text += '\nВведите сумму покупки пользователя с учетом скидки.\n' \
           'Если клиент хочет списать бонусы, введите количество бонусов после суммы покупки, разделяя их пробелом'
    msg = bot.send_message(chat_id=chat_id, text=text, reply_markup=buttons.go_to_menu())
    bot.register_next_step_handler(msg, register_buy_amount, chat_id, client)


def menu(chat_id):
    user = User.objects.get(chat_id=chat_id)
    get_qr(chat_id=chat_id)
    text, sale = get_status(client=user, mn='Ваш статус', mm='Ваша скидка', nn='Ваши бонусы:')
    text += '\n\nДля повышения скидки, предъявите QR код продавцу в магазине'
    with open('qrcode.png', 'rb') as photo:
        bot.send_photo(chat_id=chat_id, photo=photo, caption=text, reply_markup=buttons.menu())




@bot.message_handler(commands=['start'])
def start(message):
    print(message)
    chat_id = message.chat.id
    bot.clear_step_handler_by_chat_id(chat_id=chat_id)
    user, _ = User.objects.get_or_create(chat_id=chat_id)
    text = message.text.split()
    if _ or not user.birthday or not user.phone_number or not user.name:
        msg = bot.send_message(chat_id=chat_id, text='Для активации карты лояльности введите ваше имя')
        bot.register_next_step_handler(msg, enter_name, chat_id, user)
    elif user.is_seller and len(text) == 2 and len(User.objects.filter(chat_id=text[1])) == 1:
        client = User.objects.get(chat_id=text[1])
        bonus_programm(chat_id=chat_id, client=client)
    else:
        menu(chat_id=chat_id)


def enter_phone(message, chat_id, user):
    bonus = Bonus.objects.first()
    phone = message.text
    try:
        user.phone_number = phone
        user.save()
    except Exception:
        msg = bot.send_message(chat_id=chat_id, text='Введите корректный номер телефона')
        bot.register_next_step_handler(msg, enter_name, chat_id, user)
    else:
        user.bonus += bonus.bonus
        user.save()
        n = format_number(bonus.bonus)
        bot.send_message(chat_id=chat_id,
                         text=f'Спасибо за регистрацию. На ваш счет зачислено {n} бонусов. Ваша карта лояльности уже активирована и готова к использованию')
        time.sleep(4)
        menu(chat_id=chat_id)


def validate_date(date_string):
    """Проверка формата даты DD.MM.YYYY"""
    pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    match = re.match(pattern, date_string)
    if match:
        day, month, year = map(int, date_string.split("."))
        if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
            return True
        else:
            return False
    else:
        return False


def enter_birthday(message, chat_id, user):
    birthday = message.text
    try:
        if not validate_date(birthday):
            raise Exception
    except Exception:
        msg = bot.send_message(chat_id=chat_id, text='Введите дату рождения в формате 03.11.2000')
        bot.register_next_step_handler(msg, enter_name, chat_id, user)
    else:
        user.birthday = birthday
        user.save()
        msg = bot.send_message(chat_id=chat_id, text='Введите ваш номер телефона')
        bot.register_next_step_handler(msg, enter_phone, chat_id, user)


def enter_name(message, chat_id, user):
    name = message.text
    try:
        user.name = name
        user.save()
    except Exception:
        msg = bot.send_message(chat_id=chat_id, text='Введите корректное имя')
        bot.register_next_step_handler(msg, enter_name, chat_id, user)
    else:
        msg = bot.send_message(chat_id=chat_id, text='Введите вашу дату рождения.\n'
                                                     'Формат: 11.03.2000')
        bot.register_next_step_handler(msg, enter_birthday, chat_id, user)


def history(chat_id, user):
    text = 'История ваших покупок:\n\n'
    for history in user.history.all():
        amount = format_number(history.amoun)
        formatted_datetime = formats.date_format(history.date, "d-m-Y H:i")
        text += f'{formatted_datetime} {amount}₽\n\n'
    bot.send_message(chat_id=chat_id, text=text, reply_markup=buttons.go_to_menu())


def catalog(chat_id, page,categoty=None, type=None):
    if type:
        markup = buttons.catalog(page, type=type)
    else:
        markup = buttons.catalog(page, category=categoty)
    bot.send_message(chat_id=chat_id, text='Каталог продуктов', reply_markup=markup)


def detail_product(chat_id, category, prod_id, page):
    product = Product.objects.get(id=prod_id)
    n = format_number(product.price)
    text = f'Название: {product.name}\n' \
           f'Цена: {n} ₽/{product.unit}'
    if product.image:
        bot.send_photo(chat_id=chat_id, photo=product.image, caption=text, reply_markup=buttons.product(product, page, category))
    else:
        bot.send_message(chat_id=chat_id, text=text, reply_markup=buttons.product(product, page, category))


def cart(chat_id, user):
    text = 'Ваша корзина:\n\n' \
           'Для удаления товара, нажмите на нужный товар ниже'
    markup = buttons.cart(user)
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


def enter_number(message, chat_id, prod_id, page, type=''):
    user = User.objects.get(chat_id=chat_id)
    if not type:
        try:
            number = int(message.text)
        except Exception:
            msg = bot.send_message(chat_id=chat_id, text='Введите целое натуральное число',
                                   reply_markup=buttons.go_to_menu())
            bot.register_next_step_handler(msg, enter_number, chat_id, prod_id, page)
        else:
            prod = Product.objects.get(id=prod_id)
            cart = Cart.objects.create(
                product=prod,
                count=number
            )
            user.cart.add(cart)
            user.save()
            bot.send_message(chat_id=chat_id, text='Товар успешно добавлен в корзину')
            menu(chat_id=chat_id)
    else:
        try:
            stock = Stocks.objects.get(id=prod_id)
            cart = Cart.objects.create(
                stocks=stock,
                count=1
            )
        except Exception:
            prod = Product.objects.get(id=prod_id)
            cart = Cart.objects.create(
                product=prod,
                count=1
            )
        user.cart.add(cart)
        user.save()
        bot.send_message(chat_id=chat_id, text='Товар успешно добавлен в корзину')
        menu(chat_id=chat_id)


def lottery(chat_id, user):
    if user.can_use_lottery:
        rand = random.randint(1, 100)
        if rand <= 60:
            lottery = Lottery.objects.filter(rare=1)
        elif 60 < rand <= 90:
            lottery = Lottery.objects.filter(rare=2)
        elif 90 < rand <= 99:
            lottery = Lottery.objects.filter(rare=3)
        else:
            lottery = Lottery.objects.filter(rare=4)
        if lottery:
            text = 'Поздравляем! Вы выиграли '
            text += random.choice(lottery).name
            bot.send_message(chat_id=chat_id, text=text)
            time.sleep(2)
        else:
            text = 'К сожалению вы ничего не выиграли, возвращайтесь в следующий раз!'
            msg = bot.send_message(chat_id=chat_id, text=text)
            time.sleep(2)
            bot.delete_message(chat_id=chat_id, message_id=msg.id)
    else:
        text = 'Вы можете использовать лотерею раз в 24 часа, если совершили покупку в нашем магазине или через бота'
        msg = bot.send_message(chat_id=chat_id, text=text)
        time.sleep(2)
        bot.delete_message(chat_id=chat_id, message_id=msg.id)
    user.can_use_lottery = False
    user.last_lottery_time = datetime.datetime.now()
    user.save()
    menu(chat_id=chat_id)


def validate(date):
    if date == '0':
        return True
    pattern = r"^\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}$"
    match = re.match(pattern, date)
    return bool(match)


def buy(message, chat_id, user):
    date = message.text
    if not validate(date):
        msg = bot.send_message(chat_id=chat_id,
                               text='Введите дату и время, когда вам было бы удобно забрать заказ в формате ГГГГ.ММ.ДД ЧЧ:ММ.\n'
                                    'Введите 0, если вам нужно забрать заказ как можно скорее',
                               reply_markup=buttons.go_to_menu())
        bot.register_next_step_handler(msg, buy, chat_id, user)
    else:
        user.date = date
        user.save()
        total_amount = 0
        for cart in user.cart.all():
            total_amount += cart.price()
        text = 'Дата успешно добавлена.\nДля оплаты заказа, нажмите кнопку ниже'
        text, sale = get_status(client=user, mn='Ваш статус', mm='Ваша скидка')
        bot.send_message(chat_id=chat_id, text=text, reply_markup=buttons.buy(total_amount, sale))


def stock_detail(chat_id, page, prod_id):
    stock = Stocks.objects.get(id=prod_id)
    text = f'{stock.name}\n' \
           f'Цена: {stock.price} ₽/{stock.unit}\n\n' \
           f'{stock.text}'
    if stock.image:
        bot.send_photo(chat_id=chat_id, photo=stock.image, caption=text,
                       reply_markup=buttons.product(stock, page, type='stock'))
    else:
        bot.send_message(chat_id=chat_id, text=text, reply_markup=buttons.product(stock, page, type='stock'))


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    message_id = call.message.id
    chat_id = call.message.chat.id
    user, _ = User.objects.get_or_create(chat_id=call.from_user.id)
    try:
        bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass
    if call.message:
        data = call.data.split('|')
        bot.clear_step_handler_by_chat_id(chat_id=chat_id)
        if data[0] == 'menu':
            menu(chat_id=chat_id)
        elif data[0] == 'history':
            history(chat_id=chat_id, user=user)
        elif data[0] == 'products':
            catalog(chat_id=chat_id,categoty=data[1], page=data[2])
        elif data[0] == 'stock':
            catalog(chat_id=chat_id, page=data[1], type='stock')
        elif data[0] == 'stock_detail':
            stock_detail(chat_id=chat_id, page=data[2], prod_id=data[1])
        elif data[0] == 'cart':
            cart(chat_id=chat_id, user=user)
        elif data[0] == 'dell':
            prod = Cart.objects.get(id=data[1])
            prod.delete()
            bot.send_message(chat_id=chat_id, text='Товар удален изх корзины')
            cart(chat_id=chat_id, user=user)
        elif data[0] == 'product':
            detail_product(chat_id=chat_id, category=data[1], page=data[3], prod_id=data[2])
        elif data[0] == 'add_to_cart':
            if len(data) != 4:
                prod = Product.objects.get(id=data[1])
            else:
                prod = Stocks.objects.get(id=data[1])
            if not prod.need_add_to_cart:
                msg = bot.send_message(chat_id=chat_id,
                                       text='Введите количество товара, которое хотите приобрести\n'
                                            'Если товар на развес, укажите сколько грамм вы хотите приобрести',
                                       reply_markup=buttons.go_to_menu())
                bot.register_next_step_handler(msg, enter_number, chat_id, data[1], data[2])
            else:
                enter_number(message=None, chat_id=chat_id, prod_id=data[1], page=data[2], type=1)

        elif data[0] == 'lottery':
            lottery(chat_id, user)
        elif data[0] == 'buy':
            msg = bot.send_message(chat_id=chat_id,
                                   text='Введите дату и время, когда вам было бы удобно забрать заказ в формате ГГГГ.ММ.ДД ЧЧ:ММ.\n'
                                        'Введите 0, если вам нужно забрать заказ как можно скорее',
                                   reply_markup=buttons.go_to_menu())
            bot.register_next_step_handler(msg, buy, chat_id, user)
        elif data[0] == 'collect':
            number = data[1]
            order = Orders.objects.get(id=data[2])
            order.status = 'Готов к выдаче'
            order.save()
            text = f'Номер вашего заказа: {number}\n' \
                   'Ваш заказ собран. Для того, чтобы его забрать, назовите номер продавцу'
            bot.send_message(chat_id, text=text, reply_markup=buttons.take_order(data[2]))
        elif data[0] == 'categorys':
            bot.send_message(chat_id=chat_id, text='Выберите категорию', reply_markup=buttons.categorys())
        elif data[0]=='take_order':
            order = Orders.objects.get(id=data[2])
            order.status = 'Заказ получен'
            order.save()


def malling():
    while True:
        for prod in Stocks.objects.filter(is_send_message=True):
            text = prod.text
            markup = buttons.stock(prod)
            photo = prod.photo
            for user in User.objects.filter(is_seller=False):
                try:
                    if prod.image:
                        bot.send_photo(chat_id=user.chat_id, photo=photo, caption=text, reply_markup=markup)
                    else:
                        bot.send_message(chat_id=user.chat_id, text=text, reply_markup=markup)
                except Exception:
                    pass
            prod.is_send_message = False
            prod.save()
        time.sleep(60)


def clear_history():
    while True:
        for user in User.objects.filter(is_seller=False):
            last_month = datetime.datetime.now() - datetime.timedelta(days=30)
            for history in user.history.all():
                if history.date.timestamp() <= last_month.timestamp():
                    history.delete()
            try:
                day, month, year = user.birthday.split('.')
                now_day = datetime.datetime.now().day
                now_month = datetime.datetime.now().month
                if day == now_day and month == now_month:
                    bonus = Bonus.objects.first()
                    user.bonus += bonus.birthday_bonus
                    user.save()
                    bot.send_message(chat_id=user.chat_id,
                                     text=f'Поздравляем вас с днем рождения. В честь этого праздника на ваш счет зачислено {bonus.birthday_bonus} бонусов')
            except Exception:
                pass
        time.sleep(60 * 60 * 24)


@bot.shipping_query_handler(func=lambda query: True)
def shipping(shipping_query):
    bot.answer_shipping_query(shipping_query.id, ok=True, shipping_options=shipping_query,
                              error_message='Oh, seems like our Dog couriers are having a lunch right now. Try again later!')


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="Aliens tried to steal your card's CVV, but we successfully protected your credentials,"
                                                " try to pay again in a few minutes, we need a small rest.")


def send_message_to_saller(user, order):
    number = user.chat_id
    text = f'Заказ номер {number}\n' \
           f'Номер для связи с клиентом: {user.phone_number}\n' \
           f'Позиции для сбора заказа:\n'
    markup = buttons.collet(number)
    for n, cart in enumerate(order.products.all(), 1):
        if cart.product:
            text += f'{n}) {cart.product.name} {cart.count} {cart.product.unit}\n'
        else:
            text += f'{n}) {cart.stocks.name} {cart.count} {cart.stocks.unit}\n'
    for seller in User.objects.filter(is_seller=True):
        try:
            bot.send_message(chat_id=seller.chat_id, text=text, reply_markup=markup)
        except Exception:
            pass


@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    chat_id = message.chat.id
    user = User.objects.get(chat_id=chat_id)
    if user.date == '0':
        date = 'Как можно скорее'
    else:
        date = user.date
    timestamp = (datetime.datetime.now() - user.last_lottery_time()).timestamp()
    if timestamp >= 60 * 60 * 24:
        user.can_use_lottery = True
    order = Orders.objects.create(date=date)
    for cart in user.cart.all():
        user.total_amount += cart.price()
        order.products.add(cart)
        user.cart.remove(cart)
        user.save()
    user.orders.add(order)
    send_message_to_saller(user, order)
    bot.send_message(message.chat.id,
                     'Оплата прошла успешно! Как ваш заказ соберут, вам поступит сообщение, и вы сможете забрать его у нас в магазине')
    time.sleep(3)
    menu(chat_id=chat_id)


if __name__ == '__main__':
    clear_history = threading.Thread(target=clear_history)
    clear_history.start()
    malling = threading.Thread(target=malling)
    malling.start()
    bot.infinity_polling(timeout=50, long_polling_timeout=25)
