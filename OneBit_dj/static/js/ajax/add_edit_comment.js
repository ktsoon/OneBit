// добавление комментария
$('#comm_add').click(function(e){
    e.preventDefault()
    const tovar_id = +$('input#tovar_id').val()
    const rating = $('#rater_com_add').attr('data-rating')
    if (!rating){
        $('#rater_com_add').addClassAndRemove('uk-animation-shake',0,500);
        return;
    }
    const text = $('#comm_text_add').val()
    $.ajax({
        url: '/product_comm/',
        method: 'POST', // Метод запроса
        headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrf_token
            },
        data: {
            'tovar_id': tovar_id,
            'rating': rating,
            'text': text
        },
        success: function(data){
            location.reload();
            UIkit.modal(document.getElementById('add-comment-modal')).hide();
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

// редактирование комментариев
$('#comm_edit').click(function(e){
    e.preventDefault()
    const tovar_id = $('input#tovar_id').val()
    const rating = $('#rater_com_edit').attr('data-rating')
    if (!rating){
        $('#rater_com_edit').addClassAndRemove('uk-animation-shake',0,500);
        return;
    }
    const text = $('#comm_text_edit').val()
    $.ajax({
        url: '/product_comm/',
        method: 'POST', // Метод запроса
        headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrf_token
            },
        data: {
            'tovar_id': tovar_id,
            'rating': rating,
            'text': text
        },
        success: function(data){
            // Обработка успешного ответа от сервера
            location.reload();
            UIkit.modal(document.getElementById('edit-comment-modal')).hide();
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