// blank blocks
// HTML-код для добавления
const tovarHTML = `
<div class="blank-tovar">
    <div class="blank-img">
        <svg width="100%" height="200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Placeholder" preserveAspectRatio="xMidYMid slice" focusable="false">
            <title>Placeholder</title>
            <rect width="100%" height="100%" fill="#868e96"></rect>
        </svg>
    </div>
    <div class="blank-cost">
        <span class="blank-placeholder blank-glow blank-placeholder-big"></span>
        <span class="blank-placeholder blank-glow"></span>
    </div>
    <div class="blank-header">
        <span class="blank-placeholder blank-glow blank-placeholder-big"></span>
        <span class="blank-placeholder blank-glow blank-placeholder-big"></span>
    </div>
    <div class="blank-info">
        <svg class="blank-placeholder" xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 16 15" fill="none">
            <path d="M7.04894 0.92705C7.3483 0.00573921 8.6517 0.00573969 8.95106 0.92705L10.0206 4.21885C10.1545 4.63087 10.5385 4.90983 10.9717 4.90983H14.4329C15.4016 4.90983 15.8044 6.14945 15.0207 6.71885L12.2205 8.75329C11.87 9.00793 11.7234 9.4593 11.8572 9.87132L12.9268 13.1631C13.2261 14.0844 12.1717 14.8506 11.388 14.2812L8.58778 12.2467C8.2373 11.9921 7.7627 11.9921 7.41221 12.2467L4.61204 14.2812C3.82833 14.8506 2.77385 14.0844 3.0732 13.1631L4.14277 9.87132C4.27665 9.4593 4.12999 9.00793 3.7795 8.75329L0.979333 6.71885C0.195619 6.14945 0.598395 4.90983 1.56712 4.90983H5.02832C5.46154 4.90983 5.8455 4.63087 5.97937 4.21885L7.04894 0.92705Z" fill="#FFB800" />
        </svg>
        <span class="blank-placeholder blank-glow" style="width: 10%"></span>
        <img class="blank-placeholder" src="/static/img/icon-aktuelles.png" width="17" alt="комментарии">
        <span class="blank-placeholder blank-glow" style="width: 30%"></span>
    </div>
</div>
`;

// Находим контейнер
const tovarsContainer = document.querySelector('.tovars-flex');

if (tovarsContainer) {
    // Получаем текущее значение grid-template-columns
    const gridStyle = window.getComputedStyle(tovarsContainer);
    const gridTemplateColumns = gridStyle.gridTemplateColumns;

    // Считаем количество колонок
    const columnCount = gridTemplateColumns.split(' ').length;

    // Вставляем столько блоков, сколько колонок
    tovarsContainer.innerHTML = tovarHTML.repeat(columnCount);
}




document.addEventListener("DOMContentLoaded", function () {
    let page = 1;
    let isLoading = false;
    const container = document.getElementById("tovars-container");

    if (!container) {
        console.error("Ошибка: Контейнер товаров не найден!");
        return;
    }

    function loadTovars() {
        if (isLoading) return;
        isLoading = true;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 секунд таймаут

        fetch(`/load_tovars/?page=${page}`, { signal: controller.signal })
            .then(response => response.json())
            .then(data => {
                clearTimeout(timeoutId);
                if (!data.tovars.length) return;

                document.querySelectorAll(".blank-tovar").forEach(el => el.remove()); // Убираем заглушки

                data.tovars.forEach(tovar => {
                    const tovarElement = document.createElement("div");
                    tovarElement.classList.add("tovar");

                    let imagesHTML = tovar.images.length
                        ? `<div class="t-img images">
                               ${tovar.images.map(img => `<img src="${img}" alt="${tovar.slug}">`).join('')}
                           </div>`
                        : "";

                    tovarElement.innerHTML = `
                        <a href="/product/${tovar.slug}" target="_blank" class="but-heart-div">
                            ${imagesHTML}
                        ${tovar.is_favorite === false || tovar.is_favorite === true ? `
                            <div class="but-heart but-heart-tovar">
                                <input
                                    type="checkbox"
                                    class="heart-clip"
                                    data-product="${tovar.id}"
                                    ${tovar.is_favorite ? "checked" : ""}
                                >
                                <svg class="heart-main" viewBox="0 0 512 512" width="25" title="heart">
                                    <path d="M462.3 62.6C407.5 15.9 326 24.3 275.7 76.2L256 96.5l-19.7-20.3C186.1 24.3 104.5 15.9 49.7 62.6c-62.8 53.6-66.1 149.8-9.9 207.9l193.5 199.8c12.5 12.9 32.8 12.9 45.3 0l193.5-199.8c56.3-58.1 53-154.3-9.8-207.9z" />
                                </svg>
                            </div>` : ''}
                            ${tovar.skidka ? `
                                <div class="skidka">
                                    <span>-${tovar.skidka}</span>
                                </div>` : ""}
                        </a>
                        <div class="t-bottom">
                            <a href="/product/${tovar.slug}" target="_blank">
                                <div class="cost">
                                    ${tovar.skidka_cost ? `<span>${tovar.skidka_cost}</span><span>${tovar.cost}</span>` : `<span>${tovar.cost}</span>`}
                                </div>
                                <div class="t-name">${tovar.name}</div>
                                <div class="t-b-info">
                                    ${tovar.rating ? `
                                        <div class="star">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 16 15" fill="none">
                                                <path d="M7.04894 0.92705C7.3483 0.00573921 8.6517 0.00573969 8.95106 0.92705L10.0206 4.21885C10.1545 4.63087 10.5385 4.90983 10.9717 4.90983H14.4329C15.4016 4.90983 15.8044 6.14945 15.0207 6.71885L12.2205 8.75329C11.87 9.00793 11.7234 9.4593 11.8572 9.87132L12.9268 13.1631C13.2261 14.0844 12.1717 14.8506 11.388 14.2812L8.58778 12.2467C8.2373 11.9921 7.7627 11.9921 7.41221 12.2467L4.61204 14.2812C3.82833 14.8506 2.77385 14.0844 3.0732 13.1631L4.14277 9.87132C4.27665 9.4593 4.12999 9.00793 3.7795 8.75329L0.979333 6.71885C0.195619 6.14945 0.598395 4.90983 1.56712 4.90983H5.02832C5.46154 4.90983 5.8455 4.63087 5.97937 4.21885L7.04894 0.92705Z" fill="#FFB800" />
                                            </svg>
                                            <div>${tovar.rating}</div>
                                        </div>` : ''}
                                    <div class="t-b-otz">
                                        <img src="/static/img/icon-aktuelles.png" width="17" alt="комментарии">
                                        <div>${tovar.review_count} отзывов</div>
                                    </div>
                                </div>
                            </a>
                        </div>
                    `;

                    container.appendChild(tovarElement);
                });

                if (data.has_next) {
                    page++;
                    isLoading = false;
                }
                if (window.matchMedia('(min-width: 768px)').matches) {
                    new HvrSlider('.images');
                }
            })
            .catch(error => {
                console.error("Ошибка загрузки товаров:", error);
                isLoading = false;
            });
    }

    window.addEventListener("scroll", function () {
        const footerRect = document.querySelector('footer').getBoundingClientRect().height;
        if (footerRect + 340 >= Math.round(document.body.getBoundingClientRect().bottom) - window.innerHeight && !isLoading) {
            loadTovars();
        }
    });

});
