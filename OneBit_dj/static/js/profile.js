$(window).on('load', function() {
    var form = $('.fieldWrapper');
    form.find('a').replaceWith('<img src='+form.find('a').attr('href')+'>');
    form.find('.form_ava').attr('uk-form-custom', 'target: true')
    
    form = form.find('.form_ava')[0]
    var childNodesArray = Array.prototype.slice.call(form.childNodes);
    
    childNodesArray.forEach(function(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            
            form.removeChild(node);
        }
    });
   });

$(document).ready(function() {
    var inp = $('#id_avatar')
    inp.change(function(event) {
        var reader = new FileReader();

        reader.onload = function(e) {
            $('.form_ava img').attr('src', e.target.result);
            $('.form_ava img').show();
            $('.form_ava span').hide();
        };
        
        reader.readAsDataURL(event.target.files[0]);
        
    });
});


// повторное подтверждение при выходе
let clickCount = 0;
$('#exit').click(function() {
    const but = $('#exit_href');
    
    if (clickCount === 0) {
        but.find('span').text('Вы уверены?');
        clickCount++;
    } else {    window.location.href = but.attr('click_href')   }
});