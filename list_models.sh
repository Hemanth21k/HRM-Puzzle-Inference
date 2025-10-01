#!/bin/bash

# Script to list all available models in the models directory

echo "======================================="
echo "Available Models in ./models/"
echo "======================================="
echo ""

if [ ! -d "models" ]; then
    echo "Error: models directory not found"
    exit 1
fi

found_models=false

# Find all checkpoint files
while IFS= read -r -d '' file; do
    found_models=true
    # Get relative path from models/
    rel_path="${file#models/}"
    
    # Get directory name (game type)
    game_dir=$(dirname "$rel_path")
    
    # Get file name
    filename=$(basename "$file")
    
    # Get file size
    size=$(du -h "$file" | cut -f1)
    
    # Check if config exists
    config_path="models/$game_dir/all_config.yaml"
    if [ -f "$config_path" ]; then
        config_status="✓ Config found"
    else
        config_status="✗ Config missing"
    fi
    
    echo "Game/Model: $game_dir"
    echo "  File:   $filename"
    echo "  Size:   $size"
    echo "  Config: $config_status"
    echo "  Path:   /app/models/$rel_path"
    echo ""
    
done < <(find models -type f \( -name "*.pt" -o -name "*.pth" -o -name "*.ckpt" \) -print0)

if [ "$found_models" = false ]; then
    echo "No model checkpoints found!"
    echo ""
    echo "Please add your models in the following structure:"
    echo "  models/"
    echo "  ├── sudoku-1k/"
    echo "  │   ├── step_10000.pt"
    echo "  │   └── all_config.yaml"
    echo "  └── other-game/"
    echo "      ├── checkpoint.pth"
    echo "      └── all_config.yaml"
    echo ""
    echo "Supported formats: .pt, .pth, .ckpt"
fi

echo "======================================="