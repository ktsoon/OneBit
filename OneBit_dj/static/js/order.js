const sorting = new URLSearchParams(window.location.search).get("sorting") || 'all';
$('.uk-subnav-ord li').each(function() {
    if ($(this).hasClass('s-'+sorting)) {
        $(this).addClass('uk-active');
    }
});