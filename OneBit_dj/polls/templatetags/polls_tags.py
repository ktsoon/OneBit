from django import template

from polls.models import *

from django.db.models import F, FloatField, ExpressionWrapper, Avg, Count

register = template.Library()

""" поменять переменную """
@register.simple_tag
def define(val=None): return val

""" сумирует переменные """
@register.simple_tag
def summ(s1, val): return s1+val

""" умножение переменных """
@register.filter
def multiply(value, arg): return value * arg

""" аватарка """
@register.simple_tag
def avatar_img(userr):
    a = UserProfile.objects.filter(user=userr)
    if a: return a[0].avatar
    else: return False

""" количество одного товара в корзине """
@register.simple_tag
def bask_count(tov, us): return basket.objects.filter(user__id=us, tovar__id=tov)[0].t_count

""" возвращение всех категорий для каталога """
@register.simple_tag
def specifications(): return Category.objects.all()
@register.simple_tag
def Gl_specifications(): return Gl_category.objects.all()

""" все изображения товаров """
@register.simple_tag
def tovar_img_all(): return img_tovar.objects.all()

""" недавно просмотренные товары """
@register.simple_tag
def history_tovars_all(user):
    a = history_tovars.objects.filter(user=user).order_by('-created_at')[:20].select_related('tovar').annotate(
        rating=Avg('tovar__comments__star'),         # Средний рейтинг товара
        count_com=Count('tovar__comments')        # Количество отзывов
    )
    for i in a:
        i=i.tovar
        if i.skidka_cost:
            i.skidka = round(100 * (i.cost - i.skidka_cost) / i.cost)
    return a

""" Акции и скидки товары """
@register.simple_tag
def skidka_tovars_all():
    return Tovars.objects.annotate(
        skidka=ExpressionWrapper(
            100 * (F('cost') - F('skidka_cost')) / F('cost'),
            output_field=FloatField()
        ),
        rating=Avg('comments__star'),
        count_com=Count('comments')
    ).exclude(skidka_cost=None).order_by('-skidka', '-count_com','-rating')[:20]

""" Скидка определённого товара """
@register.simple_tag
def skidka_tovar(cost, skidka_cost): return 100 * (cost - skidka_cost) / cost

""" Первая картинка товара """
@register.simple_tag
def tovar_img_first(tovar): return img_tovar.objects.filter(tovar=tovar, is_video=False).first().img.url

""" Возвращает правильное окончание для слова 'отзыв' """
@register.filter
def review_word(count):
    if 11 <= count % 100 <= 14:
        return "отзывов"
    last_digit = count % 10
    if last_digit == 1:
        return "отзыв"
    elif 2 <= last_digit <= 4:
        return "отзыва"
    else:
        return "отзывов"
    
"""Возвращает правильное окончание для слова 'товар'."""
@register.filter
def pluralize_goods(count):
    count = abs(int(count))
    if 11 <= count % 100 <= 19:
        return "товаров"
    last_digit = count % 10
    if last_digit == 1:
        return "товар"
    elif 2 <= last_digit <= 4:
        return "товара"
    else:
        return "товаров"
    
""" Популярные товары """
@register.filter
def popular_tovar_order(tovars): return tovars.order_by('-count_com','-rating')

