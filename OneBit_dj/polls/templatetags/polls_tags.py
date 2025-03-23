from django import template

from polls.models import *

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
def avatar_img(user):
    a = UserProfile.objects.filter(user=user).values_list('avatar', flat=True)
    if a: return a[0]
    else: return False

@register.simple_tag
def Gl_specifications():
    return Gl_category.objects.prefetch_related('categories').all()

""" Первая картинка товара """
@register.filter
def tovar_img_first(images): return images.filter(is_video=False).first().medium_url

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
    

