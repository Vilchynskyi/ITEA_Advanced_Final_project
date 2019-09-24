import telebot
from bot.config import TOKEN
from models.cats_and_products_models import (Category,
                                             Text,
                                             Cart,
                                             Product,
                                             OrdersHistory)
from models.user_model import User
from mongoengine import *
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
)
from bson import ObjectId

connect('bot_shop')

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def send_greetings(message):
    User.get_or_create_user(message)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True,
                                   one_time_keyboard=True)
    keyboard.row('Категории', 'Корзина', 'История заказов')
    # keyboard.row(*config.START_KEYBOARD.values())
    if message.from_user.language_code == 'ru':
        bot.send_message(message.chat.id, Text.get_text('Ru greetings'),
                         reply_markup=keyboard)
    elif message.from_user.language_code == 'de':
        bot.send_message(message.chat.id, Text.get_text('Greetings'),
                         reply_markup=keyboard)


# @bot.message_handler(func=lambda message: message.text == config.START_KEYBOARD['categories])
@bot.message_handler(func=lambda message: message.text == 'Категории')
def show_all_categories(message):
    user = User.objects.filter(user_id=message.chat.id).first()
    user.update(user_state='categories')
    user.save()

    categories_kb = InlineKeyboardMarkup()
    all_categories = Category.objects.all()
    buttons_list = []

    for category in all_categories:
        arrow = ''
        callback_data = 'category_' + str(category.id)
        if category.is_parent:
            arrow = ' ->'
            callback_data = 'subcategory_' + str(category.id)
        buttons_list.append(
            InlineKeyboardButton(text=category.title + str(arrow),
                                 callback_data=callback_data)
        )
    categories_kb.add(*buttons_list)
    bot.send_message(chat_id=message.chat.id,
                     text='Все категории:',
                     reply_markup=categories_kb)


@bot.callback_query_handler(func=lambda call: call.data == 'back')
def back_button(call):
    user = User.objects.filter(user_id=call.message.chat.id).first()
    if not user.user_state == 'products':
        bot.delete_message(chat_id=call.message.chat.id,
                           message_id=call.message.message_id)
    show_all_categories(call.message)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'subcategory')
def show_subcategories(call):

    subcategories_kb = InlineKeyboardMarkup()
    category = Category.objects.get(id=call.data.split('_')[1])
    sub_buttons_list = []

    for category in category.sub_categories:
        callback_data = 'category_' + str(category.id)
        if category.is_parent:
            callback_data = 'subcategory_' + str(category.id)
        sub_buttons_list.append(
            InlineKeyboardButton(text=category.title,
                                 callback_data=callback_data)
        )
    sub_buttons_list.append(
        InlineKeyboardButton(text='Назад <-',
                             callback_data='back')
    )
    subcategories_kb.add(*sub_buttons_list)
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text='Все подкатегории:',
                          reply_markup=subcategories_kb)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'category')
def show_products(call):
    user = User.objects.filter(user_id=call.message.chat.id).first()
    user.update(user_state='products')
    user.save()

    category = Category.objects.filter(id=call.data.split('_')[1]).first()
    products = category.category_products

    if not products:
        bot.send_message(call.message.chat.id,
                         'В данной категории пока нет товаров')

    for p in products:
        products_kb = InlineKeyboardMarkup()
        products_kb.add(InlineKeyboardButton(
            text='В корзину',
            callback_data='addtocart_' + str(p.id)
            ),
            InlineKeyboardButton(
                text='Подробно',
                callback_data='productdetail_' + str(p.id)
            ),
            InlineKeyboardButton(
                text='Назад <-',
                callback_data='back'
            )
        )
        title = f'<b>{p.title}</b>'
        description = f'\n\n<i>{p.description}</i>'
        bot.send_photo(chat_id=call.message.chat.id,
                       photo=p.image.get(),
                       caption=title + description,
                       reply_markup=products_kb,
                       parse_mode='HTML',
                       )


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'addtocart')
def add_product_to_cart(call):
    Cart.create_or_append_to_cart(product_id=call.data.split('_')[1],
                                  user_id=call.message.chat.id)

    cart = Cart.objects.all().first()
    print(cart.get_total_price)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'productdetail')
def show_product_detail(call):
    detail = Product.objects.filter(id=call.data.split('_')[1]).first()
    price = f'<b>Цена: {detail.price}</b>'
    quantity = f'\n\nКоличество в наличии: {detail.quantity}'
    length = f'\n\nДлина: {detail.weight}'
    height = f'\nВысота: {detail.height}'
    width = f'\nШирина: {detail.width}'
    bot.send_message(chat_id=call.message.chat.id,
                     text=price + quantity + length + height + width,
                     parse_mode='HTML')


@bot.message_handler(func=lambda message: message.text == 'Корзина')
def show_cart(message):
    current_user = User.objects.get(user_id=message.chat.id)
    cart = Cart.objects.filter(user=current_user, is_archived=False).first()

    if not cart:
        bot.send_message(message.chat.id, 'Корзина пустая')
        return

    if not cart.products:
        bot.send_message(message.chat.id, 'Корзина пустая')

    for product in cart.products:
        remove_kb = InlineKeyboardMarkup()
        remove_button = InlineKeyboardButton(text='Delete',
                                             callback_data='rmproduct_' + str(product.id))
        remove_kb.add(remove_button)
        bot.send_message(chat_id=message.chat.id,
                         text=product.title,
                         reply_markup=remove_kb)

    submit_kb = InlineKeyboardMarkup()
    submit_button = InlineKeyboardButton(
        text='Оформить заказ',
        callback_data='submit'
    )
    submit_kb.add(submit_button)
    bot.send_message(chat_id=message.chat.id,
                     text='Подтвердите ваш заказ',
                     reply_markup=submit_kb)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'rmproduct')
def delete_product_from_cart(call):
    current_user = User.objects.get(user_id=call.message.chat.id)
    cart = Cart.objects.get(user=current_user)
    cart.update(pull__products=ObjectId(call.data.split('_')[1]))
    bot.delete_message(chat_id=call.message.chat.id,
                       message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'submit')
def submit_cart(call):
    current_user = User.objects.get(user_id=call.message.chat.id)
    cart = Cart.objects.filter(user=current_user, is_archived=False).first()
    cart.is_archived = True

    order_history = OrdersHistory.get_or_create(current_user)
    order_history.orders.append(cart)
    bot.send_message(chat_id=call.message.chat.id,
                     text='Спасибо за заказ!')
    cart.save()
    order_history.save()


@bot.message_handler(func=lambda message: message.text == 'История заказов')
def send_order_history(message):
    current_user = User.objects.get(user_id=message.chat.id)
    order_history = OrdersHistory.objects.get(user=current_user)
    bot.send_message(chat_id=message.chat.id,
                     text=order_history.orders)
    order = OrdersHistory.get_or_create(current_user)
    for ord in order.orders:
        print(ord[ObjectId])


if __name__ == '__main__':
    print('Bot started')
    bot.polling()
