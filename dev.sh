#!/usr/bin/env bash
set -e

# ForgePipeline AI - Development startup script
# Runs both backend and frontend in parallel

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  ForgePipeline AI - Development Server${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check dependencies
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}python3 is required${NC}"; exit 1; }
command -v node >/dev/null 2>&1 || { echo -e "${RED}node is required${NC}"; exit 1; }

# Install backend deps if needed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${GREEN}Installing backend dependencies...${NC}"
    pip install -q -r backend/requirements.txt -r requirements.txt
fi

# Install frontend deps if needed
if [ ! -d "node_modules" ]; then
    echo -e "${GREEN}Installing frontend dependencies...${NC}"
    npm install
fi

cleanup() {
    echo -e "\n${CYAN}Shutting down...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# Start backend
echo -e "${GREEN}Starting backend on http://localhost:8080${NC}"
cd backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo -e "${CYAN}Waiting for backend...${NC}"
for i in {1..20}; do
    if curl -sf http://localhost:8080/api/health >/dev/null 2>&1; then
        echo -e "${GREEN}Backend ready${NC}"
        break
    fi
    sleep 0.5
done

# Start frontend
echo -e "${GREEN}Starting frontend on http://localhost:5173${NC}"
npx vite --host &
FRONTEND_PID=$!

echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  ${GREEN}Frontend:${NC} http://localhost:5173"
echo -e "  ${GREEN}Backend:${NC}  http://localhost:8080"
echo -e "  ${GREEN}API Docs:${NC} http://localhost:8080/docs"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  Press Ctrl+C to stop\n"

wait
