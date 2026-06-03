const SIZE = 4;

const initialState = () => ({
  turn: 1,
  status: "playing",
  phase: "player",
  player: { id: "player", type: "player", x: 1, y: 1, hp: 3, maxHp: 3 },
  enemies: [
    { id: "enemy-a", type: "enemy", x: 2, y: 1, hp: 2, maxHp: 2 },
    { id: "enemy-b", type: "enemy", x: 2, y: 2, hp: 1, maxHp: 1 }
  ],
  walls: [{ x: 3, y: 1 }],
  logs: ["点击玩家右侧橙色敌人，试试第一条因果链。"]
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
        tile.innerHTML = `<div class="unit enemy">E</div><span class="hp">${enemy.hp}</span>${action === "attack" ? `<span class="intent">攻击</span>` : ""}`;
      } else if (isPlayer) {
        tile.innerHTML = `<div class="unit player">P</div><span class="hp">${state.player.hp}</span>`;
      } else if (action === "move") {
        tile.innerHTML = `<span class="intent">移动</span>`;
      }

      tile.addEventListener("click", () => handleTileClick(x, y));
      boardEl.appendChild(tile);
    }
  }

  playerHpEl.textContent = state.player.hp;
  gameStateEl.textContent = getStatusText();
  gameStateEl.className = state.status === "won" ? "win" : state.status === "lost" ? "lose" : "";

  logEl.innerHTML = "";
  state.logs.slice(0, 14).forEach(log => {
    const li = document.createElement("li");
    li.textContent = log;
    logEl.appendChild(li);
  });
}

function handleTileClick(x, y) {
  if (state.status !== "playing" || state.phase !== "player") return;

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

  addLog("只能点击相邻绿色格移动，或点击相邻橙色敌人攻击。");
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

  const target = state.enemies.find(item => item.id === enemy.id);
  const nextX = target.x + dx;
  const nextY = target.y + dy;

  if (!isInside(nextX, nextY) || getWallAt(nextX, nextY)) {
    addLog(`敌人被推向墙/边界：触发【撞墙伤害】。`);
    damageEnemy(target, 1, "撞墙伤害");
    return;
  }

  if (getEnemyAt(nextX, nextY) || isPlayerAt(nextX, nextY)) {
    addLog("敌人身后被挡住，无法推动。暂时不产生额外效果。");
    return;
  }

  target.x = nextX;
  target.y = nextY;
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
  if (checkEnd()) {
    render();
    return;
  }

  state.phase = "enemy";
  render();

  window.setTimeout(() => {
    enemyTurn();
    checkEnd();
    if (state.status === "playing") {
      state.phase = "player";
      state.turn += 1;
      addLog(`第 ${state.turn} 回合：轮到玩家行动。`);
    }
    render();
  }, 280);
}

function enemyTurn() {
  addLog("敌人回合：敌人开始追击。");
  const enemies = [...state.enemies];

  for (const enemy of enemies) {
    const current = state.enemies.find(item => item.id === enemy.id);
    if (!current || state.status !== "playing") continue;

    const distance = manhattan(current.x, current.y, state.player.x, state.player.y);
    if (distance === 1) {
      damagePlayer(1, "敌人近身攻击");
      continue;
    }

    const next = getBestEnemyStep(current);
    if (next) {
      current.x = next.x;
      current.y = next.y;
      addLog(`敌人移动到 (${next.x}, ${next.y})。`);
    } else {
      addLog("敌人被地形挡住，无法移动。");
    }
  }
}

function getBestEnemyStep(enemy) {
  const candidates = [
    { x: enemy.x + 1, y: enemy.y },
    { x: enemy.x - 1, y: enemy.y },
    { x: enemy.x, y: enemy.y + 1 },
    { x: enemy.x, y: enemy.y - 1 }
  ];

  return candidates
    .filter(pos => isInside(pos.x, pos.y))
    .filter(pos => !getWallAt(pos.x, pos.y))
    .filter(pos => !getEnemyAt(pos.x, pos.y))
    .filter(pos => !isPlayerAt(pos.x, pos.y))
    .sort((a, b) => manhattan(a.x, a.y, state.player.x, state.player.y) - manhattan(b.x, b.y, state.player.x, state.player.y))[0];
}

function damagePlayer(amount, reason) {
  state.player.hp -= amount;
  addLog(`${reason}：玩家生命 -${amount}，剩余 ${Math.max(0, state.player.hp)}。`);
  if (state.player.hp <= 0) {
    state.status = "lost";
    addLog("玩家生命归零。失败。重开后再设计因果链。", true);
  }
}

function checkEnd() {
  if (state.enemies.length === 0) {
    state.status = "won";
    addLog("所有敌人被击败。胜利！这就是第一条因果连锁。", true);
    return true;
  }

  if (state.player.hp <= 0) {
    state.status = "lost";
    return true;
  }

  return false;
}

function getActionAt(x, y) {
  if (state.status !== "playing" || state.phase !== "player") return null;
  const dist = manhattan(state.player.x, state.player.y, x, y);
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

function manhattan(ax, ay, bx, by) {
  return Math.abs(ax - bx) + Math.abs(ay - by);
}

function addLog(message) {
  state.logs.unshift(message);
}

function getStatusText() {
  if (state.status === "won") return "胜利";
  if (state.status === "lost") return "失败";
  if (state.phase === "enemy") return "敌人行动中";
  return `第 ${state.turn} 回合`;
}

render();
