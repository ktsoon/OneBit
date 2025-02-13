from django.contrib import admin
from django import forms
from django.utils.safestring import mark_safe
from django.contrib.admin.widgets import AdminFileWidget
from django.db import models

# from .forms import *
from .models import *

# Register your models here.

def image_preview(self): # используется в класе
    if self.img:
        return mark_safe('<img src="{0}" width="150" height="150" />'.format(self.img.url))
    else:
        return '(No image)'

class Img_tovar_Inline(admin.TabularInline): # вывод изображения в ТАБЛИЦЕ "Картинки к товару"
    """ Картинки к товару """

    model = img_tovar
    readonly_fields = (image_preview,)
    image_preview.short_description = "Изображение"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.reverse()  # Изменяем порядок на обратный
    
class characteristic_Inline(admin.TabularInline): # характеристики в форме товара
    """ Характеристики к товару """
    model = specs
    extra = 10

class TovarsAdminForm(forms.ModelForm): # условие чтобы Ценна со скидкой не была больше обычной цены и на вывод скидки в форме.
    skidka = forms.FloatField(label='Скидка (%)', required=False, disabled=True, help_text="не для заполнения")
    
    class Meta:
        model = Tovars
        fields = '__all__'

    def clean_skidka(self):
        # Поле skidka является вычисляемым и не требует очистки
        return self.cleaned_data['skidka']

    def clean(self): # условие чтобы Ценна со скидкой не была больше обычной цены.
        cleaned_data = super().clean()
        cost = cleaned_data.get('cost')
        skidka_cost = cleaned_data.get('skidka_cost')

        if cost is not None and skidka_cost is not None:
            if skidka_cost > cost:
                raise forms.ValidationError("Цена со скидкой не может быть больше обычной цены.")
        return cleaned_data

    def __init__(self, *args, **kwargs): # условие на вывод скидки в форме
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            if instance.cost and instance.skidka_cost:
                skidka_value = round((instance.cost - instance.skidka_cost) / instance.cost * 100)
                self.fields['skidka'].initial = skidka_value

@admin.register(Tovars) # Товары
class TovarsAdmin(admin.ModelAdmin):
    """ Товар """

    form = TovarsAdminForm # условие чтобы Ценна со скидкой не была больше обычной цены.

    list_display = ('name', 'category', 'avtor', 'cost', 'skidka', 'skidka_cost', 't_count')
    list_filter = ('category', 'avtor')
    list_editable = ['cost', 'skidka_cost']
    prepopulated_fields = { "slug": ("name",)}
    search_fields = ('name','slug')
    inlines = [Img_tovar_Inline, characteristic_Inline]

    def skidka(self, obj):
        if obj.cost and obj.skidka_cost:
            return f'{round((obj.cost - obj.skidka_cost) / obj.cost * 100)}%'
        return None

@admin.register(Gl_category) # Главные Категории
class Gl_categoryAdmin(admin.ModelAdmin):
    """ Главная Категория """

    list_display = ('Gl_category','slug')
    prepopulated_fields = { "slug": ("Gl_category",)}
    search_fields = ('Gl_category',)

@admin.register(Category) # Категория
class CategoryAdmin(admin.ModelAdmin):
    """ Категория """

    list_display = ('category', 'Gl_category','slug')
    prepopulated_fields = { "slug": ("category",)}
    search_fields = ('category',)
    list_filter = ('Gl_category',)

@admin.register(img_tovar) # Картинки к товару
class img_tovarAdmin(admin.ModelAdmin):
    """ Картинки к товару """

    list_display = ('tovar','get_id_tovar','get_img')
    search_fields = ('tovar',)
    readonly_fields = (image_preview,)

    def get_id_tovar(self, obj):
        return obj.tovar.id
    get_id_tovar.short_description = "id"

    def get_img(self, obj): # вывод изображения в ФОРМЕ "Картинки к товару"
        return mark_safe(f"<img src='{obj.img.url}' width=60 height=60 >")

    get_img.short_description = "Изображение"

@admin.register(Avtor) # Производители товара
class AvtorAdmin(admin.ModelAdmin):
    """ Производители товара """

    list_display = ('avtor', 'get_img', "slug")
    prepopulated_fields = { "slug": ("avtor",)}
    search_fields = ('avtor',)
    readonly_fields = (image_preview,)

    def get_img(self, obj):
        if obj.img:
            return mark_safe(f"<img src='{obj.img.url}' width=60 height=60 >")
        else:
            return '(No image)'
    get_img.short_description = "Изображение"

@admin.register(specs) # Характеристика к товару
class specsAdmin(admin.ModelAdmin):
    """ Характеристика к товару """

    list_display = ('tovar', 'category', 'description')
    list_filter = ('tovar',)
    search_fields = ('tovar', 'name')

@admin.register(detail) # Описание характеритики
class detailAdmin(admin.ModelAdmin):
    """ Описание характеритики """

    list_display = ('category', 'gl_category', 'details')
    list_filter = ('gl_category','cotegory_tovar',)
    ordering = ('cotegory_tovar', 'category')
    search_fields = ('category','gl_category')

@admin.register(favoritess) # Избранные
class favoritessAdmin(admin.ModelAdmin):
    """ Избранные """

    list_display = ('tovar', 'user', 'created_at')
    search_fields = ('tovar', 'user')
    list_filter = ('user',)

@admin.register(history_tovars) # история просмотра товаров
class history_tovarsAdmin(admin.ModelAdmin):
    """ история просмотра товаров """

    list_display = ('tovar', 'user', 'created_at')
    search_fields = ('tovar', 'user')
    list_filter = ('user',)

@admin.register(basket) # история просмотра товаров
class basketAdmin(admin.ModelAdmin):
    """ Корзина """

    list_display = ('tovar', 'user', 't_count','id')
    search_fields = ('tovar', 'user')
    list_filter = ('user',)

@admin.register(order_tovars) # заказы
class order_tovarsAdmin(admin.ModelAdmin):
    """ Товары заказов """

    list_display = ('tovar', 't_count')
    search_fields = ('tovar',)

@admin.register(order) # заказы
class orderAdmin(admin.ModelAdmin):
    """ Заказы """

    list_display = ('user', 'dostavka', 'sposob_dostavka', 'order_number')
    search_fields = ('tovar_order', 'user')
    list_filter = ('user', 'dostavka', 'sposob_dostavka')
    list_editable = ('dostavka',)

@admin.register(UserProfile) # заказы
class UserProfileAdmin(admin.ModelAdmin):
    """ Профиль пользователей """

    list_display = ('user', 'get_img')
    search_fields = ('user',)

    def get_img(self, obj):
        if obj.avatar:
            return mark_safe(f"<img src='{obj.avatar.url}' width=60 height=60 >")
        else:
            return '(No image)'
    get_img.short_description = "Изображение"

@admin.register(comments) # отзывы
class commentsAdmin(admin.ModelAdmin):
    """ Заказы """

    list_display = ('user', 'tovar', 'star', 'update_at', 'baned', 'baned_date', 'created_at')
    search_fields = ('tovar', 'user')
    list_filter = ('user', 'star', 'baned')

