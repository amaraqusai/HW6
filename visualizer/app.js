let reportData = null;
let currentGame = null;
let currentTurnIndex = 0;
let isPlaying = false;
let playInterval = null;

const elements = {
    groupInfo: document.getElementById('group-info'),
    gameSelector: document.getElementById('game-selector'),
    scoreCop: document.getElementById('score-cop'),
    scoreThief: document.getElementById('score-thief'),
    turnInfo: document.getElementById('turn-info'),
    messageInfo: document.getElementById('message-info'),
    grid: document.getElementById('grid'),
    btnPlay: document.getElementById('btn-play'),
    btnPrev: document.getElementById('btn-prev'),
    btnNext: document.getElementById('btn-next'),
};

async function init() {
    try {
        const response = await fetch('report.json');
        if (!response.ok) {
            // fallback
            const fallbackResponse = await fetch('../report.json');
            if (!fallbackResponse.ok) throw new Error('File not found');
            reportData = await fallbackResponse.json();
        } else {
            reportData = await response.json();
        }
        setupUI();
    } catch (e) {
        elements.groupInfo.innerText = "Error loading report.json. Have you run `python orchestrator.py`? (Make sure to view via python -m http.server)";
    }
}

function setupUI() {
    elements.groupInfo.innerText = `${reportData.group_name} | ${reportData.students.join(', ')}`;
    
    elements.gameSelector.innerHTML = '';
    reportData.sub_games.forEach((game, idx) => {
        const option = document.createElement('option');
        option.value = idx;
        option.innerText = `Game ${game.game_id} (Winner: ${game.winner})`;
        elements.gameSelector.appendChild(option);
    });

    elements.gameSelector.addEventListener('change', (e) => {
        loadGame(parseInt(e.target.value));
    });

    elements.btnPrev.addEventListener('click', () => step(-1));
    elements.btnNext.addEventListener('click', () => step(1));
    elements.btnPlay.addEventListener('click', togglePlay);

    loadGame(0);
}

function loadGame(gameIndex) {
    currentGame = reportData.sub_games[gameIndex];
    currentTurnIndex = 0;
    
    elements.scoreCop.innerText = currentGame.scores.Cop;
    elements.scoreThief.innerText = currentGame.scores.Thief;
    
    if (isPlaying) togglePlay(); // pause on load
    renderTurn();
}

function renderTurn() {
    if (!currentGame || !currentGame.trajectory) return;
    
    // Create 5x5 grid
    elements.grid.innerHTML = '';
    const cells = [];
    for (let y = 0; y < 5; y++) {
        for (let x = 0; x < 5; x++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            elements.grid.appendChild(cell);
            cells.push(cell);
        }
    }

    const state = currentGame.trajectory[currentTurnIndex];
    if (!state) return;

    elements.turnInfo.innerText = `Turn: ${currentTurnIndex + 1} / ${currentGame.trajectory.length} (${state.turn} moved)`;
    
    // Show opponent message
    const msg = state.action?.message || "...";
    elements.messageInfo.innerText = `${state.turn} says: "${msg}"`;

    // Draw barriers
    state.barriers.forEach(pos => {
        const idx = pos[1] * 5 + pos[0];
        if (cells[idx]) cells[idx].classList.add('barrier');
    });

    // Draw players
    const cx = state.cop_pos[0];
    const cy = state.cop_pos[1];
    const tx = state.thief_pos[0];
    const ty = state.thief_pos[1];

    const cIdx = cy * 5 + cx;
    const tIdx = ty * 5 + tx;

    if (cIdx === tIdx) {
        if (cells[cIdx]) {
            cells[cIdx].classList.add('both');
            cells[cIdx].innerText = '💥';
        }
    } else {
        if (cells[cIdx]) {
            cells[cIdx].classList.add('cop');
            cells[cIdx].innerText = '🚔';
        }
        if (cells[tIdx]) {
            cells[tIdx].classList.add('thief');
            cells[tIdx].innerText = '🥷';
        }
    }
}

function step(dir) {
    if (!currentGame) return;
    currentTurnIndex += dir;
    if (currentTurnIndex < 0) currentTurnIndex = 0;
    if (currentTurnIndex >= currentGame.trajectory.length) {
        currentTurnIndex = currentGame.trajectory.length - 1;
        if (isPlaying) togglePlay();
    }
    renderTurn();
}

function togglePlay() {
    isPlaying = !isPlaying;
    if (isPlaying) {
        elements.btnPlay.innerText = '⏸ Pause';
        playInterval = setInterval(() => step(1), 800);
    } else {
        elements.btnPlay.innerText = '▶ Play';
        clearInterval(playInterval);
    }
}

init();
