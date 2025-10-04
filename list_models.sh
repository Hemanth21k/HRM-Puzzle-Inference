#!/bin/bash

# Script to list all available checkpoints in the checkpoints directory

echo "======================================="
echo "Available Checkpoints in ./checkpoints/"
echo "======================================="
echo ""

if [ ! -d "checkpoints" ]; then
    echo "Error: checkpoints directory not found"
    exit 1
fi

found_models=false

# Find all checkpoint files
while IFS= read -r -d '' file; do
    found_models=true
    # Get relative path from checkpoints/
    rel_path="${file#checkpoints/}"
    
    # Get directory name (game type)
    game_dir=$(dirname "$rel_path")
    
    # Get file name
    filename=$(basename "$file")
    
    # Get file size
    size=$(du -h "$file" | cut -f1)
    
    # Check if config exists
    config_path="checkpoints/$game_dir/all_config.yaml"
    if [ -f "$config_path" ]; then
        config_status="✓ Config found"
    else
        config_status="✗ Config missing"
    fi
    
    echo "Game/Model: $game_dir"
    echo "  File:   $filename"
    echo "  Size:   $size"
    echo "  Config: $config_status"
    echo "  Path:   /app/checkpoints/$rel_path"
    echo ""
    
done < <(find checkpoints -type f \( -name "*.pt" -o -name "*.pth" -o -name "*.ckpt" \) -print0)

if [ "$found_models" = false ]; then
    echo "No checkpoint files found!"
    echo ""
    echo "Please add your checkpoints in the following structure:"
    echo "  checkpoints/"
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