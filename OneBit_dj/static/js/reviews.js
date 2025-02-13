$(document).ready(function () {
    $('.uk-comment-body').each(function () {
        const collapsible = $(this).find('.collapsible');
        const toggleButton = $(this).find('.toggle-button');

        // Проверяем, помещается ли текст в свернутом состоянии
        if (collapsible[0].scrollHeight <= parseInt(collapsible.css('max-height'))) {
            toggleButton.hide(); // Скрываем кнопку, если текст помещается
        }

        toggleButton.on('click', function () {
            const isExpanded = collapsible.hasClass('expanded');
            collapsible.toggleClass('expanded');
            $(this).text(isExpanded ? 'Читать далее' : 'Свернуть');
        });
    });

    // изменение кнопки в добавлении
    let rating = 0; // Переменная для хранения значения рейтинга
    let rating_ed = 0; // Переменная для хранения значения рейтинга
    // Инициализация rater-js
    raterJs({
        element: $("#rater_com_add").get(0),
        starSize: 33,
        step: 1,
        rating: 0, // Начальное значение рейтинга
        rateCallback: function (newRating, done) {
            this.setRating(newRating)
            rating = newRating; // Обновляем переменную с рейтингом
            updateButtonState_add(); // Обновляем состояние кнопки
            done(); // Завершаем действие
        }
    });

    let ret_ed = raterJs({
        element: $("#rater_com_edit").get(0),
        starSize: 33,
        step: 1,
        rating: 0, // Начальное значение рейтинга
        rateCallback: function (newRating, done) {
            this.setRating(newRating)
            rating_ed = newRating; // Обновляем переменную с рейтингом
            updateButtonState_edit(); // Обновляем состояние кнопки
            done(); // Завершаем действие
        }
    });

    // Обработчик для кнопки "Изменить"
    $('.but-edit').on('click', function () {
        const commentText = $(this).data('text');
        rating_ed = $(this).data('score');
        updateButtonState_edit()

        $('#comm_text_edit').val(commentText);
        ret_ed.setRating(rating_ed ? rating_ed : 0)
    });

    // Функция для обновления состояния кнопки
    function updateButtonState_add() {
        const button = $("#comm_add");
        if (rating > 0) {
            button.removeClass("but-dis").prop("disabled", false); // Активируем кнопку
        } else {
            button.addClass("but-dis").prop("disabled", true); // Отключаем кнопку
        }
    }
    // Функция для обновления состояния кнопки
    function updateButtonState_edit() {
        const button = $("#comm_edit");
        if (rating_ed > 0) {
            button.removeClass("but-dis").prop("disabled", false); // Активируем кнопку
        } else {
            button.addClass("but-dis").prop("disabled", true); // Отключаем кнопку
        }
    }


    // Первоначальная установка кнопки (на случай сброса модального окна)
    updateButtonState_add();
    updateButtonState_edit();
});