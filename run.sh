#!/bin/bash

# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

# --- Docker Compose로 MySQL 데이터베이스 시작 ---
echo "Starting MySQL database with Docker Compose..."
if ! docker-compose -f ./mysql-settings/docker-compose.yml up -d; then
    echo "Error: Failed to start Docker Compose services. Is Docker running?"
    exit 1
fi
echo "Database container started."

# 잠시 대기하여 DB가 완전히 시작되도록 함
sleep 10

# --- 가상환경 활성화 ---
echo "Activating Python virtual environment..."
if [ -f "erp/bin/activate" ]; then
    source erp/bin/activate
else
    echo "Error: Virtual environment not found. Please run setup script first."
    exit 1
fi
echo "Virtual environment activated."

# --- 파이썬 패키지 설치 ---
echo "Installing dependencies from requirements.txt..."
if ! pip install -r requirements.txt; then
    echo "Error: Failed to install dependencies."
    exit 1
fi
echo "Dependencies installed."

# --- FastAPI 애플리케이션 실행 ---
echo "Starting FastAPI application with Uvicorn..."
echo "Access the API at http://localhost:8000"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &

echo "Application is running in the background."
echo "To find the process ID, use: pgrep -f 'uvicorn main:app'"
echo "To stop the application, use: kill <PID>"
