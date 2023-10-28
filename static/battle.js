document.addEventListener("DOMContentLoaded", function() {
    const rollDiceButton = document.getElementById("rollDiceButton");
    const quickBattleButton = document.getElementById("quickBattleButton");
    const diceResult = document.getElementById("diceResult");
    const battleResult = document.getElementById("battleResult");
    const userInput = document.getElementById("userInput");

    rollDiceButton.addEventListener("click", () => {
        const userRoll = parseInt(userInput.value);
        if (userRoll >= 1 && userRoll <= 10) {
            fetch(`/fight/${userRoll}`, {
                method: "POST",
            })
            .then(response => response.json())
            .then(data => {
                updateBattleData(data);
            });
        } else {
            diceResult.innerText = "Введите число от 1 до 10.";
        }
    });

    quickBattleButton.addEventListener("click", () => {
        fetch("/fight/fast")
        .then(response => response.json())
        .then(data => {
            updateBattleData(data);
        });
    });

    function updateBattleData(data) {
        const playerHP = document.getElementById("player_hp");
        const playerDef = document.getElementById("player_defense");
        const enemyHP = document.getElementById("enemy_hp");            
        const enemyDef = document.getElementById("enemy_defense");

        playerHP.innerText = data.player.hp;
        playerDef.innerText = data.player.defense;
        enemyHP.innerText = data.enemy.hp;
        enemyDef.innerText = data.enemy.defense;
        if (data.winner) {
            document.getElementById('battle-controls').innerHTML = `Победитель: ${data.winner["name"]}`;
            const puk = {
                email: "katanaevdmitry45@gmail.com",
                winner: data.winner["name"]
              };
              
              fetch('/POCHTA', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify(puk)
              })
              .then(response => {
                if (response.ok) {
                  return response.json();
                } else {
                  throw new Error(`Ошибка: ${response.status}`);
                }
              })
              .then(puk => {
                console.log(puk.message);
              })
              .catch(error => {
                console.error(error);
              });
        } else {
            battleResult.innerText = "";
        }
    }
});