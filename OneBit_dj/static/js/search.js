$(document).ready(function() {

    // фильтр
    function formatPrice(input) {
        let value = input.val().replace(/\s+/g, ''); // Убираем пробелы перед форматированием
        if (!$.isNumeric(value)) return;
        let formatted = parseInt(value).toLocaleString('ru-RU'); // Добавляем пробелы
        input.val(formatted);
    }
    // Форматируем цену во время ввода
    $("#cost-ot, #cost-do").on("input", function() {
        formatPrice($(this));
    });
    // Проверка после потери фокуса
    $("#cost-ot, #cost-do").on("blur", function() {
        let fromVal = parseInt($("#cost-ot").val().replace(/\s+/g, '')) || minPrice;
        let toVal = parseInt($("#cost-do").val().replace(/\s+/g, '')) || maxPrice;

        if (fromVal > toVal) {
            $("#cost-ot").val(toVal.toLocaleString('ru-RU'));
        }
        if (toVal > maxPrice) {
            $("#cost-do").val(maxPrice.toLocaleString('ru-RU'));
        }
        if (fromVal < minPrice) {
            $("#cost-ot").val(minPrice.toLocaleString('ru-RU'));
        }
    });
    // Перед отправкой формы удаляем пробелы в input
    $("form").on("submit", function() {
        $("#cost-ot").val($("#cost-ot").val().replace(/\s+/g, ''));
        $("#cost-do").val($("#cost-do").val().replace(/\s+/g, ''));
    });


    // Функция для перемещения .cost и .t-b-info в .t-t-rght > a
    function moveCostAndTInfoToTTRight() {
    $('.tovar-srch').each(function() {
        var $cost = $(this).find('.cost');
        var $tBInfo = $(this).find('.t-b-info');
        var $tTRightA = $(this).find('.t-t-rght > a');
        
        if ($cost.length && $tBInfo.length && $tTRightA.length) {
        $tTRightA.append($cost); // Перемещаем .cost в .t-t-rght > a
        $tTRightA.append($tBInfo); // Перемещаем .t-b-info в .t-t-rght > a
        }
    });
    }

    // Проверка ширины окна при изменении размера
    $(window).resize(function() {
    if ($(window).width() <= 600) {
        moveCostAndTInfoToTTRight();
    }
    });

    // Начальная проверка
    if ($(window).width() <= 600) {
    moveCostAndTInfoToTTRight();
    }


});