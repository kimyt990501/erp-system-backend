-- User 테이블에 role 컬럼 추가
-- 실행 방법: mysql -u root -p erp_db < migration_add_role.sql

USE erp_db;

-- 1. role 컬럼 추가 (기본값: 'user')
ALTER TABLE user
ADD COLUMN role VARCHAR(20) DEFAULT 'user' COMMENT '사용자 권한 (user 또는 admin)';

-- 2. 기존 사용자들의 role을 'user'로 설정 (이미 기본값으로 설정되지만 명시적으로 업데이트)
UPDATE user SET role = 'user' WHERE role IS NULL;

-- 3. 필요시 특정 사용자를 관리자로 설정 (예시)
-- UPDATE user SET role = 'admin' WHERE email = 'admin@example.com';

SELECT '마이그레이션 완료: role 컬럼이 추가되었습니다.' AS message;
