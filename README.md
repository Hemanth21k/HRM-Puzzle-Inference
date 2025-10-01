# AI Sudoku Solver - Docker Quick Start 🐳

This guide will help you run the entire application using Docker in just a few steps.

## 📋 Prerequisites

1. **Docker Desktop** (includes Docker Compose)
   - [Windows/Mac](https://www.docker.com/products/docker-desktop)
   - [Linux](https://docs.docker.com/engine/install/)

2. **NVIDIA GPU (Optional but Recommended)**
   - [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

3. **Model Files**
   - Your trained model checkpoint (`.pt` or `.pth` file)
   - Configuration file (`all_config.yaml`)

## 🚀 Quick Start (3 Steps)

### Step 1: Organize Your Files

```
sudoku-solver/
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── main.py
│   ├── requirements.txt
│   └── pretrain.py
├── frontend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── nginx.conf
│   ├── index.html
│   ├── scripts.js
│   └── styles.css
├── checkpoints/               ← Organize by game/model type!
│   ├── sudoku-1k/
│   │   ├── step_10000.pt     ← Your checkpoint (any format)
│   │   └── all_config.yaml
│   ├── sudoku-10k/
│   │   └── checkpoint.pth
│   └── other-game/
│       └── model.ckpt
├── docker-compose.yml
└── docker-start.sh
```

### Step 2: Place Your Checkpoints

Organize your checkpoints by game/type in subdirectories:

```bash
# Create directory structure
mkdir -p checkpoints/sudoku-1k
mkdir -p checkpoints/sudoku-10k
mkdir -p checkpoints/other-game

# Copy your checkpoints (supports .pt, .pth, .ckpt, and other formats)
cp /path/to/your/checkpoint.pt checkpoints/sudoku-1k/
cp /path/to/your/all_config.yaml checkpoints/sudoku-1k/

# Example for other games
cp /path/to/other/model.pth checkpoints/other-game/
cp /path/to/other/config.yaml checkpoints/other-game/
```

**Supported checkpoint formats:**
- `.pt` (PyTorch)
- `.pth` (PyTorch)
- `.ckpt` (Checkpoint)
- Any other format your model uses

### Step 3: Run!

**Linux/Mac:**
```bash
chmod +x docker-start.sh
./docker-start.sh
```

**Windows:**
```bash
docker-start.bat
```

**Or manually:**
```bash
docker-compose up --build
```

That's it! 🎉

## 🌐 Access the Application

Once running:
- **Frontend UI**: http://localhost
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📝 How to Use

1. Open http://localhost in your browser
2. Enter the checkpoint path using the format: `/app/models/<game>/<checkpoint-file>`
   
   **Examples:**
   - `/app/models/sudoku-1k/step_10000.pt`
   - `/app/models/sudoku-1k/checkpoint_5000.pth`
   - `/app/models/sudoku-10k/model_best.ckpt`
   - `/app/models/other-game/final_model.pt`

3. Click **Initialize Solver**
4. Choose either:
   - **Solve One Step**: See each step of the solving process
   - **Auto Solve**: Watch it solve automatically with animations

## 🎮 Adding More Games/Models

The structure supports multiple games and models:

```bash
checkpoints/
├── sudoku-1k/          # Sudoku with 1k training samples
├── sudoku-10k/         # Sudoku with 10k training samples
├── chess-puzzles/      # Chess puzzles (future)
├── rubiks-cube/        # Rubik's cube solver (future)
└── your-game/          # Your custom game
```

Each subdirectory should contain:
- Model checkpoint file (any format: .pt, .pth, .ckpt, etc.)
- Configuration file (all_config.yaml)

## 🛠️ Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

### Stop Services
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
```

### Rebuild After Changes
```bash
docker-compose up --build
```

### Run in Background (Detached Mode)
```bash
./docker-start.sh --detach
# or
docker-compose up -d
```

## 🐛 Troubleshooting

### Issue: "Cannot connect to Docker daemon"

**Solution:**
- Make sure Docker Desktop is running
- On Linux: `sudo systemctl start docker`
- Add your user to docker group: `sudo usermod -aG docker $USER`

### Issue: "Port 80 is already in use"

**Solution:** Change the frontend port in `docker-compose.yml`:
```yaml
frontend:
  ports:
    - "8080:80"  # Use port 8080 instead
```
Then access via http://localhost:8080

### Issue: "Port 8000 is already in use"

**Solution:** Change the backend port in `docker-compose.yml`:
```yaml
backend:
  ports:
    - "8001:8000"  # Use port 8001 instead
```
Also update `scripts.js`:
```javascript
const API_BASE_URL = 'http://localhost:8001';
```

### Issue: GPU not detected

**Solutions:**
1. **Check if NVIDIA driver is installed:**
   ```bash
   nvidia-smi
   ```

2. **Install NVIDIA Container Toolkit:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y nvidia-container-toolkit
   sudo systemctl restart docker
   ```

3. **Test GPU access:**
   ```bash
   docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
   ```

4. **If GPU still doesn't work, run in CPU mode:**
   - Remove the `deploy` section from `docker-compose.yml`
   - Modify your