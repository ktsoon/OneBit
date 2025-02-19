// HvrSlider: небольше 5
var tImgDivs = document.querySelectorAll('div.t-img');
// --------------HvrSlider--------------
class HvrSlider {
  constructor(selector) {
    const elements = document.querySelectorAll(selector);
    elements.forEach((el) => {
      if (el.querySelectorAll('img').length > 1) {
        const hvr = document.createElement('div');
        hvr.classList.add('hvr');

        const hvrImages = document.createElement('div');
        hvrImages.classList.add('hvr__images');
        hvr.appendChild(hvrImages);

        const hvrSectors = document.createElement('div');
        hvrSectors.classList.add('hvr__sectors');
        hvrImages.appendChild(hvrSectors);

        const hvrDots = document.createElement('div');
        hvrDots.classList.add('hvr__dots');
        hvr.appendChild(hvrDots);

        el.parentNode.insertBefore(hvr, el);
        hvrImages.prepend(el);

        const hvrImagesArray = hvr.querySelectorAll('img');
        hvrImagesArray.forEach(() => {
          hvrSectors.insertAdjacentHTML('afterbegin', '<div class="hvr__sector"></div>');
          hvrDots.insertAdjacentHTML('afterbegin', '<div class="hvr__dot"></div>');
        });
        hvrDots.firstChild.classList.add('hvr__dot--active');

        const setActiveEl = function (targetEl) {
          const index = [...hvrSectors.children].indexOf(targetEl);
          hvrImagesArray.forEach((img, idx) => {
            if (index == idx) {
              img.style.display = 'block';
            } else {
              img.style.display = 'none';
            }
          });
          hvr.querySelectorAll('.hvr__dot').forEach((dot, idx) => {
            if (index == idx) {
              dot.classList.add('hvr__dot--active');
            } else {
              dot.classList.remove('hvr__dot--active');
            }
          });
        };

        const resetToFirstImage = function () {
          setActiveEl(hvrSectors.firstElementChild);
        };

        hvrSectors.addEventListener('mouseover', function (e) {
          if (e.target.matches('.hvr__sector')) {
            setActiveEl(e.target);
          }
        });

        hvrSectors.addEventListener('touchmove', function (e) {
          const position = e.changedTouches[0];
          const target = document.elementFromPoint(position.clientX, position.clientY);
          if (target.matches('.hvr__sector')) {
            setActiveEl(target);
          }
        }, { passive: true });

        hvrSectors.addEventListener('mouseleave', resetToFirstImage);
      }
    });
  }
}

if (window.matchMedia('(min-width: 768px)').matches) {
  new HvrSlider('.images');
}




window.addEventListener('DOMContentLoaded', function() {
  // Функция для добавления атрибутов
  function addUkSticky() {
      // Получаем ширину окна
      var windowWidth = window.innerWidth;

      // Проверяем ширину окна
      if (windowWidth < 700) {
          // Получаем элементы
          var hRightElements = document.querySelectorAll('div.h_right');
          var catalogElements = document.querySelectorAll('div.catalog');

          // Атрибут, который нужно добавить
          var ukStickyValue = "position: bottom; end: !body; show-on-up: true; animation: uk-animation-slide-bottom";

          // Добавляем атрибут ко всем найденным элементам с классом h_right
          hRightElements.forEach(function(element) {
              element.setAttribute('uk-sticky', ukStickyValue);
          });

          // Добавляем атрибут ко всем найденным элементам с классом catalog
          catalogElements.forEach(function(element) {
              element.setAttribute('uk-sticky', ukStickyValue);
          });
      }
  }

  // Удаление выпадающего списка при max-width: 700px
  var dropdownDiv = document.querySelector('.uk-dropdown');
  var mq = window.matchMedia('(max-width: 700px)');

  // Удаление и изменение классов для слайдера при max-width: 700px
  const ulElements = document.querySelectorAll('ul.uk-slider');
  const maxWidth = 700;

  function removeClasses(element) {
      element.removeAttribute('class');
      if (window.innerWidth > maxWidth) {
          element.classList.add('uk-slider', 'uk-slider-items', 'uk-grid-small');
      } else {
          element.classList.add('slider-i');
      }
  }

  function handleResize() {
      ulElements.forEach((element) => {
          removeClasses(element);
      });
      addUkSticky(); // Проверяем и добавляем атрибуты при изменении размера окна
  }

  // handleWidthChange(mq); // Проверяем ширину при загрузке страницы
  handleResize(); // Проверяем и добавляем атрибуты при загрузке страницы
  window.addEventListener('resize', handleResize); // Проверяем и добавляем атрибуты при изменении размера окна


});

// category
function closeDrop(button) {
  // Находим родительский uk-drop
  const dropElement = button.closest(".drop-min-category");
  if (dropElement) {
    const drop = UIkit.drop(dropElement); // Получаем объект drop
    console.log(drop)
    drop.hide(0); // Закрываем через UIkit API
  }
}


// кнопка очистить
document.getElementById('clear-button').addEventListener('click', () => {
  document.getElementById('text-input').value = '';
});




