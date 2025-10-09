from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import yaml
import os
import torch
import asyncio
import numpy as np
from pathlib import Path
from pretrain import PretrainConfig, init_train_state, create_dataloader
app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for model state
model_state = None
config = None
test_data = None  # Cache test data

class SudokuRequest(BaseModel):
    puzzle: List[List[int]]
    checkpoint_path: str  # Can be .pt, .pth, or any checkpoint format

class GeneratePuzzleRequest(BaseModel):
    source: str  # "random" or "test_data"
    test_data_path: Optional[str] = None  # Path to .npy file if using test_data

class SolverState(BaseModel):
    current_grid: List[List[int]]
    step: int
    finished: bool
    metrics: Optional[dict] = None

# Initialize model
def load_model(checkpoint_path: str):
    global model_state, config
    
    with open(os.path.join(os.path.dirname(checkpoint_path), "all_config.yaml"), "r") as f:
        config = PretrainConfig(**yaml.safe_load(f))
        config.eval_save_outputs = ["inputs", "labels", "logits"]
        config.checkpoint_path = os.path.dirname(checkpoint_path)
    
    # Create dataloader for metadata
    _, train_metadata = create_dataloader(config, "train", test_set_mode=False, 
                                         epochs_per_iter=1, 
                                         global_batch_size=config.global_batch_size, 
                                         rank=0, world_size=1)
    
    # Initialize model
    train_state = init_train_state(config, train_metadata, world_size=1)
    
    # Load checkpoint
    try:
        train_state.model.load_state_dict(torch.load(checkpoint_path, map_location="cuda"), assign=True)
    except:
        train_state.model.load_state_dict(
            {k.removeprefix("_orig_mod."): v for k, v in torch.load(checkpoint_path, map_location="cuda").items()}, 
            assign=True
        )
    
    train_state.model.eval()
    model_state = train_state
    
    return train_state

# Store active solving sessions
solving_sessions = {}

@app.post("/api/initialize")
async def initialize_solver(request: SudokuRequest):
    """Initialize the solver with a puzzle"""
    try:
        if model_state is None:
            load_model(request.checkpoint_path)
        
        # Convert puzzle to tensor format (add 1 since model expects 1-indexed)
        puzzle_tensor = torch.tensor([[cell + 1 for cell in row] for row in request.puzzle], 
                                    dtype=torch.long).reshape(-1).unsqueeze(0).cuda()
        
        # Create batch
        batch = {
            "inputs": puzzle_tensor,
            "labels": puzzle_tensor.clone(),  # Placeholder
            "puzzle_identifiers": torch.zeros(1, dtype=torch.long).cuda(),  # Add this line
        }
        
        # Initialize carry
        with torch.device("cuda"):
            carry = model_state.model.initial_carry(batch)
        
        # Store session
        session_id = str(hash(str(request.puzzle)))
        solving_sessions[session_id] = {
            "carry": carry,
            "batch": batch,
            "step": 0,
            "finished": False
        }
        
        return {
            "session_id": session_id,
            "initial_grid": request.puzzle,
            "status": "initialized"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/step/{session_id}")
async def solve_step(session_id: str):
    """Perform one solving step"""
    try:
        if session_id not in solving_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = solving_sessions[session_id]
        
        if session["finished"]:
            return {
                "finished": True,
                "current_grid": session["last_grid"],
                "step": session["step"]
            }
        
        with torch.inference_mode():
            # print("batch:",session["batch"])
            carry, _, metrics, preds, all_finish = model_state.model(
                carry=session["carry"],
                batch=session["batch"],
                return_keys=config.eval_save_outputs
            )
            all_finish = all_finish.cpu().item()
            
            # Get predictions
            pred_outs = torch.argmax(preds["logits"], dim=-1)
            print("pred outs:", pred_outs)
            print("all finish:", all_finish)
            current_grid = (pred_outs[0].reshape(9, 9) - 1).cpu().tolist()
            
            # Update session
            session["carry"] = carry
            session["step"] += 1
            session["finished"] = all_finish
            session["last_grid"] = current_grid
            
            return {
                "finished": all_finish,
                "current_grid": current_grid,
                "step": session["step"],
                "metrics": {k: float(v) if torch.is_tensor(v) else v for k, v in metrics.items()} if metrics else None
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/solve_complete/{session_id}")
async def solve_complete(session_id: str):
    """Solve the puzzle completely and return all steps"""
    try:
        steps = []
        while True:
            result = await solve_step(session_id)
            steps.append(result)
            if result["finished"]:
                break
        
        return {"steps": steps}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Clean up a solving session"""
    if session_id in solving_sessions:
        del solving_sessions[session_id]
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Session not found")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model_state is not None
    }

def generate_random_sudoku():
    """Generate a random valid Sudoku puzzle (simplified version)"""
    # Start with a valid solved Sudoku (example base)
    base = [
        [5, 3, 4, 6, 7, 8, 9, 1, 2],
        [6, 7, 2, 1, 9, 5, 3, 4, 8],
        [1, 9, 8, 3, 4, 2, 5, 6, 7],
        [8, 5, 9, 7, 6, 1, 4, 2, 3],
        [4, 2, 6, 8, 5, 3, 7, 9, 1],
        [7, 1, 3, 9, 2, 4, 8, 5, 6],
        [9, 6, 1, 5, 3, 7, 2, 8, 4],
        [2, 8, 7, 4, 1, 9, 6, 3, 5],
        [3, 4, 5, 2, 8, 6, 1, 7, 9]
    ]
    
    # Randomly remove numbers to create puzzle (keep 20-30 numbers)
    import random
    puzzle = [row[:] for row in base]
    num_to_remove = random.randint(51, 61)  # Remove 51-61 numbers (leaving 20-30)
    
    positions = [(i, j) for i in range(9) for j in range(9)]
    random.shuffle(positions)
    
    for i, j in positions[:num_to_remove]:
        puzzle[i][j] = 0
    
    return puzzle

@app.post("/api/generate_puzzle")
async def generate_puzzle(request: GeneratePuzzleRequest):
    """Generate a new Sudoku puzzle"""
    try:
        global test_data
        
        if request.source == "random":
            # Generate random puzzle
            puzzle = generate_random_sudoku()
            return {
                "puzzle": puzzle,
                "source": "random",
                "status": "success"
            }
        
        elif request.source == "test_data":
            # Load from test data .npy file
            if not request.test_data_path:
                raise HTTPException(status_code=400, detail="test_data_path is required when source is 'test_data'")
            
            test_data_path = Path(request.test_data_path)
            if not test_data_path.exists():
                raise HTTPException(status_code=404, detail=f"Test data file not found: {request.test_data_path}")
            
            # Load test data (cache it)
            if test_data is None or not hasattr(test_data, 'path') or test_data.path != str(test_data_path):
                test_data_array = np.load(test_data_path)
                test_data = type('obj', (object,), {
                    'data': test_data_array,
                    'path': str(test_data_path)
                })()
            
            # Get random sample
            import random
            idx = random.randint(0, len(test_data.data) - 1)
            puzzle_array = test_data.data[idx]
            
            # Convert to list format (assuming it's 9x9)
            if puzzle_array.shape == (81,):
                puzzle = puzzle_array.reshape(9, 9).tolist()
            elif puzzle_array.shape == (9, 9):
                puzzle = puzzle_array.tolist()
            else:
                raise HTTPException(status_code=400, detail=f"Unexpected puzzle shape: {puzzle_array.shape}")
            
            # Convert to int and handle any special values
            puzzle = [[int(cell) for cell in row] for row in puzzle]
            
            return {
                "puzzle": puzzle,
                "source": "test_data",
                "index": idx,
                "status": "success"
            }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid source. Must be 'random' or 'test_data'")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/test_data_files")
async def list_test_data_files():
    """List available test data .npy files in checkpoints directory"""
    try:
        data_dir = Path("/app/data")
        if not data_dir.exists():
            return {"files": [], "message": "Data directory not found"}
        
        npy_files = []
        for npy_path in data_dir.rglob("*.npy"):
            rel_path = npy_path.relative_to(data_dir)
            
            # Get file info
            size_mb = npy_path.stat().st_size / (1024 * 1024)
            
            # Try to get array shape
            try:
                arr = np.load(npy_path, mmap_mode='r')
                shape = arr.shape
            except:
                shape = "unknown"
            
            npy_files.append({
                "name": npy_path.name,
                "path": f"/app/data/{rel_path}",
                "size_mb": round(size_mb, 2),
                "shape": str(shape)
            })
        
        return {
            "files": npy_files,
            "count": len(npy_files)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/models")
async def list_available_models():
    """List all available models in the checkpoints directory"""
    try:
        import glob
        from pathlib import Path
        
        checkpoints_dir = Path("/app/checkpoints")
        if not checkpoints_dir.exists():
            return {"models": [], "message": "Checkpoints directory not found"}
        
        available_models = []
        
        # Search for checkpoint files
        patterns = ["*.pt", "*.pth", "*.ckpt"]
        for pattern in patterns:
            for checkpoint_path in checkpoints_dir.rglob(pattern):
                rel_path = checkpoint_path.relative_to(checkpoints_dir)
                game_dir = rel_path.parent
                
                # Check if config exists
                config_path = checkpoints_dir / game_dir / "all_config.yaml"
                has_config = config_path.exists()
                
                # Get file size
                size_mb = checkpoint_path.stat().st_size / (1024 * 1024)
                
                available_models.append({
                    "game": str(game_dir),
                    "filename": checkpoint_path.name,
                    "path": f"/app/checkpoints/{rel_path}",
                    "size_mb": round(size_mb, 2),
                    "has_config": has_config,
                    "format": checkpoint_path.suffix
                })
        
        return {
            "models": available_models,
            "count": len(available_models)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))