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

@login_required
def favorite_check(request):
    data = { 'check': 'ошибка', }
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user = request.POST.get('User')
        tovar = request.POST.get('Tovar')
        Arr = favoritess.objects.filter(user__username=user, tovar__id=tovar)
        if request.POST.get('checked') == 'true' and not Arr:
            Arr = favoritess(user=User.objects.get(username=user), tovar=Tovars.objects.get(id=tovar))
            Arr.save()
            data['check'] = 'добавлен в'
        if request.POST.get('checked') == 'false' and Arr:
            Arr.delete()
            data['check'] = 'удалён из'
        data['value'] = favoritess.objects.filter(user__username=user).count()
    return JsonResponse(data)

# исправить ошибку в авторизации (ошибка email)

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
    paginator = Paginator(tovars, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Избранное
    favorites = []
    if request.user.is_authenticated:
        favorites = Favoritess.objects.filter(user=request.user).values_list('tovar__id', flat=True)
    context['favorites'] = favorites

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
        'selected_min_price': request.GET.get('min_price'),
        'selected_max_price': request.GET.get('max_price'),
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

    # Определяем главную категорию и связанные категории
    gl_category = cat.main_categories
    related_categories = Category.objects.filter(main_categories=gl_category)

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
    paginator = Paginator(tovars, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Избранное
    favorites = []
    if request.user.is_authenticated:
        favorites = Favoritess.objects.filter(user=request.user).values_list('tovar__id', flat=True)

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
        'selected_min_price': request.GET.get('min_price'),
        'selected_max_price': request.GET.get('max_price'),
        'selected_rating': min_rating or 0,
        'favorites': favorites if request.user.is_authenticated else [],
    }

    return render(request, 'search.html', context)

def filter_update(request):
    """ Динамическое обновление производителей и количества товаров """
    search_query = request.GET.get('search', '')
    selected_categories = request.GET.getlist('category[]')
    selected_avtors = request.GET.getlist('avtor[]')

    # Поиск всех товаров по запросу
    tovars_by_name = Tovars.objects.filter(name__icontains=search_query)
    tovars_with_char = search_tovars_by_characteristics(search_query)
    all_tov = list(set(tovars_by_name) | set(tovars_with_char))

    # Фильтрация товаров по выбранным категориям и производителям
    filtered_tov = all_tov
    if selected_categories:
        filtered_tov = [t for t in filtered_tov if t.category.slug in selected_categories]

    if selected_avtors:
        filtered_tov = [t for t in filtered_tov if t.avtor.slug in selected_avtors]

    # Логика для производителей:
    # Производители из выбранных категорий (даже если выбран один производитель)
    if selected_categories:
        updated_avtors = {t.avtor for t in all_tov if t.category.slug in selected_categories}
    else:
        updated_avtors = {t.avtor for t in filtered_tov}

    # Ответ в формате JSON (только производители и общее количество товаров)
    response_data = {
        'total_products': len(filtered_tov),
        'avtors': [{'slug': avtor.slug, 'name': avtor.avtor} for avtor in updated_avtors]
    }

    return JsonResponse(response_data)

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
def basket_add_del(request):
    """ Удаление и добавление в корзину """

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user = request.POST.get('User')
        tovar = request.POST.get('Tovar')
        data = {'check': 'ошибка'}
        
        try:
            user_obj = User.objects.get(username=user)
            tovar_obj = Tovars.objects.get(id=tovar)
        except (User.DoesNotExist, Tovars.DoesNotExist):
            return JsonResponse(data)

        basket_item = basket.objects.filter(user=user_obj, tovar=tovar_obj).first()
        
        if basket_item:
            basket_item.delete()
            data['check'] = 'удалён из'
        else:
            basket.objects.create(user=user_obj, tovar=tovar_obj, t_count=1)
            data['check'] = 'добавлен в'
        
        data['value'] = basket.objects.filter(user=user_obj).count()
        return JsonResponse(data, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def basket_count(request):
    """ добавление количества товаров """
    data = {'check': 'ошибка'}
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        t = request.POST.get('Tovar')
        c = int(request.POST.get('count'))
        tov = basket.objects.get(user=request.POST.get('User'), tovar__id=t)
        if c > 0 and c < 101:
            tov.t_count=c
            tov.save()
            data['check'] = 'добавлено'
            return JsonResponse(data)
        else:
            return JsonResponse({'error': 'Invalid request'}, status=400)
    else:   return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def basket_if_select(request):
    """ выбор товара """

    data = {'check': 'ошибка'}
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        u = request.POST.get('User')
        s = request.POST.get('Select').title()
        if_all = request.POST.get('if_all') == 'true'
        if if_all:  # Если запрос на выбор всех товаров
            query = basket.objects.filter(user__username=u)
            for q in query:
                q.if_select = s
                q.save()
        else:   # Если запрос на выбор одного товара
            t = request.POST.get('Tovar')
            b = basket.objects.get(user__username=u, tovar__id=t)
            b.if_select = s
            b.save()
        data['check'] = 'добавлено'
        return JsonResponse(data)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def add_order(request):
    """ Добавление в заказ """
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        spos = request.POST.get('Sposob')
        if spos == "Pochta": # если выбрана почта россии
            FCs = request.POST.get('FCs')
            if FCs and FCs[0] != ' ' and len(FCs) > 6 and 3 > FCs.count(" ") >= 1 and len(FCs) != FCs.rfind(" ")+1: # проверка ФИО
                address = request.POST.get('address') # адрес пользователя
                p_address = request.POST.get('postal-address') # адрес почтового отделения
                if not p_address or p_address[0] == ' ' or len(p_address) < 15: return JsonResponse({'code':'postal-address'}, status=400) # проверка адреса пользователя
                if not address or address[0] == ' ' or len(address) < 15: return JsonResponse({'code':'address'}, status=400) # проверка почтового адреса
            else:
                return JsonResponse({'code':'FCs'}, status=400)
                # JsonResponse({'error': 'Ошибка в ФИО','code':'FCs'}, status=400)
        elif spos == "pickup": # если выбран самовывоз
            coords = request.POST.get('coords-map')
            if not coords: return JsonResponse({'code':'coords'}, status=400)
        else: return JsonResponse({'error': 'Invalid request'}, status=400)

        card = request.POST.get('card-number')
        mm = request.POST.get('mm')
        yy = request.POST.get('yy')
        cvv = request.POST.get('cvv')
        if not card or 12 > len(card) > 20:  return JsonResponse({'code':'card'}, status=400)
        if not mm or 2 > len(mm) == 0 or mm == '0' or mm == '00':  return JsonResponse({'code':'mm'}, status=400)
        if not yy or 2 > len(yy) == 0:  return JsonResponse({'code':'yy'}, status=400)
        if not cvv or 3 > len(cvv) == 0:  return JsonResponse({'code':'cvv'}, status=400)

        us = request.user
        bask = basket.objects.filter(if_select=True, user=us)

        # if spos == "Pochta": print(f"{bask}\n Способ - {spos} \n ФИО - {FCs} \n адрес пользователя - {p_address} \n почтовый адрес - {address} \n \n Номер - {card} \n mm - {mm} \n yy - {yy} \n cvv - {cvv}")
        # else: print(f"{bask}\n Способ - {spos} \n Магазин - {coords} \n  \n Номер - {card} \n mm - {mm} \n yy - {yy} \n cvv - {cvv}")
        
        if bask:
            o_t = []
            for i in bask:
                t_cost = 0
                if i.tovar.skidka_cost: t_cost = i.tovar.skidka_cost
                else: t_cost = i.tovar.cost
                if order_tovars.objects.filter(tovar=i.tovar,t_count=i.t_count,user=us, t_cost=t_cost):
                    continue
                order_tovars.objects.create(
                    tovar=i.tovar,
                    t_count=i.t_count,
                    user=us,
                    t_cost=t_cost
                ).save()
            if spos == "Pochta": # если почта
                ordd = order.objects.create(
                    user = us,
                    dostavka = 'collect',
                    sposob_dostavka = spos,
                    adress = address,
                    adress_mail = p_address,
                    FCs = FCs,
                    card_number = card,
                    mm = mm,
                    yy = yy,
                    cvv = cvv
                )
            else: # если самовывоз
                ordd = order.objects.create(
                    user = us,
                    dostavka = 'collect',
                    sposob_dostavka = spos,
                    coords = coords,
                    card_number = card,
                    mm = mm,
                    yy = yy,
                    cvv = cvv
                )
            for i in bask:
                t_cost = 0
                if i.tovar.skidka_cost: t_cost = i.tovar.skidka_cost
                else: t_cost = i.tovar.cost
                ordd.tovar_order.add(order_tovars.objects.get(user=us, tovar=i.tovar, t_count=i.t_count, t_cost=t_cost))
            ordd.save()
            bask.delete()
        else:   return JsonResponse({'error': 'Invalid request'}, status=400)
        return JsonResponse({'error': 'Данные Добавлены'}, status=200)
    else:
        return JsonResponse({'error': 'Invalid request XMLH'}, status=400)

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

@login_required
def comm_add_edit(request):
    """ Добавление и изменение в комментариях """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        tovar_id = request.POST.get('Tovar')
        rating = request.POST.get('rating')
        text = request.POST.get('text')
        if not all([request.user, tovar_id, rating]): return JsonResponse({'error': 'Invalid request'}, status=400)

        tovar = get_object_or_404(Tovars, id=tovar_id)

        # Проверяем существует ли уже комментарий
        comment, created = comments.objects.get_or_create(
            user=request.user,
            tovar=tovar,
            defaults={
                'comment': text,
                'star': rating
            }
        )

        if not created:
            # Обновляем существующий комментарий
            comment.comment = text 
            comment.star = rating
            comment.save()

        return JsonResponse({'success': True}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def faq(request):
    """Render the FAQ page."""

    return render(request, 'faq.html')


# ajax

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

