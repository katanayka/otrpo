document.addEventListener("DOMContentLoaded", function() {
  // Загрузка данных при загрузке страницы
  loadData();

  // Функция для загрузки данных
  function loadData() {
      fetch('/?page=1')  // Здесь указывайте путь к вашему Flask-эндпоинту
          .then(response => response.json())
          .then(data => {
              // Обработка полученных данных
              displayData(data);
          })
          .catch(error => console.error('Error:', error));
  }

  // Функция для отображения данных на странице
  function displayData(data) {
      const pokemonRow = document.querySelector('.pokemon-row');
      pokemonRow.innerHTML = '';

      data.data.forEach(item => {
          const pokemonContainer = document.createElement('div');
          pokemonContainer.classList.add('pokemon-container');

          // Создание HTML-элементов для отображения данных
          // ...

          pokemonRow.appendChild(pokemonContainer);
      });

      // Обработка пагинации и других элементов, если необходимо
      // ...

      // Пример обработки события формы
      const myForm = document.getElementById('myForm');
      myForm.addEventListener('submit', function(event) {
          event.preventDefault();
          const param = document.getElementById('param').value;
          // Здесь можно отправить данные на сервер для обработки
          // fetch('/search?param=' + param) и т.д.
      });
  }

  // Другие функции и обработчики событий
}); 
  
function filter_table() {
  let filter = document.querySelector('#search').value.toUpperCase();
  let table = document.querySelector('#tableBody');
  let rows = table.querySelectorAll('tr');
  for (let i = 0; i < rows.length; i++) {
      let td = rows[i].getElementsByTagName('td')[1];
      if (td) {
          let txtValue = td.textContent || td.innerText;
          if (txtValue.toUpperCase().indexOf(filter) > -1) {
              rows[i].style.display = '';
          } else {
              rows[i].style.display = 'none';
          }
      }
  }
}
  
function showPokemonInfo(pokemonName) {
  // Make an API request to get extended information about the selected Pokémon
  // You can use the Pokémon name to construct the API request URL
  const apiUrl = `https://pokeapi.co/api/v2/pokemon/${pokemonName}`;

  fetch(apiUrl)
    .then(response => response.json())
    .then(data => {
      const extendedInfo = `
        <h2>${pokemonName}</h2>
        <p>Height: ${data.height} dm</p>
        <p>Weight: ${data.weight} hg</p>
        <p>HP: ${data.stats[0]["base_stat"]}</p>
        <p>Atk: ${data.stats[1]["base_stat"]}</p>
        <p>Def: ${data.stats[2]["base_stat"]}</p>
        <p>Sp.Atk: ${data.stats[3]["base_stat"]}</p>
        <p>Sp.Def.: ${data.stats[4]["base_stat"]}</p>
        <p>Speed: ${data.stats[5]["base_stat"]}</p>
        <img src="${ data.sprites.front_default }" alt="{${ data.name }}">
      `;

      document.getElementById('pokemon-info').innerHTML = extendedInfo;
      document.getElementById('modal-overlay').style.display = 'block';
      document.getElementById('pokemon-info').style.display = 'block';
    })
    .catch(error => {
      console.error('Error fetching Pokémon data:', error);
    });
}

window.addEventListener('click', function (e) {
  if (document.getElementById('pokemon-info').contains(e.target)) {
    console.log("DA");
  } else {
    hidePokemonInfo();
  }
});

function hidePokemonInfo() {
  document.getElementById('modal-overlay').style.display = 'none';
  document.getElementById('pokemon-info').style.display = 'none';
}
function openLink() {
  var paramValue = document.getElementById("param").value;
  if (paramValue.length == 0) {
    var url = "/";
  }
  else var url = "/search?text=" + encodeURIComponent(paramValue);
  window.location.href = url;
}

