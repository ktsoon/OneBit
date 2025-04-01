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

$('.heart-clip').change(function() {
    var productId = $(this).data('product');

    $.ajax({
        url: '/favorite_check/',
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrf_token
        },
        data: {
            'Tovar': productId
        },
        success: function(data) {
            if_fav(data.count_favorite, 'count_favorites');
        },
        error: function(xhr, status, error) {
        UIkit.notification({
            message: 'Ошибка '+ error,
            status: 'danger'
            });
        }
    });
});