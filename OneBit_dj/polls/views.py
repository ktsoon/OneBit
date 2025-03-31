# __icontains неработает с SQLlite
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse # ajax
from django.contrib.auth.decorators import login_required # перенос пользователя на страницу авторизации если он не вошол в профиль на определённой странице
from django.views.generic import DetailView # DetailView - просмотр одной записи по ключу.
from django.contrib import messages # вывод сообщения
from django.contrib.auth import login, authenticate, logout
from django.core.paginator import Paginator
from django.core.cache import cache
from .models import *
from .forms import *
from django.db.models import Min, Max, Sum, F, Avg, Count, Q, ExpressionWrapper, FloatField

from django.utils import timezone

import itertools # используется в profile

# для поиска
# from django.db.models import Q
from fuzzywuzzy import fuzz
def fuzzy_search(query, model, field, similarity_threshold=70, method=''):
    # query: запрос.
    # model: класс модели Django.
    # field: имя поля в модели, по которому вы хотите выполнить поиск.
    # similarity_threshold процент сходства
    # method: метод fuzzywuzzy
    results = model.objects.all()

    # Фильтруем результаты по сходству
    filtered_results = []
    for result in results:
        if method == 'ratio':
            similarity = fuzz.ratio(getattr(result, field).lower(), query.lower())
        else:
            similarity = fuzz.WRatio(getattr(result, field).lower(), query.lower())
        if similarity >= similarity_threshold:
            filtered_results.append((result, similarity))

    # Сортируем результаты по убыванию сходства
    filtered_results.sort(key=lambda x: x[1], reverse=True)
    # print(filtered_results) # узнать какой процент сходства
    
    # Возвращаем только объекты модели
    return [result[0] for result in filtered_results]

def format_price(price):
    """ Убирает дробную часть и добавляет пробелы между разрядами """
    return f"{int(price):,}".replace(",", "")

def search_tovars_by_characteristics(search_text):
    """ Поиск товаров по характеристикам """
    return [
        spec.tovar for spec in Specs.objects.select_related("tovar")
        if fuzz.WRatio(spec.description.lower(), search_text.lower()) >= 81
    ]

title_list = [
        ['Недавно просмотреные'],
        ['Акции и скидки'],
        ['Популярные товары'],
        # ['Недавно просмотреные'],
        # ['Акции и скидки', '/pass'],
        # ['Популярные товары', '/pass'],
        # 'Рекомендуем для вас', (добавить) если пользователь авторизирован
    ]

def index(request):
    """ Главная """
    context = {}

    if not request.user.is_authenticated:
        cache.clear()

    favorites = []
    if request.user.is_authenticated:
        favorites = Favoritess.objects.filter(user=request.user).values_list('tovar__id', flat=True)
        history = History_tovars.objects.filter(user=request.user)[:20]

        context['favorites'] = favorites
        context['history'] = history
    
    t1 = title_list if request.user.is_authenticated and history.count() > 5 else title_list[1:]

    stocks = Tovars.objects.annotate(
        skidka_value=ExpressionWrapper(
            100 * (F('cost') - F('skidka_cost')) / F('cost'),
            output_field=FloatField()
        ),
        review_count_tovar=Count('comments'),
        rating_tovar=Avg('comments__star')
    ).order_by('-skidka_value', '-review_count_tovar', '-rating_tovar')[:20]

    context['t1'] = t1
    context['stocks'] = stocks

    return render(request, 'index.html', context)

def product(request, slug):
    """ Товар """
    context = {}

    tovar = get_object_or_404(Tovars, slug=slug)

    context["tovar"] = tovar
    user = request.user

    # категории характеристик
    char = tovar.specs.all().order_by('category__gl_category')
    s = []
    for c in char:
        if c.category.gl_category in s: continue
        s.append(c.category.gl_category)
    context['GlavChar'] = s

    # история просмотра
    if user.is_authenticated:
        visite = History_tovars.objects.filter(user=user, tovar__slug=slug).count() # открывали ли товар до этого (0-нет 1-да)
        if visite == 0: # если user просматривает товар впервые
            History_tovars.objects.create(tovar=context["tovar"], user=user) # заносим в базу
        else: # если user уже просматривал этот товар до этого
            h = History_tovars.objects.get(user=user, tovar__slug=slug)
            h.created_at = timezone.now()
            h.save()
        # /история просмотра/
        hist = History_tovars.objects.filter(user=user)[:20]
        if hist.count() > 5: context['history'] = hist

    # комментарии
    com = tovar.comments.all()
    if com and user.is_authenticated: 
        user_comments = com.filter(user=user)
        if user_comments: context['user_comments'] = True
        else: context['user_comments'] = False
        other_comments = com.exclude(user=user)
        com = list(user_comments) + list(other_comments)
    context['comments'] = com
    # куплен ли товар у пользователя
    if user.is_authenticated:
        context['if_buy'] = Order.objects.filter(
                dostavka='received', 
                user_id=user,
                tovar_order__tovar__slug=slug
            ).distinct().count()

    if user.is_authenticated:
        context['favorite'] = Favoritess.objects.filter(user=user, tovar__slug=slug).count() # добавлен ли товар в избранное
        context['title'] = title_list[0]
        context['if_basket'] = Basket.objects.filter(user=user, tovar__slug=slug).count()
    return render(request, 'product_index.html', context)

def sing_in(request):
    """ Авторизация пользователя """
    # при первом заходе на сайт
    if request.method == 'GET':
        form = LoginForm()
        if request.user.is_authenticated:
            return redirect('home')
    # при нажатии на кнопку
    elif request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, "Вы успешно вошли")
                return redirect('home')

        # форма не прошла проверку
        messages.success(request, "Неверный логин или пароль")

    return render(request, 'login.html', {"form": form})
def sing_up(request):
    """ Регистрация пользователя """
    # при первом заходе на сайт
    if request.method == 'GET':
        form = RegisterForm()
        if request.user.is_authenticated:
            return redirect('home')

    # при нажатии на кнопку
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            login(request, user)
            messages.success(request, "Вы успешно зарегистрировались.")
            return redirect("home")
        else:
            return render(request, 'register.html', {"form": form})
    
    return render(request, 'register.html', {"form": form})
def sing_out(request):
    logout(request)
    messages.success(request,'Вы успешно вышли.')
    cache.clear()
    return redirect("home")

@login_required
def favorites(request):
    """ страница избранное """
    sorting = request.GET.get('sorting')
    sorting_name = 'Сначала новые'
    user = request.user.id
    
    favorites = Favoritess.objects.filter(user=user)
    if sorting == 'new' or not sorting:
        favorites = favorites.order_by('created_at')
    elif sorting == 'old':
        favorites = favorites.order_by('-created_at')
        sorting_name = 'Сначала старые'
    elif sorting == 'low':
        favorites = favorites.order_by('tovar__cost', 'tovar__skidka_cost')
        sorting_name = 'Сначала дешёвые'
    elif sorting == 'exp':
        favorites = favorites.order_by('-tovar__skidka_cost', '-tovar__cost')
        sorting_name = 'Сначала дорогие'

    context = {
        'favorites': favorites,
        'sorting': sorting_name,
        'if_basket_all': [_ for _ in Basket.objects.filter(user=request.user).values_list('tovar__id', flat=True)],
    }

    return render(request, 'favorites.html', context)

@login_required
def profile(request):
    """ Профиль пользователя """

    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = None
    context = {}
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            cache.clear()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)

    commented_tovars = Comments.objects.filter(user_id=request.user).values_list('tovar', flat=True)
    # оставить комментарии для определённых товаров
    orders = Order.objects.filter(
        dostavka='received', 
        user_id=request.user
    )

    # Собираем уникальные товары из отфильтрованных заказов
    unique_tovars = set()
    for o in orders:
        for tovar in o.tovar_order.all():
            # Исключаем товары, на которые пользователь уже оставил комментарий
            if tovar.tovar.id not in commented_tovars:
                unique_tovars.add(tovar)

    context['comment_us'] = set(itertools.islice(unique_tovars, 6))
    
    context['form'] = form
    context['title'] = title_list[0]
    avatar = UserProfile.objects.filter(user=request.user)
    if avatar: context['avatar'] = avatar[0].avatar
    return render(request, 'profile.html', context)

def search(request):
    """ Страница с товарами по запросу (поиск) """
    search_text = request.GET.get('search', '').strip()
    if not search_text or len(search_text) > 100:
        return redirect("home")

    request.session['text_search'] = search_text
    context = {'title': search_text}

    # Проверяем, совпадает ли запрос с категорией
    category_match = fuzzy_search(search_text, Category, 'category', similarity_threshold=80, method='ratio')
    if category_match:
        return redirect('category', cat_slug=category_match[0].slug)

    # Проверяем, совпадает ли запрос с производителем
    author_match = fuzzy_search(search_text, Avtor, 'avtor', similarity_threshold=80, method='ratio')
    if author_match:
        context['avtor'] = author_match[0]
        tovars = list(Tovars.objects.filter(avtor=author_match[0]))
    else:
        # Поиск по названию товара и характеристикам
        tovars_by_name = list(Tovars.objects.filter(name__icontains=search_text))
        tovars_by_specs = search_tovars_by_characteristics(search_text)
        tovars = list(set(tovars_by_name + tovars_by_specs))

        if len(tovars) == 1:
            return redirect('product', slug=tovars[0].slug)

    # Если ничего не найдено
    if not tovars:
        context['tovars'] = []
        return render(request, 'search.html', context)

    # Определение мин/макс цены среди всех найденных товаров
    price_range = Tovars.objects.filter(id__in=[t.id for t in tovars]).aggregate(
        min_price=Min('skidka_cost', default=Min('cost')),
        max_price=Max('cost')
    )

    min_price_all = format_price(price_range['min_price'] or 0)
    max_price_all = format_price(price_range['max_price'] or 0)

    # Доступные категории и производители из найденных товаров
    available_categories = {t.category for t in tovars}
    available_avtors = {t.avtor for t in tovars}

    # Фильтрация товаров
    selected_categories = request.GET.getlist('category')
    selected_avtors = request.GET.getlist('avtor')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_rating = request.GET.get('rating')

    if selected_categories:
        tovars = [t for t in tovars if t.category.slug in selected_categories]
        available_avtors = {t.avtor for t in tovars}

    if selected_avtors:
        tovars = [t for t in tovars if t.avtor.slug in selected_avtors]
        available_categories = {t.category for t in tovars}

    # Фильтр по цене
    if min_price:
        min_price = int(min_price.replace(" ", ""))
        min_price = max(min_price, int(price_range['min_price'] or 0))
        tovars = [t for t in tovars if (t.skidka_cost or t.cost) >= min_price]

    if max_price:
        max_price = int(max_price.replace(" ", ""))
        max_price = min(max_price, int(price_range['max_price'] or 0))
        tovars = [t for t in tovars if (t.skidka_cost or t.cost) <= max_price]

    # Фильтр по рейтингу
    if min_rating:
        min_rating = float(min_rating)
        tovars = [t for t in tovars if t.rating >= min_rating]

    # Сортировка
    sort_option = request.GET.get('sort')
    if sort_option == "low":
        tovars.sort(key=lambda t: t.skidka_cost or t.cost)
        sorting = "По убыванию цены"
    elif sort_option == "exp":
        tovars.sort(key=lambda t: t.skidka_cost or t.cost, reverse=True)
        sorting = "По возрастанию цены"
    elif sort_option == "new":
        tovars.sort(key=lambda t: t.created_at, reverse=True)
        sorting = "По новинкам"
    else:
        sorting = "По релевантности"

    # Пагинация
    paginator = Paginator(tovars, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Избранное
    if request.user.is_authenticated:
        favorites, if_basket_all = [], []
        favorites = Favoritess.objects.filter(user=request.user).values_list('tovar__id', flat=True)
        if_basket_all = list(Basket.objects.filter(user=request.user).values_list('tovar__id', flat=True))
        context['favorites'] = favorites
        context['if_basket_all'] = if_basket_all

    # Обновление контекста
    context.update({
        'tovars': page_obj.object_list,
        'page_obj': page_obj,
        'sorting': sorting,
        'sort_option': sort_option,
        'categories': available_categories,
        'avtors': available_avtors,
        'min_price': min_price_all,
        'max_price': max_price_all,
        'selected_categories': selected_categories,
        'selected_avtors': selected_avtors,
        'selected_min_price': request.GET.get('min_price') or min_price_all,
        'selected_max_price': request.GET.get('max_price') or max_price_all,
        'selected_rating': min_rating or 0,
    })

    return render(request, 'search.html', context)

def category(request, cat_slug):
    """ Страница с товарами для выбранной категории """
    cat = get_object_or_404(Category, slug=cat_slug)
    tovars = list(Tovars.objects.filter(category=cat))

    # Если товаров нет
    if not tovars:
        return render(request, 'search.html', {'category': cat, 'title': cat.category, 'tovars': []})

    related_categories = Category.objects.all()

    # Определение мин/макс цены среди найденных товаров
    price_range = Tovars.objects.filter(category=cat).aggregate(
        min_price=Min('skidka_cost', default=Min('cost')),
        max_price=Max('cost')
    )

    min_price_all = format_price(price_range['min_price']) or 0
    max_price_all = format_price(price_range['max_price']) or 0

    # Доступные производители
    available_avtors = Avtor.objects.filter(tovars__category=cat).distinct()

    # Фильтрация товаров
    selected_avtors = request.GET.getlist('avtor')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_rating = request.GET.get('rating')

    if selected_avtors:
        tovars = [t for t in tovars if str(t.avtor.slug) in selected_avtors]

    if min_price:
        min_price = int(min_price)
        min_price = max(min_price, int(min_price_all))
        tovars = [t for t in tovars if (t.skidka_cost or t.cost) >= min_price]

    if max_price:
        max_price = int(max_price)
        max_price = min(max_price, int(max_price_all))
        tovars = [t for t in tovars if (t.skidka_cost or t.cost) <= max_price]

    if min_rating:
        min_rating = float(min_rating)
        tovars = [t for t in tovars if t.rating >= min_rating]

    # Сортировка
    sort_option = request.GET.get('sort', 'pop')
    if sort_option == "low":
        tovars.sort(key=lambda t: t.skidka_cost or t.cost)
        sorting = "По убыванию цены"
    elif sort_option == "exp":
        tovars.sort(key=lambda t: t.skidka_cost or t.cost, reverse=True)
        sorting = "По возрастанию цены"
    elif sort_option == "new":
        tovars.sort(key=lambda t: t.created_at, reverse=True)
        sorting = "По новинкам"
    else:
        tovars.sort(key=lambda t: t.comments.count(), reverse=True)  # По популярности (по количеству отзывов)
        sorting = "По релевантности"

    # Пагинация
    paginator = Paginator(tovars, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Избранное
    favorites = []
    if_basket_all = []
    if request.user.is_authenticated:
        favorites = Favoritess.objects.filter(user=request.user).values_list('tovar__id', flat=True)
        if_basket_all = list(Basket.objects.filter(user=request.user).values_list('tovar__id', flat=True))

    context = {
        'category': cat,
        'title': cat.category,
        'tovars': page_obj.object_list,
        'page_obj': page_obj,
        'categories': related_categories,
        'avtors': available_avtors,
        'sorting': sorting,
        'sort_option': sort_option,
        'min_price': min_price_all,
        'max_price': max_price_all,
        'selected_avtors': selected_avtors,
        'selected_min_price': request.GET.get('min_price') or min_price_all,
        'selected_max_price': request.GET.get('max_price') or max_price_all,
        'selected_rating': min_rating or 0,
        'favorites': favorites,
        'if_basket_all': if_basket_all
    }

    return render(request, 'search.html', context)

@login_required
def baskett(request):
    """ Корзина """
    context = {}

    tov = Basket.objects.filter(user=request.user)

    # Избранное
    favorites = []
    favorites = Favoritess.objects.filter(user=request.user).values_list('tovar__id', flat=True)

    context['favorites'] = favorites
    context['tovars_in_basket'] = tov

    return render(request, 'basket.html', context)

@login_required
def add_order(request):
    """ Добавление в заказ """
    
    if request.method != "POST" or not request.user.is_authenticated:
        return JsonResponse({"error": "Вы не авторизованы!"}, status=400)

    data = request.POST
    sposob_opl = data.get("Sposob")

    # Проверка типа доставки
    if sposob_opl == "Pochta":
        full_name = data.get("FCs", "").strip()
        address = data.get("address", "").strip()
        postal_address = data.get("postal-address", "").strip()

        if not full_name:
            return JsonResponse({"error": "Введите ФИО!", "code": "FCs"}, status=400)
        if not address:
            return JsonResponse({"error": "Введите адрес!", "code": "address"}, status=400)
        if not postal_address:
            return JsonResponse({"error": "Введите почтовый адрес!", "code": "postal-address"}, status=400)

    elif sposob_opl == "pickup":
        coords = data.get("coords-map", "").strip()
        if not coords:
            return JsonResponse({"error": "Выберите адрес магазина!", "code": "coords"}, status=400)
    else:
        return JsonResponse({"error": "Некорректный способ доставки!"}, status=400)

    # Получаем товары из корзины
    basket_items = Basket.objects.filter(user=request.user, if_select=True)
    if not basket_items.exists():
        return JsonResponse({"error": "ВЫберите товары!"}, status=400)

    # Создание заказа
    order = Order.objects.create(
        user=request.user,
        dostavka='collect',
        sposob_dostavka=sposob_opl,
        FCs=full_name if sposob_opl == "Pochta" else "",
        adress=address if sposob_opl == "Pochta" else "",
        adress_mail=postal_address if sposob_opl == "Pochta" else "",
        coords=coords if sposob_opl == "pickup" else "",
    )

    # Перемещение товаров из корзины в заказ
    for item in basket_items:
        price = item.tovar.skidka_cost if item.tovar.skidka_cost else item.tovar.cost
        order.tovar_order.create(tovar=item.tovar, t_cost=price, t_count=item.t_count, user=request.user)

    # Очистка корзины
    basket_items.delete()

    return JsonResponse({"redirect": "/orderlist/"})

@login_required
def order_confirmation(request):
    """ Оформление заказа """
    context = {}

    from django.conf import settings
    context['STATIC_URL_CARD'] = settings.STATIC_URL+'img/card'

    ord_tov = Basket.objects.filter(user=request.user, if_select=True)
    if not ord_tov: return redirect("basket")
    context['tovars'] = ord_tov

    return render(request, 'order_confitmation.html', context)

@login_required
def orderr(request):
    """ Список заказов """
    context = {}
    us = request.user
    sorting = request.GET.get("sorting")
    
    ordd = Order.objects.filter(user=us).order_by('-date_update')
    
    if sorting:
        if sorting == 'act':
            ordd=ordd.filter(dostavka__in=['collect','goes','delivered'])
        if sorting == 'received':
            ordd=ordd.filter(dostavka='received')
        if sorting == 'cancelled':
            ordd=ordd.filter(dostavka='cancelled')

    context['order'] = ordd
    return render(request, "order.html", context)

@login_required
def order_details(request, order_number):
    """ Подробности заказа """

    context = {}

    context['order'] = Order.objects.get(user=request.user, order_number=order_number)
    context['img'] = ImgTovar.objects.filter(is_video=False)

    context['results'] = Order.objects.filter(user=request.user, order_number=order_number)
    
    # Избранное
    favorites = []
    favorites = Favoritess.objects.filter(user=request.user).values_list('tovar__id', flat=True)
    context['favorites'] = favorites

    return render(request, 'order_details.html', context)

def faq(request):
    """Render the FAQ page."""

    return render(request, 'faq.html')


# ajax

def search_text(request):
    """ Подсказки при вводе в поисковую строку """
    text = request.GET.get('text')
    if not text:
        return JsonResponse({'status': 400, 'message': 'No search text provided'})

    payload = []

    # Поиск категорий и авторов с учётом неточного совпадения
    categories = fuzzy_search(text, Category, 'category') or Category.objects.filter(category__icontains=text)
    authors = fuzzy_search(text, Avtor, 'avtor') or Avtor.objects.filter(avtor__icontains=text)

    # Поиск товаров (сначала точное совпадение, затем нечеткое)
    first_image_ids = (
        ImgTovar.objects
        .filter(is_video=False, tovar__name__icontains=text)
        .values('tovar_id')
        .annotate(first_image_id=Min('id'))
        .values_list('first_image_id', flat=True)
    )

    tovars_all = ImgTovar.objects.filter(id__in=first_image_ids)
    
    if not tovars_all:
        tovars_all = [
            result for result in ImgTovar.objects.filter(is_video=False)
            if fuzz.WRatio(result.tovar.name.lower(), text.lower()) >= 50
        ]
        # Убираем дублирующиеся товары
        seen_names = set()
        tovars_all = [x for x in tovars_all if not (x.tovar.name in seen_names or seen_names.add(x.tovar.name))]

    # Формирование JSON-ответа
    for cat in categories:
        payload.append({'name': cat.category, 'slug': cat.slug, 'categ': 'cat', 'gl_cat': cat.main_categories.main_category})

    for avt in authors:
        payload.append({
            'name': avt.avtor, 'slug': avt.slug, 'categ': 'avt',
            'img_url': getattr(avt.img, 'url', None)
        })

    for tovar in tovars_all:
        payload.append({
            'name': tovar.tovar.name,
            'slug': tovar.tovar.slug,
            'categ': 'tovar',
            'img_url': tovar.thumbnail_url  # Используем thumbnail_url
        })

    return JsonResponse({'status': 200, 'search': payload})

def filter_update(request):
    """ Динамическое обновление производителей и количества товаров """
    
    selected_categories = request.GET.getlist("category[]")
    filters = Q()
    if selected_categories:
        filters &= Q(category__slug__in=selected_categories)

    filtered_tovars = Tovars.objects.filter(filters).distinct()

    # Получаем список доступных производителей по отфильтрованным товарам
    avtors = Avtor.objects.filter(tovars__in=filtered_tovars).distinct().values("avtor", "slug")

    return JsonResponse({
        "avtors": list(avtors)}, status=200)

@login_required
def favorite_check(request):
    """ AJAX функция для добавления/удаления товара в Избранное """

    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        tovar_id = request.POST.get('Tovar')
        tovar = get_object_or_404(Tovars, id=tovar_id)

        favorite, created = Favoritess.objects.get_or_create(user=request.user, tovar=tovar)
        if not created:
            favorite.delete()

        count_favorite = Favoritess.objects.filter(user=request.user).count()

        return JsonResponse({'count_favorite': count_favorite}, status=200)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def basket_if_select(request):
    """ выбор товара """

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if_all = request.POST.get("if_all") == "true"
        check = request.POST.get("check") == "true"
        basket_id = request.POST.get("basket_id")

        if if_all:
            Basket.objects.filter(user=request.user).update(if_select=check)

        elif basket_id:
            basket_item = Basket.objects.filter(user=request.user, id=basket_id).first()
            if basket_item:
                basket_item.if_select = check
                basket_item.save()

        return JsonResponse({'check': 'добавлено'})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def basket_count(request):
    """ добавление количества товаров """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        basket_id = request.POST.get("basket_id")
        count = request.POST.get("count")

        if not basket_id or not count:
            return JsonResponse({'error': 'Некорректные данные'}, status=400)
        
        try:
            count = int(count)
            if count < 1 or count > 99:
                return JsonResponse({'error': 'Количество должно быть больше 0 и не больше 99'}, status=400)
        except ValueError:
            return JsonResponse({'error': 'Некорректные количество'}, status=400)
        
        basket_item = Basket.objects.filter(user=request.user, id=basket_id).first()
        if not basket_item:
            return JsonResponse({'error': 'Товар не найден'}, status=404)
        
        basket_item.t_count = count
        basket_item.save()
        
        return JsonResponse({},status=200)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def basket_add_del(request):
    """ Удаление и добавление в корзину """

    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = request.POST.get('Tovar')
        t_list = request.POST.get('list')

        if not data and t_list == 'false':
            return JsonResponse({"error": "Не переданы товары"}, status=400)
        
        if t_list == 'false': # 1 товар для удаления или добавления
            tovar = get_object_or_404(Tovars, id=data)
            basket_item, created = Basket.objects.get_or_create(user=request.user, tovar=tovar)

            
            if not created:
                basket_item.delete()
                in_basket = False
            else:
                in_basket = True
            
        else: # несколько товаров для удаления
            Basket.objects.filter(user=request.user, if_select=True).delete()
            in_basket = False

        count_basket = Basket.objects.filter(user=request.user).count()

        return JsonResponse({'in_basket': in_basket, 'count_basket': count_basket}, status=200)

    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def comm_add_edit(request):
    """ Добавление и изменение в комментариях """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        tovar_id = request.POST.get("tovar_id")
        rating = request.POST.get("rating")
        text = request.POST.get("text", "").strip()
        
        if not tovar_id or not rating:
            return JsonResponse({'error': 'Отсутствуют обязательные параметры'}, status=400)
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return JsonResponse({'error': 'Некорректное значение рейтинга'}, status=400)
        except ValueError:
            return JsonResponse({'error': 'Некорректное значение рейтинга'}, status=400)
        
        tovar = get_object_or_404(Tovars, id=tovar_id)

        comment, created = Comments.objects.update_or_create(
            user=request.user, tovar=tovar,
            defaults={'star': rating, 'text': text}
        )
        
        return JsonResponse({}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)

# load content

def load_tovars(request):
    """
    Загружает товары постронично через AJAX
    """
    page = int(request.GET.get("page", 1))
    per_page = 18
    offset = (page - 1) * per_page

    tovars = Tovars.objects.prefetch_related("images")[offset:offset + per_page]

    def format_price_tov(price):
        return f"{price:,}".replace(",", " ")  # 109240 → 109 240

    data = []
    for tovar in tovars:
        images = tovar.images.filter(is_video=False)[:5]  # Получаем первые 5 изображений, исключая видео
        image_urls = [img.medium_url for img in images]

        data.append({
            "id": tovar.id,
            "name": tovar.name,
            "slug": tovar.slug,
            "cost": format_price_tov(int(tovar.cost)),
            "skidka_cost": format_price_tov(int(tovar.skidka_cost)) if tovar.skidka_cost else None,
            "skidka": round(tovar.skidka) if tovar.skidka else 0,
            "rating": f"{tovar.rating:.1f}" if tovar.rating else 0,
            "review_count": tovar.review_count,
            "images": image_urls,  # Массив из 5 изображений
        })
        if request.user.is_authenticated:
            data[-1]["is_favorite"] = tovar.favoritess_set.filter(user=request.user).exists()

    return JsonResponse({"tovars": data, "has_next": len(tovars) == per_page})

from django.utils.timesince import timesince
def load_comments(request, product_id):
    page = int(request.GET.get("page", 1))
    user_comment = None

    # Получаем все комментарии к товару
    comments_qs = Comments.objects.filter(tovar_id=product_id).select_related("user").order_by("-created_at")

    # Если пользователь авторизован, ищем его комментарий
    if request.user.is_authenticated:
        user_comment = comments_qs.filter(user=request.user).first()
        comments_qs = comments_qs.exclude(user=request.user)  # Исключаем его из общего списка

    paginator = Paginator(comments_qs, 5)  # Пагинация только для остальных комментариев
    comments_page = paginator.get_page(page)

    # Создаем список комментариев
    comments_data = []
    
    # Добавляем комментарий пользователя только на первой странице
    if page == 1 and user_comment:
        comments_data.append({
            "id": user_comment.id,
            "username": user_comment.user.username,
            "avatar": user_comment.user.profile.avatar.url if hasattr(user_comment.user, "profile") and user_comment.user.profile.avatar else None,
            "comment": user_comment.text,
            "star": user_comment.star,
            "created_at": timesince(user_comment.created_at, timezone.now()) + " назад",
            "updated_at": timesince(user_comment.update_at, timezone.now()) + " назад" if user_comment.update_at != user_comment.created_at else None,
            "baned": user_comment.baned,
            "user_comment": True
        })

    # Добавляем остальные комментарии
    for com in comments_page:
        comments_data.append({
            "id": com.id,
            "username": com.user.username,
            "avatar": com.user.profile.avatar.url if hasattr(com.user, "profile") and com.user.profile.avatar else None,
            "comment": com.text,
            "star": com.star,
            "created_at": timesince(com.created_at, timezone.now()) + " назад",
            "updated_at": timesince(com.update_at, timezone.now()) + " назад" if com.update_at != com.created_at else None,
            "baned": com.baned,
            "user_comment": False
        })
    return JsonResponse({
        "comments": comments_data,
        "has_next": comments_page.has_next(),
    })

