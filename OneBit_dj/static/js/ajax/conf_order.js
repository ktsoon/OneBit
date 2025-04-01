function validateFullNameWithMessage(field) { // Функция для проверки ФИО
    const fullName = field.val().trim();
    
    if (fullName === "") {
        return "Поле ФИО не может быть пустым";
    }
    
    if (fullName.includes('  ')) {
        return "Между словами должен быть только один пробел";
    }
    
    const parts = fullName.split(' ');
    
    if (parts.length < 2 || parts.length > 3) {
        return "Введите Фамилию и Имя (Отчество не обязательно)";
    }
    
    for (let i = 0; i < parts.length; i++) {
        const part = parts[i];
        
        if (part.length < 3) {
            return "Каждая часть ФИО должна содержать минимум 3 буквы";
        }
        
        if (!/^[а-яА-ЯёЁ-]+$/.test(part)) {
            return "ФИО должно содержать только русские буквы";
        }
    }
    
    return null; // Нет ошибок
}

$('#basket_submit').click(function (e) {
    e.preventDefault();

    const P_form = $('#dadata-zipcode-form');
    P_form.find('input').removeClass('danger-bord');
    $('#map-right').removeClass('danger-map');

    let hasError = false;

    // Определяем способ оплаты
    let sposob = $('.sposob a[aria-selected="true"]').data('value');

    if (sposob === "Pochta") {
        let full_name = P_form.find('#name');
        let fullNameError = validateFullNameWithMessage(full_name);
        let address = P_form.find('#address-input');
        let postal_address = P_form.find('#postal-unit-address');

        if (fullNameError) {
            full_name.addClassAndRemove('danger-bord', 0, 500);
            $('.uk-text-danger').text(fullNameError);
            hasError = true;
        } else {
            $('.uk-text-danger').text('');
        }
        if (address.val().trim() === "") {
            address.addClassAndRemove('danger-bord', 0, 500);
            hasError = true;
        }
        if (postal_address.val().trim() === "") {
            postal_address.addClassAndRemove('danger-bord', 0, 500);
            hasError = true;
        }
    } 
    else if (sposob === "pickup") {
        let coords = $("#map-right > .map_adress_select > span > span");
        if (coords.text().trim() === "") {
            $('#map-right').addClassAndRemove('danger-map', 0, 500);
            hasError = true;
        }
    }

    // Валидация карты, если выбрана
    let c_n = $('#card-number');
    let mm = $('#expiry-mm');
    let yy = $('#expiry-yy');
    let cvv = $('#cvv');

    if ($('#card-hint').is(":visible") === true) {
        if (c_n.val().replace(/\s/g, "").length !== 16) {
            c_n.addClassAndRemove('danger-bord', 0, 500);
            hasError = true;
        }
        if (mm.val().length !== 2 || isNaN(mm.val()) || parseInt(mm.val()) < 1 || parseInt(mm.val()) > 12) {
            mm.addClassAndRemove('danger-bord', 0, 500);
            hasError = true;
        }
        if (yy.val().length !== 2 || isNaN(yy.val()) || parseInt(yy.val()) < 24) {
            yy.addClassAndRemove('danger-bord', 0, 500);
            hasError = true;
        }
        if (cvv.val().length !== 3 || isNaN(cvv.val())) {
            cvv.addClassAndRemove('danger-bord', 0, 500);
            hasError = true;
        }
    }

    if (hasError) {
        return;
    }

    $.ajax({
        url: '/add_order/',
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrf_token
        },
        data: {
            "Sposob": sposob,
            "FCs": P_form.find('#name').val(),
            "address": P_form.find('#address-input').val(),
            "postal-address": P_form.find('#postal-unit-address').val(),
            "coords-map": $("#map-right > .map_adress_select > span > span").text(),
        },
        success: function (data) {
            window.location.replace("/orderlist/");
        },
        error: function (xhr, status, error) {
            UIkit.notification({
                message: xhr.responseJSON.error || "Ошибка при оформлении заказа",
                status: 'danger'
            });
        }
    });
});
