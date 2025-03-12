from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse # *JsonResponse - возвращает переменную json
from django.contrib.auth.decorators import login_required # перенос пользователя на страницу авторизации если он не вошол в профиль на определённой странице
from django.views.generic import DetailView # DetailView - просмотр одной записи по ключу.
from django.contrib import messages # вывод сообщения
from django.contrib.auth import login, authenticate, logout
from django.core.paginator import Paginator
from django.core.cache import cache
from .models import *
from .forms import *
# __icontains неработает с SQLlite
from django.db.models import Min, Max, Sum, F, Avg, Count, Q, ExpressionWrapper, FloatField

from OneBit_dj.settings import BASE_URL # для ссылок seo

import itertools # используется в profile

def char_add_tov(tov, count=5, basket=False):
    """ Создание словаря для хранения первых характеристик каждого товара """

    if basket:
        tovars_specs = {Tovars.objects.filter(id=tovar.tovar.id).annotate(rating=Avg('comments__star'), count_com=Count('comments'))[0]: list() for tovar in tov}
        specs_all = []
        for i in tov:
            for j in specs.objects.filter(tovar=i.tovar):
                specs_all.append(j)
    else:
        tovars_specs = {Tovars.objects.filter(id=tovar.id).annotate(rating=Avg('comments__star'), count_com=Count('comments'))[0]: list() for tovar in tov}
        specs_all = specs.objects.filter(tovar__in=tov)
    for spec in specs_all:
        if len(tovars_specs[spec.tovar]) < count:
            tovars_specs[spec.tovar].append(spec)
    return tovars_specs

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

def search_tovars_by_characteristics(search):
        """ Поиск товаров по характеристикам """
        tovars_with_char = []
        for char in specs.objects.all():
            similarity = fuzz.WRatio(char.description.lower(), search.lower())
            if similarity >= 81:  # Устанавливаем порог сходства
                # print(char.description, similarity)
                tovars_with_char.append(char.tovar)
        return tovars_with_char

title_list = [
        ['Недавно просмотреные'],
        ['Акции и скидки'],
        ['Популярные товары'],
        # ['Недавно просмотреные'],
        # ['Акции и скидки', '/pass'],
        # ['Популярные товары', '/pass'],
        # 'Рекомендуем для вас', (добавить) если пользователь авторизирован
    ]


def load_tovars(request):
    """
    Загружает товары постронично через AJAX
    """
    page = request.GET.get('page', 1) # - номер страницы, по умолчанию 1
    tovars_list = Tovars.objects.all()
    paginator = Paginator(tovars_list, 18)

    tovars = paginator.get_page(page)
    data = {
        'tovars': list(tovars.object_list.values('id', 'name', 'cost', 'skidka_cost', 'slug')),
        'has_next': tovars.has_next()
    }
    return JsonResponse(data)

def index(request):
    """ Главная """

    if not request.user.is_authenticated:
        cache.clear()

    tovars = Tovars.objects.all()

    favorites = []
    if request.user.is_authenticated:
        favorites = Favoritess.objects.filter(user=request.user).values_list('tovar__id', flat=True)
        history = History_tovars.objects.filter(user=request.user)[:20]
    
    t1 = title_list if request.user.is_authenticated and history.count() > 5 else title_list[1:]

    stocks = Tovars.objects.annotate(
        skidka_value=ExpressionWrapper(
            100 * (F('cost') - F('skidka_cost')) / F('cost'),
            output_field=FloatField()
        ),
        review_count_tovar=Count('comments'),
        rating_tovar=Avg('comments__star')
    ).order_by('-skidka_value', '-review_count_tovar', '-rating_tovar')[:20]

    context = {
        't1': t1,
        "stocks": stocks,
        "history": history,
        'favorites': list(favorites)
    }
    return render(request, 'index.html', context)

class productDetailView(DetailView):
    """ Товар """
    model = Tovars
    template_name = "product_index.html"
    context_object_name = 'tovar'

    # новые переменная
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        slug = self.kwargs['slug']
        user = self.request.user.id
        context["img_tovar_p"] = img_tovar.objects.filter(tovar__slug=slug) # картинки к товару
        context["seo_img"] = BASE_URL + context["img_tovar_p"].filter(is_video=False).first().img.url

        # характеритики {
        context["specs"] = specs.objects.filter(tovar__slug=slug).order_by('-category__gl_category','-category__category')
        A = []
        specs_gl = context["specs"]
        for i in specs_gl:
            A.append(i.category.gl_category)
        li = []
        for i in A:
            if i not in li:
                li.append(i)
        context["specs_gl"] = li
        # } /характеристики/

        # история просмотра
        if user:
            visite = history_tovars.objects.filter(user=user, tovar__slug=slug).count() # открывали ли товар до этого (0-нет 1-да)
            if visite == 0: # если user просматривает товар впервые
                history_tovars.objects.create(tovar=context["tovar"], user=self.request.user) # заносим в базу
            else: # если user уже просматривал этот товар до этого
                history_tovars.objects.get(user=user, tovar__slug=slug).delete() # удаляем из базы
                history_tovars.objects.create(tovar=context["tovar"], user=self.request.user) # и заносим заного, чтобы он сохранялся как последний просмотренный товар
        # /история просмотра/
        hist = history_tovars.objects.filter(user=user).count()
        if hist - 5 > 0: context['c_history'] = True

        # комментарии
        com = comments.objects.filter(tovar__slug=slug).order_by('-created_at')
        if com: 
            context['len_com'] = com.count()
            if self.request.user.is_authenticated:
                user_comments = com.filter(user=user)
                if user_comments: context['user_comments'] = True
                else: context['user_comments'] = False
                other_comments = com.filter(baned=False).exclude(user=user)
                com = list(user_comments) + list(other_comments)
            else:
                com = com.filter(baned=False)
            context['comments'] = com
            context['avg_star'] = str(comments.objects.aggregate(Avg('star'))['star__avg'])
        else: context['avg_star'] = 0
        if self.request.user.is_authenticated:
            context['if_buy'] = order.objects.filter(
                    dostavka='received', 
                    user_id=user,
                    tovar_order__tovar__slug=slug
                ).distinct().count()

        
        context['favorite'] = favoritess.objects.filter(user=user, tovar__slug=slug).count() # добавлен ли товар в избранное
        context['title'] = title_list[0]
        context['if_basket'] = basket.objects.filter(user=user, tovar__slug=slug).count()
        context["specs_tip"] = context["specs"].filter(category__category='Тип')
        return context

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

    from django.db.models import F, FloatField, ExpressionWrapper
    context={}
    sorting = request.GET.get('sorting')
    sorting_name = 'Сначала новые'
    user = request.user.id
    
    tovars = favoritess.objects.filter(user=user).select_related('tovar').annotate(
        skidka=ExpressionWrapper(
            100 * (F('tovar__cost') - F('tovar__skidka_cost')) / F('tovar__cost'),
            output_field=FloatField()
        )
    ).select_related('tovar').annotate(
        rating=Avg('tovar__comments__star'),         # Средний рейтинг товара
        count_com=Count('tovar__comments')           # Количество отзывов
    )
    if sorting == 'new' or not sorting:
        tovars = tovars.order_by('created_at')
    elif sorting == 'old':
        tovars = tovars.order_by('-created_at')
        sorting_name = 'Сначала старые'
    elif sorting == 'low':
        tovars = tovars.order_by('tovar__cost', 'tovar__skidka_cost')
        sorting_name = 'Сначала дешёвые'
    elif sorting == 'exp':
        tovars = tovars.order_by('-tovar__skidka_cost', '-tovar__cost')
        sorting_name = 'Сначала дорогие'


    favorites = favoritess.objects.filter(user=user).values_list('id', flat=True)
    context['favorites'] = list(favorites)

    context['tovars'] = tovars
    context["tovar_img"] = img_tovar.objects.all()
    context['sorting'] = sorting_name
    context['if_basket_all'] = [i.tovar.name for i in basket.objects.filter(user=request.user)]

    return render(request, 'favorites.html', context)

@login_required
def profile(request):
    """ Профиль пользователя """

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None
    context = {}
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)

    commented_tovars = comments.objects.filter(user_id=request.user).values_list('tovar', flat=True)
    # оставить комментарии для определённых товаров
    orders = order.objects.filter(
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
    # Выводим уникальные товары
    # print("\nУникальные товары:")
    # for tovar in unique_tovars:
    #     print(f"Товар: {tovar.tovar.name}, ID: {tovar.tovar.id}")
    
    context['form'] = form
    context['title'] = title_list[0]
    avatar = UserProfile.objects.filter(user=request.user)
    if avatar: context['avatar'] = avatar[0].avatar
    return render(request, 'profile.html', context)

def search_text(request):
    """ подсказки при вводе в поисковую строку """
    text = request.GET.get('text')
    payload = []
    data = {}
    if text:
        cat = fuzzy_search(text, Category, 'category')
        if not cat: cat = Category.objects.filter(category__icontains=text)
        avt = fuzzy_search(text, Avtor, 'avtor')
        if not avt: avt = Avtor.objects.filter(avtor__icontains=text)
        
        first_image_ids_all = img_tovar.objects.filter(is_video=False, tovar__name__icontains=text).values('tovar_id').annotate(first_image_id=Min('id'))
        first_image_ids = [record['first_image_id'] for record in first_image_ids_all]
        tovars_all = img_tovar.objects.filter(id__in=first_image_ids) # товары
        if not tovars_all: # если запрос не точный
            img_tovar_ids = img_tovar.objects.filter(is_video=False)
            filtered_results = []
            for result in img_tovar_ids:
                similarity = fuzz.WRatio(result.tovar.name.lower(), text.lower())
                if similarity >= 50:
                    filtered_results.append((result, similarity))
            # Сортируем результаты по убыванию сходства
            filtered_results.sort(key=lambda x: x[1], reverse=True)
            # Возвращаем только объекты модели
            tovars_all = [result[0] for result in filtered_results]
            filtered_results_t=[]
            filtered_results_v=''
            for x in tovars_all:
                if x.tovar.name != filtered_results_v:
                    filtered_results_t.append(x)
                    filtered_results_v = x.tovar.name
            tovars_all = filtered_results_t

        for tovar in cat:
            payload.append({
                'name': tovar.category,
                'slug': tovar.slug,
                'categ': 'cat',
                'gl_cat': tovar.Gl_category.Gl_category
                })
        for tovar in avt:
            if tovar.img:
                payload.append({
                    'name': tovar.avtor,
                    'slug': tovar.slug,
                    'categ': 'avt',
                    'img_url': tovar.img.url
                })
            else:
                payload.append({
                    'name': tovar.avtor,
                    'slug': tovar.slug,
                    'categ': 'avt',
                    'img': None
                })
        for tovar in tovars_all:
            payload.append({
                'name': tovar.tovar.name,
                'slug': tovar.tovar.slug,
                'categ': 'tovar',
                'img_url': tovar.img.url
                })

        data['status'] = 200
        data['search'] = payload
    return JsonResponse(data)

def search(request):
    """ страница с товарами по запросу (поиск) """
    context = {}
    search = request.GET.get('search')
    context['title'] = search
    print(search, search.isspace())
    if not search or search.isspace(): return redirect("home")
    if len(search) > 100: return redirect("home")
    request.session['text_search'] = search
    cat = fuzzy_search(search, Category, 'category', similarity_threshold=80, method='ratio')[:1]
    if cat: return redirect('category', cat_slug=cat[0].slug)

    avt = fuzzy_search(search, Avtor, 'avtor', similarity_threshold=80, method='ratio')[:1]
    if avt:
        context['avtor'] = avt[0]
        tov = Tovars.objects.filter(avtor=avt[0])
    else:
        # Поиск по названию товара
        tovars_by_name = Tovars.objects.filter(name__icontains=search)
        # Поиск по характеристикам
        tovars_with_char = search_tovars_by_characteristics(search)
        # Объединяем результаты поиска по названию и характеристикам
        tov = set(list(tovars_by_name) + list(tovars_with_char))
        if len(tov) == 1: return redirect('product', next(iter(tov)).slug) # если товар один то сразу перебрасывает на странуцу этого товара

    all_tovars = Tovars.objects.filter(id__in=[t.id for t in tov])  # Все найденные товары

    if not all_tovars.exists():
        context['tovars'] = []
        return render(request, 'search.html', context)
    
    # Определение мин/макс цены без фильтров (учёт skidka_cost)
    price_range = all_tovars.aggregate(
        min_price=Min('skidka_cost', default=Min('cost')),
        max_price=Max('skidka_cost', default=Max('cost'))
    )

    min_price_all = price_range['min_price'] or 0
    max_price_all = price_range['max_price'] or 0
    
    
    # Получение категорий и производителей только из найденных товаров
    available_categories = {t.category for t in tov}
    available_avtors = {t.avtor for t in tov}
    
    # Фильтрация товаров
    selected_categories = request.GET.getlist('category')
    selected_avtors = request.GET.getlist('avtor')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_rating = request.GET.get('rating')

    # Фильтр по категории
    if selected_categories:
        tov = [t for t in tov if str(t.category.slug) in selected_categories]
        # Обновляем список производителей, но **только из выбранной категории**
        available_avtors = {t.avtor for t in tov}
    
    # Фильтр по производителю
    if selected_avtors:
        tov = [t for t in tov if str(t.avtor.slug) in selected_avtors]
        # Обновляем список категорий, но **только из выбранных производителей**
        available_categories = {t.category for t in tov}


    if not selected_categories or selected_avtors:
        # Если производители не выбраны, показываем все категории
        available_categories = {t.category for t in all_tovars}
        available_avtors = {t.avtor for t in all_tovars}

    # Фильтр по цене
    if min_price:
        min_price = int(min_price)
        min_price = max(min_price, min_price_all)
        tov = [t for t in tov if (t.skidka_cost or t.cost) >= min_price]
    if max_price:
        max_price = int(max_price)
        max_price = min(max_price, max_price_all)
        tov = [t for t in tov if (t.skidka_cost or t.cost) <= max_price]

    # Фильтр по рейтингу
    if min_rating:
        min_rating = float(min_rating)
        tovars_with_high_rating = Tovars.objects.annotate(avg_rating=Avg('comments__star')).filter(avg_rating__gte=min_rating)
        tov = [t for t in tov if t in tovars_with_high_rating]

    # Сортировка (по умолчанию - по релевантности)
    sort_option = request.GET.get('sort')
    if sort_option == "low":
        tov = sorted(tov, key=lambda x: x.skidka_cost if x.skidka_cost else x.cost)
        sorting = "По убыванию цены"
    elif sort_option == "exp":
        tov = sorted(tov, key=lambda x: x.skidka_cost if x.skidka_cost else x.cost, reverse=True)
        sorting = "По возрастанию цены"
    elif sort_option == "new":
        tov = sorted(tov, key=lambda x: x.created_at, reverse=True)
        sorting = "По новинкам"
    elif not sort_option or sort_option == "pop":
        sorting = "По релевантности"

    # Пагинация
    paginator = Paginator(list(tov), 10)  # 10 товаров на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Избранное
    favorites = []
    if request.user.is_authenticated:
        favorites = favoritess.objects.filter(user=request.user).values_list('tovar__id', flat=True)
    context['favorites'] = favorites

    context.update({
        'tovars': char_add_tov(page_obj),
        'page_obj': page_obj,
        'sorting': sorting,
        'sort_option': sort_option,
        'categories': available_categories,
        'avtors': available_avtors,
        'min_price': price_range['min_price'],
        'max_price': price_range['max_price'],
        'selected_categories': selected_categories,
        'seo_category': Category.objects.filter(slug__in=selected_categories),
        'selected_avtors': selected_avtors,
        'selected_min_price': request.GET.get('min_price'),
        'selected_max_price': request.GET.get('max_price'),
        'selected_rating': min_rating or 0
    })
    print(context['selected_min_price'])
    if request.user.is_authenticated: context['if_basket_all'] = [i.tovar.name for i in basket.objects.filter(user=request.user)]
    return render(request, 'search.html', context)

def category(request, cat_slug):
    """ страница с товарами по запросу(или нет) с выбранной категорией (поиск) """
    context = {}
    cat = get_object_or_404(Category, slug=cat_slug) # Получаем категорию по slug или выдаем 404
    tov = Tovars.objects.filter(category=cat) # Получаем все товары в данной категории
    context['category'] = cat
    context['title'] = cat.category
    if not tov:
        context['tovars'] = []
        return render(request, 'search.html', context)
    # Получаем главную категорию
    gl_category = cat.Gl_category
    # Получаем все категории внутри этой главной категории
    related_categories = Category.objects.filter(Gl_category=gl_category)

    # Фильтрация товаров
    selected_avtors = request.GET.getlist('avtor')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_rating = request.GET.get('rating')
    
    selected_category = request.GET.get('category')
    if selected_category and selected_category != cat_slug:
        return redirect('category', cat_slug=selected_category)

    # Фильтр по производителю
    if selected_avtors:
        tov = tov.filter(avtor__slug__in=selected_avtors)

    # Фильтр по цене
    if min_price:
        min_price = int(min_price)
        tov = tov.filter(Q(skidka_cost__gte=min_price) | Q(cost__gte=min_price))
    
    if max_price:
        max_price = int(max_price)
        tov = tov.filter(Q(skidka_cost__lte=max_price) | Q(cost__lte=max_price))

    # Фильтр по рейтингу
    if min_rating:
        min_rating = float(min_rating)
        tov = tov.annotate(avg_rating=Avg('comments__star')).filter(avg_rating__gte=min_rating)

    # Получение доступных производителей (из найденных товаров)
    available_avtors = Avtor.objects.filter(tovars__in=tov).distinct()

    # Минимальная и максимальная цена среди найденных товаров
    price_range = tov.aggregate(
        min_price=Min('skidka_cost', default=Min('cost')),
        max_price=Max('cost')
    )


    # Сортировка (по умолчанию - по релевантности)
    sort_option = request.GET.get('sort', 'pop')
    if sort_option == "low":
        tov = tov.order_by('skidka_cost', 'cost')
        sorting = "По убыванию цены"
    elif sort_option == "exp":
        tov = tov.order_by('-skidka_cost', '-cost')
        sorting = "По возрастанию цены"
    elif sort_option == "new":
        tov = tov.order_by('-created_at')
        sorting = "По новинкам"
    else:
        tov = tov.annotate(review_count=Count('comments')).order_by('-review_count')
        sorting = "По релевантности"
    
    # Пагинация
    paginator = Paginator(tov, 10)  # 10 товаров на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Избранное
    favorites = []
    if request.user.is_authenticated:
        favorites = favoritess.objects.filter(user=request.user).values_list('tovar__id', flat=True)
    context['favorites'] = favorites

    context.update({
        'tovars': char_add_tov(page_obj),
        'page_obj': page_obj,
        'category': cat,
        'search': cat.category.lower(),
        'categories': related_categories,
        'avtors': available_avtors,
        'sorting': sorting,
        'sort_option': sort_option,
        'min_price': price_range['min_price'],
        'max_price': price_range['max_price'],
        'selected_avtors': selected_avtors,
        'selected_min_price': min_price or price_range['min_price'],
        'selected_max_price': max_price or price_range['max_price'],
        'selected_rating': min_rating or 0
    })
    if request.user.is_authenticated: context['if_basket_all'] = [i.tovar.name for i in basket.objects.filter(user=request.user)]
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

    tov = basket.objects.filter(user=request.user)
    tov_ids = tov.values_list('tovar', flat=True)
    tov_img = img_tovar.objects.filter(tovar__in = tov_ids, is_video=False)

    # Избранное
    favorites = []
    if request.user.is_authenticated:
        favorites = favoritess.objects.filter(user=request.user).values_list('tovar__id', flat=True)

    context['favorites'] = favorites
    context['tovars'] = char_add_tov(tov, basket=True)
    context['tovars_if_select'] = tov
    context['tovar_img'] = tov_img

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

    ord_tov = basket.objects.filter(user=request.user, if_select=True)
    if not ord_tov: return redirect("basket")
    context['tovars'] = ord_tov

    # img
    tov_ids = ord_tov.values_list('tovar', flat=True)
    tov_img = img_tovar.objects.filter(tovar__in = tov_ids, is_video=False)
    context['tovar_img'] = tov_img

    return render(request, 'order_confitmation.html', context)

@login_required
def orderr(request):
    """ Список заказов """
    context = {}
    us = request.user
    sorting = request.GET.get("sorting")
    
    ordd = order.objects.filter(user=us).annotate(
        total_price=Sum(F('tovar_order__t_count') * F('tovar_order__t_cost'))
        ).order_by('-date_update')
    
    if sorting:
        if sorting == 'act':
            ordd=ordd.filter(dostavka__in=['collect','goes','delivered'])
        if sorting == 'received':
            ordd=ordd.filter(dostavka='received')
        if sorting == 'cancelled':
            ordd=ordd.filter(dostavka='cancelled')


    context['order'] = ordd
    context['img'] = img_tovar.objects.filter(is_video=False)
    return render(request, "order.html", context)

@login_required
def order_details(request, order_number):
    """ Подробности заказа """

    context = {}

    ordd = order.objects.get(user=request.user, order_number=order_number)
    context['order'] = ordd
    context['img'] = img_tovar.objects.filter(is_video=False)

    context['results'] = order.objects.filter(user=request.user, order_number=order_number).aggregate(
        total_count=Sum('tovar_order__t_count'),
        total_cost=Sum(F('tovar_order__t_count') * F('tovar_order__t_cost')))
    
    # Избранное
    favorites = []
    if request.user.is_authenticated:
        favorites = favoritess.objects.filter(user=request.user).values_list('tovar__id', flat=True)
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