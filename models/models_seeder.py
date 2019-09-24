import random
import string
from models.cats_and_products_models import Category, Product, Text
from models.text_for_shop import CATEGORIES, PRODUCTS
from mongoengine import connect

random_bool = (True, False)


def random_string(string_length=10):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(string_length))


def seed_and_get_categories(cats_list):
    category_list = []
    for category in cats_list:
        temp_category = Category(title=category).save()
        category_list.append(temp_category)
    return category_list


def seed_products(list_of_products, categories):
    for i in range(50):
        product = dict(
            title=random.choice(list_of_products),
            description=random_string(),
            price=random.randint(1000, 100 * 1000),
            quantity=random.randint(0, 100),
            is_available=random.choice(random_bool),
            is_discount=random.choice(random_bool),
            length=random.uniform(0, 100),
            height=random.uniform(0, 100),
            width=random.uniform(0, 100),
            category=random.choice(categories)
        )
        Product(**product).save()


def seed_products_with_image():
    products = Product.objects.all()

    for i in products:
        with open('/Users/macbookair/PycharmProjects/adv/lesson13/bot/images/image.png',
                  'rb') as image:
            i.image.put(image)
            i.save()


if __name__ == '__main__':
    connect('bot_shop')
    en_text = dict(
         title='Greetings',
         text=random_string(2000),
    )
    Text(**en_text).save()

    ru_text = dict(
         title='Ru greetings',
         text='Добро пожаловать в наш магазин. '
              'Спасибо что Вы посетили наш магазин. Надеюсь Вы найдёте то, '
              'что искали! Удачных покупок! :-)'
     )
    Text(**ru_text).save()

    """Seed 10 categories and 50 products"""
    categories_10 = list(CATEGORIES.keys())[:10]
    seeded_categories = seed_and_get_categories(categories_10)
    seed_products(PRODUCTS, seeded_categories)

    """Seed 3 subcategories in first category"""
    category_obj = Category.objects.all().first()
    auto_category = CATEGORIES['Авто']
    subcategories = seed_and_get_categories(auto_category)
    category_obj.sub_categories = subcategories
    category_obj.save()

    """Add to each product image"""
    # seed_products_with_image()
