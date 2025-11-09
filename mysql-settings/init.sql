USE erp_db;

-- 1. 회원 (User) 테이블
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    hire_date DATE NOT NULL COMMENT '입사일',
    is_active BOOLEAN DEFAULT TRUE COMMENT '재직/퇴사 여부',
    role VARCHAR(20) DEFAULT 'user' COMMENT '사용자 권한 (user 또는 admin)'
) COMMENT '회원 정보';

-- 2. 연차 현황 (LeaveBalance) 테이블
CREATE TABLE leave_balance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '회원 ID',
    total_granted FLOAT DEFAULT 0.0 COMMENT '총 부여된 연차',
    total_used FLOAT DEFAULT 0.0 COMMENT '총 사용한 연차',
    FOREIGN KEY (user_id) REFERENCES user(id)
) COMMENT '연차 현황';

-- 3. 연차 신청 내역 (LeaveRequest) 테이블
CREATE TABLE leave_request (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    start_date DATE NOT NULL COMMENT '연차 시작일',
    end_date DATE NOT NULL COMMENT '연차 종료일',
    days_used FLOAT NOT NULL COMMENT '신청 일수 (0.5, 1.0 등)',
    reason TEXT COMMENT '신청 사유',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '상태 (pending, approved, rejected)',
    FOREIGN KEY (user_id) REFERENCES user(id)
) COMMENT '연차 신청 내역';

-- 4. 급여 명세서 (SalaryStatement) 테이블
CREATE TABLE salary_statement (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pay_month VARCHAR(7) NOT NULL COMMENT '지급 연월 (예: 2025-10)',
    base_pay INT NOT NULL COMMENT '기본급',
    bonus INT DEFAULT 0 COMMENT '상여금',
    deductions INT DEFAULT 0 COMMENT '공제액 (4대보험, 소득세 등)',
    net_pay INT NOT NULL COMMENT '실수령액',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '사용자가 입력한 시점',
    FOREIGN KEY (user_id) REFERENCES user(id)
) COMMENT '급여 명세서';

-- 5. 근태 (Attendance) 테이블
CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    work_date DATE NOT NULL COMMENT '근무일',
    check_in TIME COMMENT '출근 시각',
    check_out TIME COMMENT '퇴근 시각',
    status VARCHAR(20) DEFAULT 'present' COMMENT '상태 (present, late, early_leave, absent)',
    notes TEXT COMMENT '비고',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시점',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정 시점',
    FOREIGN KEY (user_id) REFERENCES user(id),
    INDEX idx_user_date (user_id, work_date),
    UNIQUE KEY unique_user_date (user_id, work_date)
) COMMENT '근태 기록';