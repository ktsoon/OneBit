$(document).ready(function() {
    // Перебираем все элементы с классом "order"
    $('.order').each(function() {
        // Получаем значение атрибута data-dost
        let dataDost = $(this).data('dost');

        // Проверяем, содержит ли data-dost одно из указанных значений
        if (['collect', 'goes', 'delivered'].includes(dataDost)) {
            // Добавляем к значению "act"
            let newDataDost = dataDost + ' act';
            $(this).data('dost', newDataDost);

            // Также обновляем DOM-атрибут (если нужно для визуализации)
            $(this).attr('data-dost', newDataDost);
        }
    });
});
