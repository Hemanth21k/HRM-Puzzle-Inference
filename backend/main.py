from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import yaml
import os
import torch
import asyncio
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

class SudokuRequest(BaseModel):
    puzzle: List[List[int]]
    checkpoint_path: str  # Can be .pt, .pth, or any checkpoint format

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
                                    dtype=torch.long).unsqueeze(0).cuda()
        
        # Create batch
        batch = {
            "inputs": puzzle_tensor,
            "labels": puzzle_tensor.clone(),  # Placeholder
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
            carry, _, metrics, preds, all_finish = model_state.model(
                carry=session["carry"],
                batch=session["batch"],
                return_keys=config.eval_save_outputs
            )
            
            # Get predictions
            pred_outs = torch.argmax(preds["logits"], dim=-1)
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

@app.get("/api/models")
async def list_available_models():
    """List all available models in the models directory"""
    try:
        import glob
        from pathlib import Path
        
        models_dir = Path("/app/models")
        if not models_dir.exists():
            return {"models": [], "message": "Models directory not found"}
        
        available_models = []
        
        # Search for checkpoint files
        patterns = ["*.pt", "*.pth", "*.ckpt"]
        for pattern in patterns:
            for checkpoint_path in models_dir.rglob(pattern):
                rel_path = checkpoint_path.relative_to(models_dir)
                game_dir = rel_path.parent
                
                # Check if config exists
                config_path = models_dir / game_dir / "all_config.yaml"
                has_config = config_path.exists()
                
                # Get file size
                size_mb = checkpoint_path.stat().st_size / (1024 * 1024)
                
                available_models.append({
                    "game": str(game_dir),
                    "filename": checkpoint_path.name,
                    "path": f"/app/models/{rel_path}",
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