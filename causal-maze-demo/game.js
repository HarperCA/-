const SIZE = 4;

const initialState = () => ({
  turn: 1,
  status: "playing",
  player: { id: "player", type: "player", x: 1, y: 1, hp: 3, maxHp: 3 },
  enemies: [
    { id: "enemy-a", type: "enemy", x: 2, y: 1, hp: 2, maxHp: 2 },
    { id: "enemy-b", type: "enemy", x: 2, y: 2, hp: 1, maxHp: 1 }
  ],
  walls: [{ x: 3, y: 1 }],
  logs: ["点击玩家右侧敌人，试试第一条因果链。"]
});

let state = initialState();

const boardEl = document.querySelector("#board");
const logEl = document.querySelector("#log");
const playerHpEl = document.querySelector("#playerHp");
const gameStateEl = document.querySelector("#gameState");
const resetBtn = document.querySelector("#resetBtn");

resetBtn.addEventListener("click", () => {
  state = initialState();
  render();
});

function render() {
  boardEl.innerHTML = "";

  for (let y = 0; y < SIZE; y++) {
    for (let x = 0; x < SIZE; x++) {
      const tile = document.createElement("button");
      tile.className = "tile";
      tile.type = "button";
      tile.setAttribute("aria-label", `格子 ${x},${y}`);

      const action = getActionAt(x, y);
      if (action === "move") tile.classList.add("reachable");
      if (action === "attack") tile.classList.add("attackable");

      const wall = getWallAt(x, y);
      const enemy = getEnemyAt(x, y);
      const isPlayer = state.player.x === x && state.player.y === y;

      if (wall) {
        tile.innerHTML = `<div class="wall">■</div>`;
      } else if (enemy) {
        tile.innerHTML = `<div class="unit enemy">E</div><span class="hp">${enemy.hp}</span>`;
      } else if (isPlayer) {
        tile.innerHTML = `<div class="unit player">P</div><span class="hp">${state.player.hp}</span>`;
      }

      tile.addEventListener("click", () => handleTileClick(x, y));
      boardEl.appendChild(tile);
    }
  }

  playerHpEl.textContent = state.player.hp;
  gameStateEl.textContent = getStatusText();
  gameStateEl.className = state.status === "won" ? "win" : state.status === "lost" ? "lose" : "";

  logEl.innerHTML = "";
  state.logs.slice(0, 12).forEach(log => {
    const li = document.createElement("li");
    li.textContent = log;
    logEl.appendChild(li);
  });
}

function handleTileClick(x, y) {
  if (state.status !== "playing") return;

  const action = getActionAt(x, y);
  if (action === "move") {
    movePlayer(x, y);
    afterPlayerAction();
    return;
  }

  if (action === "attack") {
    const enemy = getEnemyAt(x, y);
    attackEnemy(enemy);
    afterPlayerAction();
    return;
  }

  addLog("只能点击相邻空格移动，或点击相邻敌人攻击。");
  render();
}

function movePlayer(x, y) {
  state.player.x = x;
  state.player.y = y;
  addLog(`玩家移动到 (${x}, ${y})。`);
}

function attackEnemy(enemy) {
  const dx = enemy.x - state.player.x;
  const dy = enemy.y - state.player.y;

  addLog(`玩家攻击敌人：触发【攻击会推人】。`);
  damageEnemy(enemy, 1, "攻击伤害");

  if (!isEnemyAlive(enemy.id)) return;

  const nextX = enemy.x + dx;
  const nextY = enemy.y + dy;

  if (!isInside(nextX, nextY) || getWallAt(nextX, nextY)) {
    addLog(`敌人被推向墙/边界：触发【撞墙伤害】。`);
    damageEnemy(enemy, 1, "撞墙伤害");
    return;
  }

  if (getEnemyAt(nextX, nextY) || isPlayerAt(nextX, nextY)) {
    addLog("敌人身后被挡住，无法推动。暂时不产生额外效果。");
    return;
  }

  enemy.x = nextX;
  enemy.y = nextY;
  addLog(`敌人被推到 (${nextX}, ${nextY})。`);
}

function damageEnemy(enemy, amount, reason) {
  const target = state.enemies.find(item => item.id === enemy.id);
  if (!target) return;

  target.hp -= amount;
  addLog(`${reason}：敌人生命 -${amount}，剩余 ${Math.max(0, target.hp)}。`);

  if (target.hp <= 0) {
    killEnemy(target);
  }
}

function killEnemy(enemy) {
  const deadX = enemy.x;
  const deadY = enemy.y;
  state.enemies = state.enemies.filter(item => item.id !== enemy.id);
  addLog(`敌人在 (${deadX}, ${deadY}) 死亡：触发【死亡爆炸】。`);

  const victims = state.enemies.filter(item => Math.abs(item.x - deadX) <= 1 && Math.abs(item.y - deadY) <= 1);

  if (victims.length === 0) {
    addLog("爆炸范围内没有其他敌人。");
  }

  victims.forEach(victim => damageEnemy(victim, 1, "爆炸伤害"));
}

function afterPlayerAction() {
  if (state.enemies.length === 0) {
    state.status = "won";
    addLog("所有敌人被击败。胜利！这就是第一条因果连锁。", true);
  } else {
    state.turn += 1;
  }

  render();
}

function getActionAt(x, y) {
  if (state.status !== "playing") return null;
  const dist = Math.abs(state.player.x - x) + Math.abs(state.player.y - y);
  if (dist !== 1) return null;
  if (getEnemyAt(x, y)) return "attack";
  if (!getWallAt(x, y) && !isOccupied(x, y)) return "move";
  return null;
}

function getEnemyAt(x, y) {
  return state.enemies.find(enemy => enemy.x === x && enemy.y === y);
}

function getWallAt(x, y) {
  return state.walls.find(wall => wall.x === x && wall.y === y);
}

function isPlayerAt(x, y) {
  return state.player.x === x && state.player.y === y;
}

function isOccupied(x, y) {
  return isPlayerAt(x, y) || getEnemyAt(x, y) || getWallAt(x, y);
}

function isInside(x, y) {
  return x >= 0 && x < SIZE && y >= 0 && y < SIZE;
}

function isEnemyAlive(id) {
  return state.enemies.some(enemy => enemy.id === id);
}

function addLog(message) {
  state.logs.unshift(message);
}

function getStatusText() {
  if (state.status === "won") return "胜利";
  if (state.status === "lost") return "失败";
  return `第 ${state.turn} 回合`;
}

render();
