$(document).ready(function() {
    function checkAllCheckboxesOnLoad() {
        var allChecked = $('.tovar_b').length > 0 && $('.tovar_b:checked').length === $('.tovar_b').length;
        $('#set_all').prop('checked', allChecked);
    }
    // Проверяем выбранны ли все товары, для выбора общего чекбокса
    checkAllCheckboxesOnLoad();
    
    
    // общий ценик
    function updateTotals() {
        var selectedCount = 0;
        var totalNormalCost = 0;
        var totalSkidkaCost = 0;

        var dostavka = $('#dostavka');
        var zakaz = $('#zakaz');
        var button_z = zakaz.find('button');
        if ($('.tovar_b:checked').length == 0) {
            dostavka.hide();
            zakaz.find('hr').hide();
            zakaz.find('.itogi').hide();
            button_z.removeClass('uk-button-onebit');
            button_z.addClass('dis_but');
            button_z.prop("disabled", true);
            button_z.text('Выберите товары');
        } else {
            dostavka.show();
            zakaz.find('hr').show();
            zakaz.find('.itogi').show();
            button_z.addClass('uk-button-onebit');
            button_z.removeClass('dis_but');
            button_z.prop("disabled", false);
            button_z.text('Заказать');
        }

        $('.tovar_b:checked').each(function() {
            selectedCount++;
            var $parent = $(this).closest('.tovar-srch');
            var normalCost = parseInt($parent.find('#n-cost').text().replace(/\s/g, '').replace(/&nbsp;/g, ''));
            var skidkaCost = parseInt($parent.find('#s-cost').text().replace(/\s/g, '').replace(/&nbsp;/g, ''));
            var quantity = parseInt($parent.find('input[type="number"]').val()) || 1;

            totalNormalCost += (isNaN(normalCost) ? 0 : normalCost) * quantity;
            totalSkidkaCost += (isNaN(skidkaCost) ? 0 : skidkaCost) * quantity;
        });

        $('.itogi h4 sub').text(selectedCount);

        function animateValue($element, start, end, duration) {
            $element.prop('Counter', start).animate({
                Counter: end
            }, {
                duration: duration,
                easing: 'easeOutQuad',
                step: function(now) {
                    $element.text(Math.ceil(now).toLocaleString().replace(/,/g, '&nbsp;'));
                }
            });
        }

        var currentCost1 = parseInt($('.cost1').text().replace(/\s/g, '').replace(/&nbsp;/g, '')) || 0;
        var currentCost2 = parseInt($('.cost2').text().replace(/\s/g, '').replace(/&nbsp;/g, '')) || 0;

        animateValue($('.cost1'), currentCost1, totalNormalCost, 300);
        animateValue($('.cost2'), currentCost2, totalSkidkaCost, 300);

        if (totalSkidkaCost === 0) {
            setTimeout(function() { $('.cost2').hide() }, 300);
        } else {
            $('.cost2').show();
        }
    }

    $("#set_all").change(function () {
        $('.tovar_b').prop('checked', this.checked);
        updateTotals();
    });

    $('.tovar_b').change(function () {
        if ($('.tovar_b:checked').length == $('.tovar_b').length) {
            $('#set_all').prop('checked', true);
        } else {
            $('#set_all').prop('checked', false);
        }
        updateTotals();
    });

    $('.p-b-count .uk-b-minus, .p-b-count .uk-b-plus').on('click', function() {
        var $input = $(this).siblings('input[type="number"]');
        $input.trigger('input'); // Триггерим событие input
    });

    // Добавляем обработчик события для изменения количества товаров
    $('input[name="tov_count"]').on('input', function() {
        updateTotals();
    });

    updateTotals();



    // удаление сразу нескольких из корзины
    function updateModalItemList(){
        var itemList = $('#modal-close-default-ch ul');
        itemList.empty(); // Очистка списка

        $('.tovar_b:checked').each(function() {
            var $parent = $(this).closest('.tovar-srch');
            var itemName = $parent.find('.t-cntr-name').text().trim();
            var itemImgSrc = $parent.find('.images img').attr('src');

            // Создание нового элемента списка
            var listItem = `
                <li>
                    <img src="${itemImgSrc}" alt="${itemName}">
                    <span class="uk-margin-small-left">${itemName}</span>
                </li>
            `;
            itemList.append(listItem); // Добавление элемента в список
        });
    }
    $('#delete-selected').on('click', function() {
        if ($('.tovar_b:checked').length === 0){
            UIkit.notification({message: 'Выберите хотя бы один товар для удаления!', status: 'warning'}); // Уведомление
        } else {
            updateModalItemList();
            UIkit.modal('#modal-close-default-ch').show(); // Открытие модального окна
        }
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


    // uk-sticky bottom
    function forceStickyUpdate() {
        UIkit.update(); // Принудительно обновляем UIkit, чтобы он пересчитал позиционирование
    }

    // Отслеживание изменений внутри .right-bar (изменение высоты)
    var observer = new MutationObserver(function () {
        forceStickyUpdate();
    });

    observer.observe($('.right-bar')[0], { childList: true, subtree: true, attributes: true });

    updateSticky(); // Вызываем при загрузке
    $(window).on('resize', updateSticky); // Отслеживаем изменение размера экрана

});
// uk-sticky bottom
function updateSticky() {
    if ($(window).width() <= 700) {
        $('.right-bar .uk-card').attr('uk-sticky', 'position: bottom; end: !body; offset: -70; show-on-up: true; animation: uk-animation-slide-bottom');
        UIkit.sticky(inactive, '.right-bar')
        UIkit.sticky('.right-bar .uk-card'); // Обновляем поведение
    }else if ($(window).width() <= 1220) {
        $('.right-bar .uk-card').attr('uk-sticky', 'position: bottom; end: !main; animation: uk-animation-slide-bottom');
        UIkit.sticky(inactive, '.right-bar')
        UIkit.sticky('.right-bar .uk-card'); // Обновляем поведение
    }else {
        $('.right-bar').attr('uk-sticky', 'end: !.main; offset: 20');
        UIkit.sticky(inactive, '.right-bar .uk-card')
        UIkit.sticky('.right-bar'); // Обновляем поведение
    }
}

updateSticky(); // Вызываем при загрузке
$(window).on('resize', updateSticky); // Отслеживаем изменение размера экрана
