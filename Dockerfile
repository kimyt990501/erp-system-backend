# 1. 베이스 이미지 선택 (Python 3.11 슬림 버전)
FROM python:3.11-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 의존성 설치
# requirements.txt를 먼저 복사하여 Docker 캐시를 활용
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 프로젝트 전체 파일 복사
COPY . .

# 5. 컨테이너 외부로 노출할 포트 설정
EXPOSE 8000

# 6. 애플리케이션 실행
# 0.0.0.0 호스트를 사용하여 컨테이너 외부에서 접근 가능하도록 설정
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
