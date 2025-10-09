// API Configuration
// Use environment-based URL detection
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8010' 
    : `http://${window.location.hostname}:8010`;

// State management
let currentSessionId = null;
let autoSolving = false;
let currentStep = 0;

// Initial puzzle
const initialPuzzle = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9]
];

let currentPuzzle = JSON.parse(JSON.stringify(initialPuzzle));

// DOM Elements
const sudokuGrid = document.getElementById('sudoku-grid');
const checkpointInput = document.getElementById('checkpoint-path');
const modelSelect = document.getElementById('model-select');
const generateBtn = document.getElementById('generate-btn');
const resetBtn = document.getElementById('reset-btn');
const initializeBtn = document.getElementById('initialize-btn');
const stepBtn = document.getElementById('step-btn');
const autoSolveBtn = document.getElementById('auto-solve-btn');
const stopBtn = document.getElementById('stop-btn');
const statusText = document.getElementById('status-text');
const stepCount = document.getElementById('step-count');
const sessionIdSpan = document.getElementById('session-id');

// Modal elements
const puzzleModal = document.getElementById('puzzle-modal');
const confirmGenerateBtn = document.getElementById('confirm-generate-btn');
const cancelGenerateBtn = document.getElementById('cancel-generate-btn');
const testDataSelect = document.getElementById('test-data-select');

// Radio button handling
document.querySelectorAll('input[name="puzzle-source"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        testDataSelect.disabled = e.target.value !== 'test_data';
    });
});

// Model selection handler
modelSelect.addEventListener('change', (e) => {
    if (e.target.value && e.target.value !== 'custom') {
        checkpointInput.value = e.target.value;
    } else if (e.target.value === 'custom') {
        checkpointInput.focus();
    }
});

// Create Sudoku Grid
function createSudokuGrid(puzzle) {
    sudokuGrid.innerHTML = '';
    
    for (let row = 0; row < 9; row++) {
        for (let col = 0; col < 9; col++) {
            const cell = document.createElement('div');
            cell.classList.add('sudoku-cell');
            cell.dataset.row = row;
            cell.dataset.col = col;
            
            if (initialPuzzle[row][col] !== 0) {
                cell.classList.add('readonly');
                cell.textContent = puzzle[row][col] || '';
            } else {
                cell.textContent = puzzle[row][col] || '';
                if (puzzle[row][col] !== 0) {
                    cell.classList.add('ai-filled');
                }
            }
            
            sudokuGrid.appendChild(cell);
        }
    }
}

// Update grid with animation
function updateGrid(newPuzzle) {
    for (let row = 0; row < 9; row++) {
        for (let col = 0; col < 9; col++) {
            const index = row * 9 + col;
            const cell = sudokuGrid.children[index];
            
            if (currentPuzzle[row][col] !== newPuzzle[row][col]) {
                cell.classList.remove('ai-filled', 'changed');
                void cell.offsetWidth; // Trigger reflow
                
                if (initialPuzzle[row][col] === 0) {
                    cell.classList.add('changed');
                    setTimeout(() => {
                        cell.classList.remove('changed');
                        cell.classList.add('ai-filled');
                    }, 500);
                }
                
                cell.textContent = newPuzzle[row][col] || '';
            }
        }
    }
    
    currentPuzzle = JSON.parse(JSON.stringify(newPuzzle));
}

// Update UI status
function updateStatus(status, step = null) {
    statusText.textContent = status;
    if (step !== null) {
        currentStep = step;
        stepCount.textContent = step;
    }
}

// API Calls
async function initializeSolver() {
    try {
        updateStatus('Initializing solver...');
        initializeBtn.disabled = true;
        
        const checkpointPath = checkpointInput.value.trim();
        if (!checkpointPath) {
            alert('Please enter a checkpoint path');
            initializeBtn.disabled = false;
            updateStatus('Ready');
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/api/initialize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                puzzle: currentPuzzle,
                checkpoint_path: checkpointPath
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        currentSessionId = data.session_id;
        sessionIdSpan.textContent = currentSessionId.substring(0, 10) + '...';
        
        updateStatus('Solver initialized - Ready to solve', 0);
        stepBtn.disabled = false;
        autoSolveBtn.disabled = false;
        initializeBtn.disabled = false;
        
    } catch (error) {
        console.error('Error initializing solver:', error);
        alert('Failed to initialize solver: ' + error.message);
        updateStatus('Error');
        initializeBtn.disabled = false;
    }
}

async function solveStep() {
    try {
        if (!currentSessionId) {
            alert('Please initialize the solver first');
            return;
        }
        
        updateStatus('Solving step...');
        stepBtn.disabled = true;
        autoSolveBtn.disabled = true;
        
        const response = await fetch(`${API_BASE_URL}/api/step/${currentSessionId}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        updateGrid(data.current_grid);
        updateStatus(data.finished ? 'Solved!' : 'Step completed', data.step);
        
        if (data.finished) {
            stepBtn.disabled = true;
            autoSolveBtn.disabled = true;
            stopBtn.disabled = true;
        } else {
            stepBtn.disabled = false;
            autoSolveBtn.disabled = false;
        }
        
        return data.finished;
        
    } catch (error) {
        console.error('Error solving step:', error);
        alert('Failed to solve step: ' + error.message);
        updateStatus('Error');
        stepBtn.disabled = false;
        autoSolveBtn.disabled = false;
        return true; // Stop on error
    }
}

async function autoSolve() {
    if (autoSolving) return;
    
    autoSolving = true;
    autoSolveBtn.disabled = true;
    stopBtn.disabled = false;
    stepBtn.disabled = true;
    initializeBtn.disabled = true;
    
    updateStatus('Auto solving...');
    
    while (autoSolving) {
        const finished = await solveStep();
        
        if (finished) {
            autoSolving = false;
            break;
        }
        
        // Add delay between steps for visualization
        await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    stopBtn.disabled = true;
    if (!autoSolving) {
        updateStatus('Stopped');
        stepBtn.disabled = false;
        autoSolveBtn.disabled = false;
    }
    initializeBtn.disabled = false;
}

function stopAutoSolve() {
    autoSolving = false;
    stopBtn.disabled = true;
    updateStatus('Stopped');
    stepBtn.disabled = false;
    autoSolveBtn.disabled = false;
    initializeBtn.disabled = false;
}

function resetPuzzle() {
    currentPuzzle = JSON.parse(JSON.stringify(initialPuzzle));
    createSudokuGrid(currentPuzzle);
    
    if (currentSessionId) {
        fetch(`${API_BASE_URL}/api/session/${currentSessionId}`, {
            method: 'DELETE'
        }).catch(console.error);
    }
    
    currentSessionId = null;
    autoSolving = false;
    currentStep = 0;
    
    sessionIdSpan.textContent = 'None';
    stepCount.textContent = '0';
    updateStatus('Ready');
    
    stepBtn.disabled = true;
    autoSolveBtn.disabled = true;
    stopBtn.disabled = true;
    initializeBtn.disabled = false;
}

// Event Listeners
generateBtn.addEventListener('click', openGenerateModal);
cancelGenerateBtn.addEventListener('click', closeGenerateModal);
confirmGenerateBtn.addEventListener('click', generateNewPuzzle);
resetBtn.addEventListener('click', resetPuzzle);
initializeBtn.addEventListener('click', initializeSolver);
stepBtn.addEventListener('click', solveStep);
autoSolveBtn.addEventListener('click', autoSolve);
stopBtn.addEventListener('click', stopAutoSolve);

// Generate puzzle functions
async function openGenerateModal() {
    puzzleModal.style.display = 'flex';
    await loadTestDataFiles();
}

function closeGenerateModal() {
    puzzleModal.style.display = 'none';
}

async function loadTestDataFiles() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/test_data_files`);
        if (!response.ok) return;
        
        const data = await response.json();
        
        if (data.files && data.files.length > 0) {
            testDataSelect.innerHTML = '<option value="">-- Select test data file --</option>';
            data.files.forEach(file => {
                const option = document.createElement('option');
                option.value = file.path;
                option.textContent = `${file.name} (${file.size_mb}MB, shape: ${file.shape})`;
                testDataSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading test data files:', error);
    }
}

async function generateNewPuzzle() {
    try {
        updateStatus('Generating puzzle...');
        
        const source = document.querySelector('input[name="puzzle-source"]:checked').value;
        const requestBody = { source };
        
        if (source === 'test_data') {
            const testDataPath = testDataSelect.value;
            if (!testDataPath) {
                alert('Please select a test data file');
                return;
            }
            requestBody.test_data_path = testDataPath;
        }
        
        const response = await fetch(`${API_BASE_URL}/api/generate_puzzle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update initial puzzle (this becomes the new "reset" state)
        for (let i = 0; i < 9; i++) {
            for (let j = 0; j < 9; j++) {
                initialPuzzle[i][j] = data.puzzle[i][j];
            }
        }
        
        // Reset and display new puzzle
        currentPuzzle = JSON.parse(JSON.stringify(initialPuzzle));
        createSudokuGrid(currentPuzzle);
        
        // Clear session
        if (currentSessionId) {
            fetch(`${API_BASE_URL}/api/session/${currentSessionId}`, {
                method: 'DELETE'
            }).catch(console.error);
        }
        
        currentSessionId = null;
        autoSolving = false;
        currentStep = 0;
        
        sessionIdSpan.textContent = 'None';
        stepCount.textContent = '0';
        stepBtn.disabled = true;
        autoSolveBtn.disabled = true;
        stopBtn.disabled = true;
        
        updateStatus(`New puzzle generated from ${data.source}`);
        closeGenerateModal();
        
    } catch (error) {
        console.error('Error generating puzzle:', error);
        alert('Failed to generate puzzle: ' + error.message);
        updateStatus('Error');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    createSudokuGrid(currentPuzzle);
    updateStatus('Ready');
    loadAvailableModels();
});

// Load available models from backend
async function loadAvailableModels() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/models`);
        if (!response.ok) {
            console.error('Failed to fetch models');
            return;
        }
        
        const data = await response.json();
        
        if (data.models && data.models.length > 0) {
            // Clear existing options except first two
            modelSelect.innerHTML = '<option value="">-- Select a model --</option>';
            
            // Add models from backend
            data.models.forEach(model => {
                const option = document.createElement('option');
                const configStatus = model.has_config ? '✓' : '✗';
                option.value = model.path;
                option.textContent = `${model.game} - ${model.filename} (${model.size_mb}MB) ${configStatus}`;
                modelSelect.appendChild(option);
            });
            
            // Add custom option at the end
            const customOption = document.createElement('option');
            customOption.value = 'custom';
            customOption.textContent = 'Custom Path...';
            modelSelect.appendChild(customOption);
            
            console.log(`Loaded ${data.models.length} models`);
        }
    } catch (error) {
        console.error('Error loading models:', error);
        // Keep default options if fetching fails
    }
}