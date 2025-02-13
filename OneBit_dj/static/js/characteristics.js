// Получаем все элементы с классом "char_gl"
var charGlDivs = document.querySelectorAll('.char_gl');
// Проходимся по каждому элементу с классом "char_gl"
charGlDivs.forEach(function(charGlDiv) {
    // Находим заголовок h3
    var h3 = charGlDiv.querySelector('h3');

    // Получаем все дочерние элементы div с классом "s-char-small", исключая заголовок h3
    var divs = Array.from(charGlDiv.querySelectorAll('.s-char-small')).filter(function(div) {
        return div !== h3;
    });

    // Создаем новый div для первой половины
    var firstHalfDiv = document.createElement('div');
    firstHalfDiv.classList.add('first-half');

    // Создаем новый div для второй половины
    var secondHalfDiv = document.createElement('div');
    secondHalfDiv.classList.add('second-half');

    // Вычисляем индекс, с которого начнется вторая половина
    var index = Math.ceil(divs.length / 2);

    // Добавляем первую половину элементов в первый div
    for (var i = 0; i < index; i++) {
        firstHalfDiv.appendChild(divs[i].cloneNode(true));
    }

    // Добавляем вторую половину элементов во второй div
    for (var j = index; j < divs.length; j++) {
        secondHalfDiv.appendChild(divs[j].cloneNode(true));
    }

    // Очищаем элемент "char_gl"
    charGlDiv.innerHTML = '';

    // Добавляем созданные div с половинами в элемент "char_gl" с учетом сохранения заголовка h3
    if (h3) {
        charGlDiv.appendChild(h3);
    }
    charGlDiv.appendChild(firstHalfDiv);
    charGlDiv.appendChild(secondHalfDiv);
});
