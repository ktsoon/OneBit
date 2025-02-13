window.addEventListener('DOMContentLoaded', function() {
    var pScore = document.getElementById('p-score');
    var svg = document.querySelector('.p-t-star svg');

    if (pScore && svg) {
        var score = parseFloat(pScore.textContent);
        if (score < 4.0) {
            svg.querySelector('path').setAttribute('fill', '#c5c5c5');
        }
    }
});