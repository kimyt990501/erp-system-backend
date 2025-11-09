# ERP 백엔드 API

## 설명

이 프로젝트는 ERP(전사적 자원 관리) 웹 애플리케이션을 위한 백엔드 API입니다. Python과 FastAPI로 구축되었으며, 다양한 회사 리소스를 관리하기 위한 엔드포인트를 제공합니다.

## 주요 기능

- 사용자 인증 (JWT 기반)
- 사용자 관리
- 출퇴근 기록 관리
- 휴가 관리
- 급여 관리
- 자동화된 작업을 위한 스케줄링

## 사용 기술

- **백엔드:** Python, FastAPI
- **데이터베이스:** MySQL (Docker로 관리)
- **ORM:** SQLModel
- **비동기 DB 드라이버:** AsyncMy
- **인증:** python-jose, passlib
- **작업 스케줄링:** APScheduler
- **환경 설정:** pydantic-settings

## 설정 및 설치

### 1. 저장소 복제

```bash
git clone <repository-url>
cd erp_backend
```

### 2. 가상 환경 생성 및 활성화

가상 환경 사용을 권장합니다.

```bash
python -m venv erp
source erp/bin/activate
```

### 3. 의존성 설치

`requirements.txt` 파일로부터 필요한 모든 패키지를 설치합니다.

```bash
pip install -r requirements.txt
```

### 4. 데이터베이스 설정

이 프로젝트는 Docker를 사용하여 MySQL 데이터베이스를 실행합니다.

- Docker가 설치되어 있고 실행 중인지 확인하세요.
- `mysql-settings` 디렉토리로 이동합니다.
- 다음 명령을 실행하여 데이터베이스 컨테이너를 시작합니다.

```bash
cd mysql-settings
docker-compose up -d
```

이 명령은 `my-erp-mysql`이라는 이름의 MySQL 컨테이너와 `erp_db`라는 데이터베이스를 생성합니다. 초기 스키마는 `init.sql` 파일로부터 생성됩니다.

### 5. 환경 변수 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성합니다. 아래 예시 내용을 복사하고 필요한 경우 수정하세요.

```env
DATABASE_URL=mysql+asyncmy://root:kyt0501@127.0.0.1:3306/erp_db

# JWT 비밀 키 (복잡한 임의의 문자열로 변경하세요)
# 예: openssl rand -hex 32
SECRET_KEY=thisiserpweb
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## 애플리케이션 실행

이 프로젝트는 실행 과정을 자동화하는 셸 스크립트를 제공합니다. 또는 수동으로 각 단계를 실행할 수도 있습니다.

### 1. 셸 스크립트를 이용한 실행 (권장)

Linux 및 macOS 환경에서는 `run.sh` 스크립트를 사용하여 데이터베이스 시작, 의존성 설치, 애플리케이션 실행을 한 번에 처리할 수 있습니다.

먼저 스크립트에 실행 권한을 부여합니다.

```bash
chmod +x run.sh
```

그런 다음 스크립트를 실행합니다.

```bash
./run.sh
```

이 스크립트는 다음 작업을 자동으로 수행합니다:
1. Docker Compose를 사용하여 MySQL 데이터베이스를 백그라운드에서 시작합니다.
2. Python 가상 환경을 활성화합니다.
3. `requirements.txt`에 명시된 의존성을 설치합니다.
4. Uvicorn을 사용하여 FastAPI 애플리케이션을 백그라운드에서 실행합니다.

애플리케이션이 백그라운드에서 실행되며, 로그를 통해 진행 상황을 확인할 수 있습니다. 실행 중인 프로세스를 중지하려면 다음 명령어를 사용하세요.

```bash
# 프로세스 ID 찾기
pgrep -f 'uvicorn main:app'

# 찾은 PID를 사용하여 프로세스 종료
kill <PID>
```

### 2. 수동 실행

설정이 완료되면 Uvicorn을 사용하여 FastAPI 애플리케이션을 직접 실행할 수 있습니다.

```bash
uvicorn main:app --reload
```

---

두 방법 중 하나로 실행하면 API는 `http://127.0.0.1:8000`에서 사용할 수 있습니다.

## API 엔드포인트

API는 다음 라우터를 제공합니다:

- `/auth`: 사용자 인증 및 토큰 생성을 처리합니다.
- `/users`: 사용자 정보를 관리합니다.
- `/leave`: 휴가 요청을 처리합니다.
- `/salary`: 급여 데이터를 관리합니다.
- `/attendance`: 직원 출퇴근을 기록합니다.

`http://127.0.0.1:8000/docs`에서 대화형 API 문서(Swagger UI)에 접근할 수 있습니다.