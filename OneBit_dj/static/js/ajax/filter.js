function updateFilters() {
    let selectedCategories = $(".category-filter:checked").map(function() {
        return $(this).val();
    }).get();
    let selectedAvtors = $(".avtor-filter:checked").map(function() {
        return $(this).val();
    }).get();

    // Если нет выбранных категорий, передаём все доступные
    if (selectedCategories.length === 0) {
        selectedCategories = $(".category-filter").map(function() {
            return $(this).val();
        }).get();
    }

    $.ajax({
        url: "/search/filters/",
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrf_token
        },
        data: {
            'category[]': selectedCategories,
            'avtor[]': selectedAvtors
        },
        success: function(response) {
            updateAvtorList(response.avtors, selectedAvtors);
        }
    });
}


function updateAvtorList(avtors, selectedAvtors) {
    let avtorList = $("#avtor-list .nav-form");
    avtorList.empty();  // Очищаем текущий список производителей

    $.each(avtors, function(index, avtor) {
        avtorList.append(
            `<div class="uk-flex">
                <input class="uk-checkbox avtor-filter" type="checkbox" name="avtor" value="${avtor.slug}" id="${avtor.slug}"
                ${selectedAvtors.includes(avtor.slug) ? 'checked' : ''}>
                <label for="${avtor.slug}">${avtor.avtor}</label>
            </div>`
        );
    });
}
$(window).on("load", function() {
    updateFilters();
});

// При изменении фильтров обновляем производителей и количество товаров
$(document).on("change", ".category-filter, .avtor-filter", function() {
    updateFilters();
});