USE erp_db;

-- 근태 (Attendance) 테이블 추가
CREATE TABLE IF NOT EXISTS attendance (
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
