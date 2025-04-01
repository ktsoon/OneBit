
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        return new Promise(resolve => {
            clearTimeout(timeout);
            timeout = setTimeout(() => resolve(func.apply(this, args)), wait);
        });
    };
}

new Autocomplete('#autocomplete', {
    search: debounce(input => {
        if (input.length < 1) { return Promise.resolve([]); } // Фикс ошибки
        const url = `/search_text/?text=${input}`;
        return fetch(url)
            .then(response => response.json())
            .then(text => text.search.slice(0, 6));
    }, 300),

    onSubmit: result => {
        if (result['categ'] === 'tovar') {
            window.location.href = `/product/${result['slug']}`;
        } else if (result['categ'] === 'cat') {
            window.location.href = `/category/${result['slug']}/`;
        } else if (result['categ'] === 'avt') {
            document.querySelector('form.uk-search').submit();
        }
    },

    renderResult: (result, props) => {
        if (result['categ'] === 'tovar') {
            return `<li ${props} style='border-left: 2px red solid'>
                <div class="search-tovar">
                    <img src="${result['img_url']}">
                    <div>
                        <div>${result['name']}</div>
                        <div class="srch-t-bt">Товар</div>
                    </div>
                </div>
            </li>`;
        } else if (result['categ'] === 'cat') {
            return `<li ${props} style='border-left: 2px green solid'>
                <div>
                    <div>${result['name']}</div>
                    <div class="srch-t-bt">${result['gl_cat']}</div>
                </div>
            </li>`;
        } else if (result['categ'] === 'avt') {
            return `<li ${props} style='border-left: 2px yellow solid'>
                <div class="search-tovar srch-t-avt">
                    ${result['img_url'] ? `<img src="${result['img_url']}">` : ''}
                    <div>
                        <div>${result['name']}</div>
                        <div class="srch-t-bt">Бренд</div>
                    </div>
                </div>
            </li>`;
        }
    },

    getResultValue: result => result['name']
});