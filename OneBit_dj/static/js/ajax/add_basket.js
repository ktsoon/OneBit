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
function if_button(val, check){
    var div = val.find('div')
    if(!check){
        val.addClass("uk-button-onebit");
        div.replaceWith("<div>Добавить в&nbsp;корзину</div>")
    }
    else{
        val.removeClass("uk-button-onebit");
        div.replaceWith("<div>В&nbsp;корзине</div>")
    }
}
$('button#IntoBasket').click(function(){
    var $this = $(this);
    var baskId = $this.data('product');

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
            if_button($this, data.in_basket);
            if_fav(data.count_basket, 'count_basket');
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