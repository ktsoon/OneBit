function if_fav(val, classes){
    if (val > 99) {
        document.getElementById(classes).innerHTML = '99+';
        document.getElementById(classes).style.display = "inline-flex";
      }
    else if (val != 0) {
        document.getElementById(classes).innerHTML = val;
        document.getElementById(classes).style.display = "inline-flex";
    }
    else{
        document.getElementById(classes).style.display = "none";
    }
}

function if_basket_clear_all(){
    $('#basket-container').html('Ваша корзина пуста.').addClass('clear_all');
    $('.cost1').text('0');
    $('.cost2').text('0');
    $('.itogi h4 sub').text('0');
    $('.select-bask #set_all').prop('checked', false);
    $('.select-bask').remove();
}

function deleteTovar(baskId){
    $('#bask-' + baskId).remove();
}

function deleteSelectedTovar(){
    $('.tovar_b:checked').each(function() {
        $(this).closest('.tovar-srch').remove();
    });
}

// удаление 1 товара из корзины
$('.uk-modal button#modal-del-tovar').click(function(){
    var baskId = $(this).attr('data-product');

    $.ajax({
        url: '/basket_add_del/',
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrf_token
        },
        data: {
            'Tovar': baskId,
            'list': false
        },
        success: function(data){
            if_fav(data.count_basket, 'count_basket');
            if (data.count_basket == 0) {
                if_basket_clear_all();
            }
            deleteTovar(baskId);
        },
        error: function(xhr, status, error){
            UIkit.notification({
                message: 'Ошибка '+ error,
                status: 'danger'
                });
            console.error(baskId, 'Произошла ошибка:', error);
        }
    });
});
// удаление выбранных товаров из корзины
$('.uk-modal button#modal-delete-selected').click(function(){
    $.ajax({
        url: '/basket_add_del/',
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrf_token
        },
        data: {
            'list': true
        },
        success: function(data){
            if_fav(data.count_basket, 'count_basket');
            deleteSelectedTovar();
            if (data.count_basket == 0) {
                if_basket_clear_all();
            }
            
        },
        error: function(xhr, status, error){
            UIkit.notification({
                message: 'Ошибка '+ error,
                status: 'danger'
                });
            console.error(baskId, 'Произошла ошибка:', error);
        }
    });
});