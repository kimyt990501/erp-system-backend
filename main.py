from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 라우터 임포트
from api import auth, users, leave, salary, attendance
from scheduler.jobs import scheduler

app = FastAPI(
    title="ERP API",
    description="회사 ERP 웹을 위한 백엔드 API",
    version="0.1.0"
)

# --- 미들웨어 설정 ---
# (중요) Vue.js 프론트엔드와 통신하기 위한 CORS 설정
# 지금은 모든 출처(*)를 허용 (개발용)
# 나중에 Vue 앱 주소만 허용 (예: "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 라우터 포함 ---
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(leave.router)
app.include_router(salary.router)
app.include_router(attendance.router)

# --- 스케줄러 시작/종료 이벤트 ---
@app.on_event("startup")
async def startup_event():
    scheduler.start()
    print("Scheduler started...")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("Scheduler shut down...")

# --- 기본 루트 ---
@app.get("/")
def read_root():
    return {"message": "Welcome to ERP API"}