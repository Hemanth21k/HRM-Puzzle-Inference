document.addEventListener('DOMContentLoaded', () => {
    const sudokuGrid = document.getElementById('sudoku-grid');

    // Sample sudoku puzzle (0 represents empty cells)
    const sudokuData = [
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

    function createSudokuGrid() {
        for (let row = 0; row < 9; row++) {
            for (let col = 0; col < 9; col++) {
                const cell = document.createElement('div');
                cell.classList.add('sudoku-cell');

                // Mark cells with pre-filled numbers as readonly
                if (sudokuData[row][col] !== 0) {
                    cell.classList.add('readonly');
                    cell.textContent = sudokuData[row][col];
                } else {
                    // Add input functionality for empty cells
                    cell.contentEditable = true;
                    cell.addEventListener('input', (e) => validateInput(e, row, col));
                    cell.addEventListener('blur', (e) => handleBlur(e, row, col));
                }

                // Apply sub-grid styling every 3x3 cells
                if (row % 3 === 0 && col % 3 === 0) {
                    const subgrid = document.createElement('div');
                    subgrid.classList.add('sudoku-subgrid-3x3');
                    sudokuGrid.appendChild(subgrid);
                    subgrid.appendChild(cell);
                } else {
                    sudokuGrid.appendChild(cell);
                }
            }
        }
    }

    function validateInput(event, row, col) {
        const value = event.target.textContent;
        // Only allow numbers 1-9
        if (!/^[1-9]$/.test(value)) {
            event.target.textContent = '';
        } else {
            // Additional validation logic could go here (e.g., Sudoku rules)
        }
    }

    function handleBlur(event, row, col) {
        const value = event.target.textContent;
        if (!/^[1-9]$/.test(value)) {
            event.target.textContent = '';
        }
    }

    createSudokuGrid();
});
