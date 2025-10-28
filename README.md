# Finding Tickers

A full-stack application for enriching CSV files with stock ticker symbols using the Finnhub API.
<img width="1880" height="884" alt="image" src="https://github.com/user-attachments/assets/b29d228c-2d54-4a68-8e84-3614337eada8" />

<img width="1818" height="941" alt="image" src="https://github.com/user-attachments/assets/fce069c9-f5d9-4488-8d9a-874b9085b3bf" />



## Features

- Upload CSV files with company names
- Automatically fetch stock ticker symbols
- Beautiful, modern web interface with stock market theme
- Download enriched CSV files
- Multi-threaded processing for speed
- Real-time progress tracking
- Single company lookup
- Docker support for easy deployment

## Architecture

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: React + TypeScript + Tailwind CSS + Vite
- **API**: Finnhub Stock API
- **Containerization**: Docker & Docker Compose

## Prerequisites

### Required
- **Docker** and **Docker Compose** (Recommended)
- **Finnhub API key** (Free at [finnhub.io](https://finnhub.io))

### Optional (for local development)
- Python 3.11+
- Node.js 18+
- npm

## 🚀 Quick Start (Recommended)


1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Finding_tickers
   ```

2. **Set up environment variables**
   ```bash
   # Create .env file in backend directory
   cd backend
   cp .env.example .env 
   
   # Or create .env manually
   echo "FINNHUB_API_KEY=your_api_key_here" > .env
   ```

3. **Make start script executable and run**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```
   
4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### **Option 1: Quick Start Script** ⚡
```bash
# Clone the repository
git clone <repository-url>
cd Finding_tickers

# Set up environment variables
echo "FINNHUB_API_KEY=your_api_key_here" > backend/.env

# Make start script executable and run
chmod +x start.sh
./start.sh
```

### **Option 2: Manual Docker Compose** 🐳
```bash
# Build and start all services
docker compose build
docker compose up
```

### **Option 3: Local Development** 💻
```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FINNHUB_API_KEY=your_api_key_here
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (in new terminal)
cd frontend
npm install
npm run dev
```

### **Access the Application**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
   

## 🔑 Environment Configuration

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Required
FINNHUB_API_KEY=your_finnhub_api_key_here
```


## 📚 Documentation

### **Complete Documentation Suite**
- **📋 Complete Project Summary**: `agent/complete_project_summary.md` - High-level overview and quick start
- **🔧 Backend Documentation**: `agent/project_documentation.md` - Complete backend architecture
- **🎨 Frontend Documentation**: `agent/frontend_documentation.md` - React application details

### **Quick Reference**
- **API Docs**: http://localhost:8000/docs (when running)
- **Health Check**: http://localhost:8000/health
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000

---

### Running Tests

**Backend Tests:**
```bash
cd backend
source .venv/bin/activate
pytest tests/
```

**Frontend Build:**
```bash
cd frontend
npm run build
```

### Docker Commands

**Start services:**
```bash
docker compose up
```

**Build and start:**
```bash
docker compose up --build
```

**Stop services:**
```bash
docker compose down
```

**View logs:**
```bash
docker compose logs -f
```
