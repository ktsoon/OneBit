// выбрать 1 товар в корзине
$('.ord-t-del').click(function () {
    const check = false;
    const id_t = $(this).attr('id')
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
        success: function(data){
            console.log($('.tov').length)
            if ($('.tov').length != 1){
                $('.tov#'+id_t).remove()
            }
            else{
                location.reload()
            }
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

