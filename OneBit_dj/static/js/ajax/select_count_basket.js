// Добавить число товара в корзине
        $('.p-b-count input#inp_count').on('input change', function() {
            const id_t = $(this).attr('data-product')
            $.ajax({
                url: '/basket_count/',
                method: 'POST',
                headers: {
                      'Content-Type': 'application/x-www-form-urlencoded',
                      'X-Requested-With': 'XMLHttpRequest',
                      'X-CSRFToken': csrf_token
                  },
                data: {
                    'basket_id': id_t,
                    'count': $(this).val()
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