from django.urls import path
from . import views

from django.http import HttpResponse
from django.conf import settings
import os
def robots_txt(request):
    """
    Представление для robots.txt. Возвращает содержимое static/robots.txt.
    """
    file_path = os.path.join(settings.BASE_DIR, 'static', 'robots.txt')
    with open(file_path, 'r') as file:
        return HttpResponse(file.read(), content_type='text/plain')

urlpatterns = [
    path('', views.index, name='home'), # главная
    path('product/<str:slug>/', views.product, name='product'), # отдельный товар
    path('login/', views.sing_in, name="login"), # авторизация
    path('register/', views.sing_up, name="register"), # регистрация
    path('favorites/', views.favorites, name='favorites'), # избранные товары
    path('profile/', views.profile, name='profile'), # профиль пользователя
    path('search/', views.search, name='search'), # поиск
    path('category/<str:cat_slug>/', views.category, name='category'), # поиск, но с категориями
    path('basket/', views.baskett, name='basket'), # корзина
    path('basket/confirmation/', views.order_confirmation, name='order_confirmation'), # подтверждение заказа
    path('orderlist/', views.orderr, name='order'), # заказы
    path('orderdetails/<str:order_number>/', views.order_details, name='order_details'), # заказы
    path('FAQ/', views.faq, name="faq"), # Часто задаваемые вопросы (FAQ)

    # ---------------------------AJAX---------------------------
    path('sing_out/', views.sing_out, name="logout"), # выйти из аккаунта ajax
    path('favorite_check/', views.favorite_check, name='favorite_check'), # проверка на отправку избранных ajax
    path('product_comm/', views.comm_add_edit, name='comm_add_edit'), # отдельный товар
    path('search_text/', views.search_text, name='search_text'), # поисковая строка ajax
    path('search/filters/', views.filter_update, name='filter_update'),  # обновления фильтров ajax
    path('basket_add_del/', views.basket_add_del, name='basket_add_del'), # корзина. удаление и добавление ajax
    path('basket_count/', views.basket_count, name='basket_count'), # корзина. обновить количество товара ajax
    path('basket/select/', views.basket_if_select, name='basket_if_select'), # выбор товара ajax
    path('add_order/', views.add_order, name='add_order'), # добавление в заказ ajax

    path('load_tovars/', views.load_tovars, name='load_tovars'), # AJAX загрузка товаров
    path('load_comments/<int:product_id>/', views.load_comments, name='load_comments'), # AJAX загрузка товаров

    # ---------------------------seo---------------------------
    path('robots.txt', robots_txt, name='robots_txt'), # robots.txt 
    path('yandex_26fe0f1d1ef9ebba.html', views.yandex_seo, name='yandex_txt'), # robots.txt 
    path('googlec6ef7980068add75.html', views.google_seo, name='google_txt'), # robots.txt 
] 
# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)