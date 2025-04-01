document.addEventListener("DOMContentLoaded", function () {
    let page = 1;
    let isLoading = false;
    let hasMoreComments = true;
    const reviewsContainer = document.querySelector(".uk-comment-list");
    const loadIndicator = document.querySelector("#load-more-comments");

    let rating = 0;
    let rating_ed = 0;

    // ✅ Инициализация рейтинга для добавления комментария
    raterJs({
        element: document.getElementById("rater_com_add"),
        starSize: 33,
        step: 1,
        rating: 0,
        rateCallback: function (newRating, done) {
            this.setRating(newRating);
            rating = newRating;
            updateButtonState_add();
            done();
        }
    });

    // ✅ Инициализация рейтинга для редактирования комментария
    let ret_ed = raterJs({
        element: document.getElementById("rater_com_edit"),
        starSize: 33,
        step: 1,
        rating: 0,
        rateCallback: function (newRating, done) {
            this.setRating(newRating);
            rating_ed = newRating;
            updateButtonState_edit();
            done();
        }
    });

    function loadComments() {
        if (isLoading || !hasMoreComments) return;
        isLoading = true;
        loadIndicator.style.display = "block";

        fetch(`/load_comments/${ttt}?page=${page}`)
            .then(response => response.json())
            .then(data => {
                data.comments.forEach(com => {
                    const commentId = `com-${com.id}`;
                    const isLongComment = com.comment.length > 250; // ✅ Если текст длиннее 250 символов

                    const commentHtml = `
                        <li id="${commentId}">
                            <article class="uk-comment uk-comment-primary">
                                <div class="uk-comment-header">
                                    <div class="uk-grid-medium uk-flex-middle" uk-grid>
                                        <div class="uk-width-auto">
                                            ${com.avatar ? `<img class="uk-comment-avatar" src="${com.avatar}" width="80" height="80">` : `<span class="uk-icon" uk-icon="icon: user; ratio: 4"></span>`}
                                        </div>
                                        <div class="uk-width-expand com-right">
                                            <h4 class="uk-comment-title uk-margin-remove">${com.username}</h4>
                                            <ul class="uk-comment-meta uk-subnav uk-subnav-divider uk-margin-remove-top">
                                                <li>
                                                    <span>${com.created_at}</span>
                                                    <div class="p-score"><div class="rater-com" id="rater_com_${com.id}"></div></div>
                                                </li>
                                            </ul>
                                            <span class="uk-text-muted">${com.updated_at ? "изменено" : ""}</span>
                                        </div>
                                    </div>
                                </div>
                                <div class="uk-comment-body">
                                    ${com.baned ? 
                                        `<span class="uk-label uk-label-danger">Комментарий скрыт</span>` 
                                        :
                                        `<p class="collapsible">${com.comment}</p>
                                        ${isLongComment ? `<a class="uk-link-muted toggle-button" data-id="${com.id}">Читать далее</a>` : ""}
                                        `
                                    }
                                </div>
                                ${com.user_comment ? `
                                    <button class="uk-button uk-button-default uk-button-small but-edit"
                                        uk-toggle="target: #edit-comment-modal"
                                        onclick="updateButtonState_edit()"
                                        data-id="${com.id}"
                                        data-text="${com.comment}"
                                        data-score="${com.star}">Изменить</button>
                                ` : ""}
                            </article>
                        </li>`;
                    
                    reviewsContainer.insertAdjacentHTML("beforeend", commentHtml);

                    // ✅ Инициализация рейтинга для загруженных комментариев
                    raterJs({
                        max: 5,
                        readOnly: true,
                        starSize: 20,
                        rating: com.star,
                        element: document.getElementById(`rater_com_${com.id}`)
                    });
                });

                if (!data.has_next) {
                    hasMoreComments = false;
                    window.removeEventListener("scroll", scrollHandler);
                    loadIndicator.remove();
                } else {
                    page++;
                }

                isLoading = false;
                reinitCommentEvents();  // ✅ Обновляем обработчики событий для новых комментариев
            })
            .catch(() => {
                isLoading = false;
                loadIndicator.style.display = "none";
            });
    }

    function scrollHandler() {
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 300) {
            loadComments();
        }
    }

    window.addEventListener("scroll", scrollHandler);
    loadComments();

    // ✅ Функция для повторной инициализации событий
    function reinitCommentEvents() {
        document.querySelectorAll(".toggle-button").forEach(button => {
            button.removeEventListener("click", toggleComment);
            button.addEventListener("click", toggleComment);
        });

        document.querySelectorAll(".but-edit").forEach(button => {
            button.removeEventListener("click", editComment);
            button.addEventListener("click", editComment);
        });
    }

    // ✅ Обработчик кнопки "Читать далее"
    function toggleComment(event) {
        const button = event.target;
        const commentText = button.previousElementSibling;
        if (commentText) {
            commentText.classList.toggle("expanded");
            button.textContent = commentText.classList.contains("expanded") ? "Свернуть" : "Читать далее";
        }
    }

    // ✅ Обработчик кнопки "Изменить"
    function editComment(event) {
        const button = event.target;
        const commentText = button.getAttribute("data-text");
        const commentScore = parseFloat(button.getAttribute("data-score")) || 0;

        $("#comm_text_edit").val(commentText);
        ret_ed.setRating(commentScore); // ✅ Теперь рейтинг предустанавливается в модальном окне
    }

    function updateButtonState_add() {
        const button = $("#comm_add");
        button.prop("disabled", rating <= 0).toggleClass("but-dis", rating <= 0);
    }

    function updateButtonState_edit() {
        const button = $("#comm_edit");
        button.prop("disabled", rating_ed <= 0).toggleClass("but-dis", rating_ed <= 0);
    }

    updateButtonState_add();
});
