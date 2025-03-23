let slideIndex = 0;
showSlides();

const paginationImages = document.querySelectorAll('.pagination img, .pagination video');
paginationImages.forEach((media, index) => {
  media.addEventListener('click', () => {
    currentSlide(index);
  });
});

function showSlides() {
  const slides = document.querySelectorAll(".slide img, .slide video");
  const div_slides = document.querySelectorAll(".slide");
  const mainImageContainer = document.querySelector(".main-image");
  mainImageContainer.innerHTML = ""; // Очистить контейнер

  const currentSlide = slides[slideIndex];
  let mainMedia;

  if (currentSlide.tagName.toLowerCase() === 'video') {
    mainMedia = document.createElement('video');
    const source = document.createElement('source');
    source.src = currentSlide.src;
    mainMedia.appendChild(source);
    mainMedia.setAttribute('controls', ''); // Добавляем атрибут controls
    mainImageContainer.appendChild(mainMedia);
  } else {
    const link = document.createElement('a');
    // Убираем "_thumbnail" из URL изображения
    const imageUrl = currentSlide.src.replace('_thumbnail', '');

    // Проверяем ширину экрана
    if (window.innerWidth > 700) {
      link.href = imageUrl; // Добавляем href только при ширине экрана больше 700px
    }

    mainMedia = document.createElement('img');
    mainMedia.src = imageUrl; // Используем измененный URL
    mainMedia.alt = currentSlide.alt;

    // Добавляем класс uk-transition-scale-up только при ширине экрана больше 700px
    if (window.innerWidth > 700) {
      mainMedia.classList.add('uk-transition-scale-up', 'uk-transition-opaque');
    } else {
      mainMedia.classList.add('uk-transition-opaque'); // Добавляем только uk-transition-opaque
    }

    link.appendChild(mainMedia);
    mainImageContainer.appendChild(link);
  }

  // Убираем uk-lightbox при ширине экрана 700px и меньше
  if (window.innerWidth <= 700) {
    mainImageContainer.removeAttribute('uk-lightbox');
  } else {
    mainImageContainer.setAttribute('uk-lightbox', '');
  }

  for (let i = 0; i < slides.length; i++) {
    slides[i].classList.remove("active");
    div_slides[i].classList.remove("act");
  }
  currentSlide.classList.add("active");
  div_slides[slideIndex].classList.add("act");
}

function currentSlide(index) {
  slideIndex = index;
  showSlides();
}

// -------------------------------------------------------------------------------------------------------

const slider = document.getElementById('pagination');
const slides = document.querySelectorAll('.slide');
const prevButton = document.querySelector('.prev');
const nextButton = document.querySelector('.next');
const countSliderDownSTOP = 5.125;

const slideHeight = slides[0].offsetHeight + 5; // Получаем высоту каждого слайда
const numSlides = slides.length; // Получаем количество слайдов
let slideIndexx = 0;

if (numSlides <= 5) {
  document.getElementById('bottomSlider').style.display = 'none';
} else {
  slider.style.marginTop = '22px';
  document.querySelector('.pagg').style.marginTop = '10px';
}

function showSlide(index) {
  if (index < 0) {
    slideIndexx = 0; // Если мы на первом слайде и пытаемся пролистать назад, остаемся на первом слайде
  } else if (index >= numSlides - countSliderDownSTOP) {
    slideIndexx = numSlides - countSliderDownSTOP; // Если мы на последнем слайде и пытаемся пролистать вперед, остаемся на последнем слайде
  }
  const maxTranslateY = (numSlides - 1) * slideHeight; // Максимальное значение translateY
  const translateY = Math.min(slideIndexx * slideHeight, maxTranslateY); // Устанавливаем translateY, но не больше максимального значения
  slider.style.transform = `translateY(-${translateY}px)`;
}

prevButton.addEventListener('click', () => {
  slideIndexx--; // Перелистываем на один слайд вверх
  showSlide(slideIndexx);
});

nextButton.addEventListener('click', () => {
  slideIndexx++; // Перелистываем на один слайд вниз
  showSlide(slideIndexx);
});

slider.addEventListener('wheel', event => {
  event.preventDefault();
  if (event.deltaY > 0) {
    slideIndexx++; // Перелистываем на один слайд вниз
  } else {
    slideIndexx--; // Перелистываем на один слайд вверх
  }
  showSlide(slideIndexx);
});