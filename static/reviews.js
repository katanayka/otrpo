document.addEventListener("DOMContentLoaded", function() {
    const reviewForm = document.getElementById("reviewForm");
    const reviewsContainer = document.getElementById("reviews");
    const starRating = document.getElementById("starRating");
    const pokemon_id = document.getElementById("getid").innerHTML;
    // Ваш код для отображения оценки звездочками
    // Отправка отзыва
    reviewForm.addEventListener("submit", function(event) {
        event.preventDefault();
        const username = document.getElementById("username").value;
        const rating = document.getElementById("rating").value;
        const review = document.getElementById("review").value;

        const data = {
            pokemon_id: pokemon_id,
            username: username,
            rating: rating,
            review_text: review
        };

        fetch("/add_review", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            // Обработка успешной отправки
        })
        .catch(error => {
            console.error(error);
        });
    });

    // Загрузка и отображение отзывов
    function loadReviews() {
        fetch("/get_reviews/" + pokemon_id) // Замените на соответствующий ID покемона
        .then(response => response.json())
        .then(data => {
            reviewsContainer.innerHTML = "";
            data.reviews.forEach(review => {
                const reviewElement = document.createElement("div");
                reviewElement.innerHTML = `<p>${review.username}: ${review.review_text} (Rating: ${review.rating})</p>`;
                reviewsContainer.appendChild(reviewElement);
            });
        })
        .catch(error => {
            console.error(error);
        });
    }

    loadReviews();

    // Ваш код для отображения оценки звездочками

    // Отправка оценки
    starRating.addEventListener("click", function(event) {
        const rating = event.target.dataset.rating;
        const data = {
            pokemon_id: 1,  // Замените на соответствующий ID покемона
            rating: rating
        };

        fetch("/add_rating", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            // Обработка успешной отправки
        })
        .catch(error => {
            console.error(error);
        });
    });
});
