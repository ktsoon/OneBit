from django.db import models
from django.urls import reverse
from django.core.validators import FileExtensionValidator
from django.db.models import Avg
from datetime import datetime
from django.contrib.auth.models import User

from ckeditor.fields import RichTextField # описание товара

from django.core.validators import MaxValueValidator, MinValueValidator

from django.core.files.storage import default_storage
from django.dispatch import receiver
from django.db.models.signals import pre_delete
from django.core.files.base import ContentFile
from PIL import Image
import os

""" путь сохранения картинок к производителям """
def img_avtor(instance, fullname):  return f'static/img/Avtor/{instance.avtor.id}/{fullname}'

""" путь сохранения картинок к товару """
def img_tovar(instance, fullname):  return f'static/img/tovar/{instance.tovar.slug}/{fullname}'

""" путь сохранения аватарок пользователя """
def img_users(instance, fullname):  return f'static/img/users/{instance.user.id}/{fullname}'


""" -----------------migrate----------------- """
# python manage.py makemigrations
# python manage.py migrate

class UserProfile(models.Model):
    """ Профиль пользователя """

    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    avatar = models.ImageField("Аватарка", upload_to=img_users, null=True, blank=False)

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профиль пользователей"

    def __str__(self):
        return self.user.username

    def get_absolute_url(self):
        return reverse("UserProfile_detail", kwargs={"pk": self.pk})

class Tovars(models.Model):
    """ Товары """
    
    name = models.CharField("Название", max_length=255, blank=False, help_text="Введите название товара (без названия категории)")
    slug = models.SlugField("URL", max_length=255, unique=True, db_index=True, help_text="если ошибка: поля повторяются. то измениете поле")
    category = models.ForeignKey("Category", verbose_name='Категория', on_delete=models.CASCADE, blank=False, help_text="Выберите категорию", related_name="tovars")
    avtor = models.ForeignKey("Avtor", verbose_name='Производитель', on_delete=models.PROTECT, help_text="Выберите Производителя товара")
    cost = models.DecimalField("Цена", blank=False, max_digits=12, decimal_places=2)
    skidka_cost = models.DecimalField("Цена со скидкой", null=True, blank=True, help_text="можно оставить пустым", max_digits=12, decimal_places=2)
    descr = RichTextField("Описание", max_length=2000, blank=True, null=True, default=None, help_text="Описание товара")
    t_count = models.PositiveIntegerField("Количество товаров", default=99, validators=[MinValueValidator(1), MaxValueValidator(10000)])
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)

    @property
    def rating(self):
        """Возвращает средний рейтинг товара."""
        return self.comments.aggregate(Avg("star"))["star__avg"] or 0
    
    @property
    def review_count(self):
        """Возвращает количество отзывов."""
        return self.comments.count()
    
    @property
    def skidka(self):
        """Возвращает процент скидки."""
        if self.skidka_cost:
            return round(100 * (self.cost - self.skidka_cost) / self.cost)
        return 0
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product", kwargs={"slug": self.slug})

class Gl_category(models.Model):
    """ Главные Категории """

    Gl_category = models.CharField("Главная категория", max_length=120, unique=True, db_index=True, help_text="Введите название главной категории")
    slug = models.SlugField("URL", max_length=255, unique=True, db_index=True, help_text="если ошибка: поля повторяются. то измениете поле")
    seo = models.TextField("SEO")

    class Meta:
        verbose_name = "Главная категория"
        verbose_name_plural = "Главные категории"

    def __str__(self):
        return self.Gl_category

    def get_absolute_url(self):
        return reverse("Gl_category_detail", kwargs={"pk": self.pk})

class Category(models.Model):
    """ Категории """

    Gl_category = models.ForeignKey(Gl_category, verbose_name="Главная категория", null=True, on_delete=models.CASCADE)
    category = models.CharField("Категория", max_length=120, db_index=True, unique=True, help_text="Введите название категории")
    slug = models.SlugField("URL", max_length=255, unique=True, db_index=True, help_text="если ошибка: поля повторяются. то измениете поле")
    seo = models.TextField("SEO")
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.category

    def get_absolute_url(self):
        return reverse("Category_detail", kwargs={"pk": self.pk})

class ImgTovar(models.Model):
    """ Картинки к товарам """

    tovar = models.ForeignKey(Tovars, on_delete=models.CASCADE, help_text="Выберите товар", related_name="images")
    img = models.FileField("Картинка или видео", upload_to=img_tovar, null=True, blank=False, validators=[FileExtensionValidator(allowed_extensions=['jpg','jpeg','jfif','pjpeg','pjp','png','svg','webp','gif','avi','flv','mp4','mpg'])])
    is_video = models.BooleanField("Видео", default=False, help_text="ставиться автомитически. если нет, то поставте")  # Поле для определения, является ли файл видео

    def save(self, *args, **kwargs):
        # Проверяем, является ли файл видео
        if self.img.name.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
            self.is_video = True  # Устанавливаем галочку автоматически
        else:
            self.is_video = False  # Сбрасываем, если это не видео

        super().save(*args, **kwargs)

        if not self.is_video:
            self.create_resized_images()

    def create_resized_images(self):
        """Создает три версии изображения: миниатюру, среднее и оригинал."""
        img_path = self.img.path
        try:
            img = Image.open(img_path)
            sizes = {
                "thumbnail": (150, 150),
                "medium": (400, 400),
            }

            for size_name, max_size in sizes.items():
                img_resized = img.copy()
                img_resized.thumbnail(max_size)

                file_root, file_ext = os.path.splitext(self.img.name)
                new_filename = f"{file_root}_{size_name}{file_ext}"

                temp_file = ContentFile(b"")
                img_resized.save(temp_file, format=img.format)
                default_storage.save(new_filename, temp_file)
        except Exception as e:
            print(f"Ошибка обработки изображения: {e}")  # Логируем ошибку, но не прерываем сохранение

    def get_image_url(self, size="original"):
        """Возвращает URL для нужного размера изображения."""
        if size == "original":
            return self.img.url
        file_root, file_ext = os.path.splitext(self.img.url)
        return f"{file_root}_{size}{file_ext}"
    
    @property
    def thumbnail_url(self):
        """Миниатюра (150x150)"""
        return self.get_image_url("thumbnail")

    @property
    def medium_url(self):
        """Средний размер (400x400)"""
        return self.get_image_url("medium")

    @property
    def original_url(self):
        """Полное изображение"""
        return self.get_image_url("original")
    
    def delete_files(self):
        """Удаляет все файлы изображений при удалении записи."""
        if self.img:
            file_root, file_ext = os.path.splitext(self.img.path)
            for size in ["thumbnail", "medium", "original"]:
                file_path = f"{file_root}_{size}{file_ext}" if size != "original" else self.img.path
                if os.path.exists(file_path):
                    os.remove(file_path)

    class Meta:
        verbose_name = "Картинка к товару"
        verbose_name_plural = "Картинки к товарам"

    def __str__(self):
        return f"Изображение {self.tovar.name}"
    
@receiver(pre_delete, sender=ImgTovar)
def delete_tovar_images(sender, instance, **kwargs):
    """Удаляет файлы изображений перед удалением записи."""
    instance.delete_files()

class Avtor(models.Model):
    """ Производитель товара """

    avtor = models.CharField("Производитель", max_length=50, help_text="Введите производителя товара")
    img = models.ImageField("Картинка", upload_to = img_avtor, max_length=None, blank=True, null=True)
    slug = models.SlugField("URL", max_length=255, unique=True, db_index=True, help_text="если ошибка: поля повторяются. то измениете поле")
    seo = models.TextField("SEO", help_text="Можете добавить ключевые слова (без дублирования названия производителя)")

    class Meta:
        verbose_name = "Производитель"
        verbose_name_plural = "Производители"

    def __str__(self):
        return self.avtor

    def get_absolute_url(self):
        return reverse("Avtor_detail", kwargs={"pk": self.pk})

class Detail(models.Model):
    """ Описание характеритики """

    gl_category = models.CharField("Категория xарактеристики", max_length=50, null=True, help_text="Введите категорию характеристики")
    category = models.CharField("Характеристика", max_length=50, help_text="Введите характеристику")
    details = models.TextField("Описание характерискики", null=True, blank=True, help_text="Описание характеристики (не обязательно)")
    cotegory_tovar = models.ManyToManyField(Category, blank=True, verbose_name="Категория товара")

    class Meta:
        verbose_name = "Описание характеритики"
        verbose_name_plural = "Описание характеритики"

    def __str__(self):
        categories = self.cotegory_tovar.all().values('category').order_by('category')
        if not categories:
            return f"{self.category} - Все"
        if len(categories) == 1:
            return f"{self.category} - {categories[0]['category']}"
        return f"{self.category} - {', '.join(category['category'] for category in categories)}"

class Specs(models.Model):
    """ Характеристики к товару """

    tovar = models.ForeignKey(Tovars, on_delete=models.CASCADE, db_index=True, help_text="Выберите товар")
    category = models.ForeignKey(Detail, verbose_name="Характеристика", on_delete=models.CASCADE, help_text="Выберите характеристику к товару")
    description = models.TextField("Значение", help_text="Введите значение характеристики к товару")

    class Meta:
        verbose_name = "Характеристику к товару"
        verbose_name_plural = "Характеристики к товару"

    def __str__(self):
        return self.category.gl_category

class Favoritess(models.Model):
    """ Избранные товары """

    tovar = models.ForeignKey(Tovars, verbose_name="Товар", on_delete=models.CASCADE)
    user  = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name="Дата добавления", auto_now_add=True, null=True)

    class Meta:
        verbose_name = "Избранный товар"
        verbose_name_plural = "Избранные товары"
        unique_together = ('tovar', 'user')

    def __str__(self):
        return self.tovar.name

class History_tovars(models.Model):
    """ История просмотра товаров """
    
    tovar = models.ForeignKey(Tovars, verbose_name="Товар", on_delete=models.CASCADE)
    user  = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name="Дата просмотра товара", auto_now_add=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "История просмотра товаров"
        verbose_name_plural = "Истории просмотров товаров"

    def __str__(self):
        return f'{self.tovar} {self.user} {self.created_at}'

class Basket(models.Model):
    """ Корзина """

    tovar = models.ForeignKey(Tovars, on_delete=models.CASCADE, db_index=True, help_text="Выберите товар")
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)
    t_count = models.PositiveIntegerField("Количество", default=1, validators=[MinValueValidator(1), MaxValueValidator(100)])
    if_select = models.BooleanField("Выбран ли товар", default=False)

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

    def __str__(self):
        return f'Товар {self.tovar} для пользователя {self.user}'

class Order_tovars(models.Model):
    """ Товары заказов """

    tovar = models.ForeignKey(Tovars, on_delete=models.CASCADE, db_index=True, help_text="Выберите товар")
    t_count = models.PositiveIntegerField("Количество", default=1, validators=[MinValueValidator(1), MaxValueValidator(100)])
    t_cost = models.IntegerField("Цена", blank=False)
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Товар заказа"
        verbose_name_plural = "Товары заказов"

    def __str__(self):
        return self.tovar.name

class Order(models.Model):
    """ Заказ """

    get_dostavka=[
        ('collect', 'Проверяется'),
        ('goes', 'Достовляется'),
        ('delivered', 'Доставлен'),
        ('received', 'Получен'),
        ('cancelled', 'Отменён')]
    get_sposob_dostavka =[
        ('pickup','Самовывоз'),
        ('Pochta','Почта Росси')]
    
    order_number = models.CharField('Индификатор',max_length=25, unique=True, editable=False)
    
    tovar_order = models.ManyToManyField(Order_tovars, blank=True, verbose_name="Товары заказа")
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)

    dostavka = models.CharField("Доставка", max_length=9, choices=get_dostavka)
    sposob_dostavka = models.CharField("Способ доставки", max_length=9, choices=get_sposob_dostavka)
    
    adress = models.CharField("Адрес пользователя", max_length=550, blank=True, null=True, help_text='Если способ доставки \"Почта России\"')
    adress_mail = models.CharField("Адрес почтового отделения", max_length=550, blank=True, null=True, help_text='Если способ доставки \"Почта России\"')
    FCs = models.CharField("ФИО", max_length=250, blank=True, null=True, help_text='Если способ доставки \"Почта России\"')
    track_numbers = models.CharField("трек-номера", max_length=14, blank=True, null=True, help_text='Если способ доставки \"Почта России\"',) # 14 el

    coords = models.CharField("Координаты магазина", max_length=250, blank=True, null=True, help_text='Если способ доставки \"Самовывоз\"')

    card_number = models.CharField("Номер карты", max_length=19)
    mm = models.PositiveIntegerField("Месяц карты", validators=[MinValueValidator(1),MaxValueValidator(12)])
    yy = models.PositiveIntegerField("Год карты", validators=[MinValueValidator(1),MaxValueValidator(99)])
    cvv = models.CharField("CVV", max_length=3)
    date = models.DateTimeField("Дата заказа", auto_now=False, auto_now_add=True)
    date_update = models.DateTimeField("Дата доставки/отмены", auto_now=True)

    errors = models.CharField("Описать ошибку", max_length=250, default=None, null=True, blank=True, help_text="Если возникла ошибка, то опишите её пользователю")
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Получаем дату и время в нужном формате
            date_part = datetime.now().strftime('%Y%m%d')  # Год, месяц, день (например, 20250118)
            time_part = datetime.now().strftime('%H%M%S')  # Часы, минуты, секунды (например, 223512)
            # Получаем ID текущего объекта (сначала None, но после сохранения ID будет доступен)
            next_id = order.objects.count() + 1
            # Формируем order_number
            self.order_number = f"{date_part}-{time_part}-{next_id}"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return self.user.username

class Comments(models.Model):
    """ Отзывы """
    
    tovar = models.ForeignKey(Tovars, on_delete=models.CASCADE, help_text="Выберите товар", related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField("Коментарий", max_length=3000, null=True, blank=True)
    star = models.PositiveIntegerField("Оценка", validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    update_at = models.DateTimeField(verbose_name="Дата изменения", auto_now=True)
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Комметарий товара"
        verbose_name_plural = "Комметарии товаров"

    def __str__(self):
        return self.user.get_username()


