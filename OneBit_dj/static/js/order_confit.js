const token = "124d0bec66bbc42ff87b17214441e149e0f3fe95";

$("#address-input").suggestions({
    token: token, // API-ключ DaData
    type: "ADDRESS", // Тип подсказок
    count: 5, // Количество подсказок
    onSelect: function (suggestion) {
        // Проверка качества геокодирования
        console.log(suggestion.data.qc_geo)
        if (suggestion.data.qc_geo <= 4) {
        // Получение почтового индекса из подсказки
        const postalCode = suggestion.data.postal_code;

        if (postalCode) {
            $('#dadata-error').hide()
            // URL для API DaData для почтовых отделений
            const url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/postal_unit";

            // Опции запроса
            const options = {
                method: "POST",
                mode: "cors",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": "Token " + token
                },
                body: JSON.stringify({ query: postalCode })
            };

            // Выполнение запроса для получения данных о почтовом отделении
            fetch(url, options)
                .then(response => response.json())
                .then(data => {
                    if (data.suggestions && data.suggestions.length > 0) {
                        const unit = data.suggestions[0].data;
                        console.log(unit)

                        // Обновление информации на странице
                        $("#postal-unit-address").val(unit.address_str+', '+unit.postal_code || "Неизвестно");
                        $('#postal-unit-address').attr('data-postal_code', postalCode)
                        if (unit.is_closed) {
                            $('#dadata-error').show().text("Почтовое отделение закрыто. Введите другой адрес");
                        } else{
                            $('#dadata-error').hide()
                        }
                    } else {
                        // Если данных нет
                        $("#postal-unit-address").val("");
                        $('#dadata-error').hide()
                    }
                })
                .catch(error => console.log("Ошибка запроса:", error));
        } else {
            // Если индекс не найден
            $("#postal-unit-address").val("");
            $('#dadata-error').show().text("Почтовое отделение не найдено. Введите другой адрес");
        }
    } else {
        $('#dadata-error').show().text("Укажите более точный адрес");
    }
    }
});

// select dostavka
$(document).ready(function () {
    $('.sposob a').on('click', function () {
        // Убираем класс name у всех ссылок
        $('.sposob a').removeClass('select_d');

        // Добавляем класс name к выбранной ссылке
        $(this).addClass('select_d');

        // Активируем соответствующий скрытый input
        const value = $(this).data('value');
        $(`#${value}`).prop('checked', true);
    });
});
 
// Yandex map

// Массив магазинов
const stores = [
    { name: "<b>Адрес:</b> <span>Ярославская область, Ростов, Пролетарская улица, 86</span>", coords: [57.193864, 39.443892] },
    { name: "<b>Адрес:</b> <span>Москва, Красная площадь, 1</span>", coords: [55.755825, 37.617298] },
    { name: "<b>Адрес:</b> <span>Москва, Тверская улица, 19</span>", coords: [55.765432, 37.603456] },
    { name: "<b>Адрес:</b> <span>Москва, Смоленский бульвар, 19с2</span>", coords: [55.742867, 37.582645] },
    { name: "<b>Адрес:</b> <span>Свердловская область, Екатеринбург, проспект Ленина, 35</span>", coords: [56.838926, 60.605702] },
    { name: "<b>Адрес:</b> <span>Челябинск, Артиллерийская улица, 117/2</span>", coords: [55.164442, 61.436843] },
    { name: "<b>Адрес:</b> <span>Республика Башкортостан, Уфа, улица 50-летия Октября, 15</span>", coords: [54.738764, 55.972055] }
];
// добавляем блоки справа
const mapRight = document.getElementById('map-right');
stores.forEach(store => {
    // Создаем новый блок с классами
    const mapAdress = document.createElement('div');
    mapAdress.classList.add('map_adress');
    // Добавляем data-coords с нужными координатами
    mapAdress.setAttribute('data-coords', JSON.stringify(store.coords));
    
    // Создаем элемент span с адресом
    const span = document.createElement('span');
    span.innerHTML = store.name;

    // Вставляем span в блок
    mapAdress.appendChild(span);

    // Добавляем новый блок в контейнер
    mapRight.appendChild(mapAdress);
});

// Инициализация карты
ymaps.ready(() => {
    const map = new ymaps.Map("map", {
        center: [55.755825, 37.617298],
        zoom: 5,
        controls: ['zoomControl', 'typeSelector']
    });

    // Создаем кластеризатор
    const clusterer = new ymaps.Clusterer({
        preset: 'islands#invertedVioletClusterIcons',
        clusterDisableClickZoom: false,
        clusterOpenBalloonOnClick: true
    });

    const placemarks = stores.map((store, index) => {
        const placemark = new ymaps.Placemark(store.coords, {
            hintContent: store.name,
        }, {
            iconLayout: 'default#image',
            iconImageHref: pic,
            iconImageSize: [30, 42],
            iconImageOffset: [-15, -42]
        });

        // Событие клика на метке
        placemark.events.add('click', () => {
            // Удаляем активный класс у всех адресов
            document.querySelectorAll('.map_adress').forEach(el => el.classList.remove('map_adress_select'));
            // Добавляем активный класс соответствующему блоку
            const addressBlock = document.querySelector(`.map_adress[data-coords='${JSON.stringify(store.coords)}']`);
            if (addressBlock) {
                addressBlock.classList.add('map_adress_select');
                // Прокручиваем контейнер .map_right
                const container = document.querySelector('.map_right');
                const blockTop = addressBlock.offsetTop; // Позиция блока относительно контейнера

                container.scrollTo({
                    top: blockTop - container.offsetTop,
                    behavior: 'smooth'
                });
            }
        });

        return placemark;
    });

    // Добавляем метки в кластеризатор
    clusterer.add(placemarks);

    // Добавляем кластеризатор на карту
    map.geoObjects.add(clusterer);

    // Событие клика на адресе
    document.querySelectorAll('.map_adress').forEach(block => {
        block.addEventListener('click', () => {
            // Удаляем активный класс у всех адресов
            document.querySelectorAll('.map_adress').forEach(el => el.classList.remove('map_adress_select'));
            // Добавляем активный класс текущему блоку
            block.classList.add('map_adress_select');

            // Центруем карту на соответствующей метке
            const coords = JSON.parse(block.dataset.coords);
            map.setCenter(coords, 14); // Центрируем карту
        });
    });
});


// вывод банковской карты в зависимости от номера карты
$(document).ready(function () {
    const defaultImages = `
        <img src="${DJANGO_STATIC_URL}/mir.png">
        <img src="${DJANGO_STATIC_URL}/visa.png">
        <img src="${DJANGO_STATIC_URL}/mastercard.png">
        <img src="${DJANGO_STATIC_URL}/maestro.png">
        <img src="${DJANGO_STATIC_URL}/jcb.png">
        <img src="${DJANGO_STATIC_URL}/amex.png">
    `;

    function updateCardImages(images) {
        const $container = $('.card_img > div');
        $container.html(images);

        // Добавляем или удаляем класс в зависимости от количества изображений
        if ($container.find('img').length === 1) {
            $container.addClass('one_card_img');
        } else {
            $container.removeClass('one_card_img');
        }
    }

    $('#card-number').on('input', function () {
        let $input = $(this);
        let number = $input.val().replace(/[^\d]/g, ''); // Удаляем всё, кроме цифр
        $input.val(number); // Применяем только цифры обратно в поле
        let result = $input.validateCreditCard(); // Проверяем карту
        let cardType = result.card_type;

        if (number === '') {
            // Поле пустое
            // $('#card-hint').text('Введите номер карты.').css('color', 'gray');
            updateCardImages(defaultImages);
            return;
        }

        if (cardType) {
            // Определён тип карты
            let maxLength = Math.max(...cardType.valid_length);

            // Обрезаем лишние символы
            if (number.length > maxLength) {
                number = number.slice(0, maxLength);
            }
            $input.data('text', number)
            // Форматируем с пробелами
            let formatted = number.replace(/(\d{4})(?=\d)/g, '$1 ');

            // Обновляем значение поля
            $input.val(formatted);

            // Обновляем подсказку
            $('#card-hint').addClass('opacity');
            $input.removeClass('danger-red');

            // Меняем изображение карты
            updateCardImages(`
                <img src="${DJANGO_STATIC_URL}/${cardType.name.toLowerCase()}.png" alt="${cardType.name}">
            `);
            if (number.length < 12) {
                // анимация подсказки
                $('#card-hint')
                .removeClass('uk-animation-slide-top uk-animation-reverse opacity')
                .addClass('uk-animation-slide-top');
                $input.addClass('danger-red');
                // Обновляем подсказку
                $('#card-hint').text('Номер карты слишком короткий.').css('color', 'red');
            }
        } else {
            // Тип карты не определён
            if (number.length > 19) {
                number = number.slice(0, 19);
            }
            
            // Форматируем с пробелами
            let formatted = number.replace(/(\d{4})(?=\d)/g, '$1 ');
            $input.val(formatted);

            // анимация подсказки
            $('#card-hint')
            .removeClass('uk-animation-slide-top uk-animation-reverse opacity')
            .addClass('uk-animation-slide-top');
            $input.addClass('danger-red');
            // Обновляем подсказку
            $('#card-hint').text('Введите корректный номер карты.').css('color', 'red');

            // Возвращаем исходные изображения
            updateCardImages(defaultImages);
        }
    });
    $('#expiry-mm, #expiry-yy').focus('input', function () { 
        let $this=$(this);
        if (!$this.val()) $this.addClass('danger-red');
    });

    // Обработка срока действия
    $('#expiry-mm, #expiry-yy').on('input', function () {
        let $this = $(this);
        let value = $this.val().replace(/[^\d]/g, ''); // Удаляем всё, кроме цифр
        const date = new Date();
        const Year = date.getFullYear() % 100;
        const Month = date.getMonth() + 1;
        const maxYear = Year + 7; // Максимальный срок действия карты (7 лет)


        // Проверка для месяца
        if ($this.attr('id') === 'expiry-mm') {
            if (value > 12) value = '12';
            console.log(value,value == '1')
            if (value == '0' || !value || value == '') value = '0'
            if (value == '0' || !value || value == '' || value == '00') $this.addClass('danger-red')
                else $this.removeClass('danger-red')
        }
        // Проверка для года
        if ($this.attr('id') === 'expiry-yy') {
            if (value > maxYear) value = maxYear; // Максимальный год — через 7 лет
            if (value < Year || !$this.val()) $this.addClass('danger-red'); // Минимальный год
            else $this.removeClass('danger-red');
            
            // Если месяц уже введён и меньше текущего при текущем годе, корректируем месяц
            const enteredMonth = parseInt($('#expiry-mm').val(), 10);
            if (value == Year && enteredMonth < Month) {
                $('#expiry-mm').val(Month); // Устанавливаем минимальный месяц
            }
        }

        // Автоматическое добавление и удаление ведущего нуля
        if (value.length === 1) {
            value = '0' + value; // Добавляем ноль, если одна цифра
        } else if ((value.length === 2 || value.length === 3) && value.startsWith('0')) {
            value = value.replace(/^0/, ''); // Убираем ноль, если введена вторая цифра
        }

        // Ограничение длины
        if (value.length > 2) value = value.slice(0, 2);

        $this.val(value);
    });

    // Обработка CVV
    $('#cvv').focus('input', $(this).addClass('danger-red'));
    $('#cvv').on('input', function () {
        let $this = $(this);
        $this.addClass('danger-red');
        let value = $this.val().replace(/[^\d]/g, ''); // Только цифры
        if (value.length >= 3){
            value = value.slice(0, 3); // Максимум 3 цифры
            $this.removeClass('danger-red')
        }
        else $this.addClass('danger-red');
        $this.val(value);
    });
});


// сумма товаров
$(document).ready(function () {
    let totalCost = 0; // Итоговая стоимость товаров с учетом скидки
    let totalOriginalCost = 0; // Итоговая первоначальная стоимость товаров
    let totalCount = 0; // Общее количество всех товаров

    // Проходим по всем товарам
    $('#product-container .tov').each(function () {
        const $product = $(this);

        // Получаем количество товара
        const countText = $product.find('.count-t span').text();
        const count = parseInt(countText.match(/\d+/)[0]); // Извлекаем число из строки, например, "1 шт."

        // Получаем стоимость с учетом скидки
        const costWithDiscount = parseInt($product.find('[data-cost]').data('cost'));

        // Получаем первоначальную стоимость или подставляем costWithDiscount, если data-bes-skidkoi отсутствует
        const originalCost = $product.find('[data-bes-skidkoi]').length > 0
            ? parseInt($product.find('[data-bes-skidkoi]').data('bes-skidkoi'))
            : costWithDiscount;

        // Добавляем в общие значения
        totalCost += costWithDiscount * count;
        totalOriginalCost += originalCost * count;
        totalCount += count;
    });

    // Добавляем рассчитанные значения в HTML
    const $itogi = $('.itogi');
    $('.uk-h1 sup').text(totalCount);
    $itogi.find('sub').text(totalCount); // Устанавливаем общее количество товаров
    $itogi.find('.cost1').text(totalCost.toLocaleString()); // Устанавливаем стоимость со скидкой
    $itogi.find('.cost2').text(totalOriginalCost.toLocaleString()); // Устанавливаем первоначальную стоимость
});



// uk-sticky bottom

// Отслеживание изменений внутри .right-bar (изменение высоты)
var observer = new MutationObserver(function () {
    observer.disconnect();
    updateSticky();
});

observer.observe($('.right-bar')[0], { childList: true, subtree: true, attributes: true });

function updateSticky() {
    if ($(window).width() <= 700) {
        $('.right-bar').attr('uk-sticky', 'position: bottom; end: !body; offset: -70; show-on-up: true; animation: uk-animation-slide-bottom');
    } else if ($(window).width() <= 1220) {
        $('.right-bar').attr('uk-sticky', 'position: bottom; end: !.content_2');
    } else {
        $('.right-bar').attr('uk-sticky', 'end: !.content_2; offset: 20');
    }
    UIkit.update('.right-bar'); // Обновляем только .right-bar
}

updateSticky(); // Вызываем один раз при загрузке

