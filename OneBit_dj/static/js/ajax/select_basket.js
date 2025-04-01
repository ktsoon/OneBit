// выбрать 1 товар в корзине
$('.tovar_b').click(function () {
    const check = this.checked;
    const id_t = $(this).attr('value')
    $.ajax({
        url: '/basket/select/',
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrf_token
        },
        data: {
            'check': check,
            'basket_id': id_t,
            'if_all': false
        },
        error: function(xhr, status, error){
            // Обработка ошибки
            UIkit.notification({
                message: 'Ошибка '+ error,
                status: 'danger'
                });
            console.error(id_t, 'Произошла ошибка:', error);
        }
    });
});
// выбрать все товары в корзине
$('#set_all').click(function () {
    const check = this.checked;
    $.ajax({
        url: '/basket/select/',
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrf_token
        },
        data: {
            'check': check,
            'if_all': true
        },
        error: function(xhr, status, error){
            // Обработка ошибки
            UIkit.notification({
                message: 'Ошибка '+ error,
                status: 'danger'
                });
            console.error('Произошла ошибка:', error);
        }
    });
});