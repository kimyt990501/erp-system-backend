import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import select, update
from sqlmodel.ext.asyncio.session import AsyncSession
from db.database import engine # 메인 엔진을 공유
from db.models import User, LeaveBalance
from datetime import date

logger = logging.getLogger(__name__)

async def add_monthly_leave_job():
    """
    매월 1일, 1년 미만 재직자에게 연차 1일 부여 (예시 로직)
    """
    logger.info("Starting monthly leave job...")
    
    # 스케줄러는 별도 세션 필요
    async with AsyncSession(engine) as session:
        try:
            today = date.today()
            
            # 1. 1년 미만 재직자(is_active=True) 찾기
            one_year_ago = today.replace(year=today.year - 1)
            
            stmt = select(User).where(
                User.is_active == True,
                User.hire_date > one_year_ago 
            )
            users_to_update = await session.exec(stmt)
            user_ids = [user.id for user in users_to_update]

            if not user_ids:
                logger.info("No users to update for monthly leave.")
                return

            # 2. 해당 유저들의 연차 1일 증가
            update_stmt = update(LeaveBalance)\
                .where(LeaveBalance.user_id.in_(user_ids))\
                .values(total_granted=LeaveBalance.total_granted + 1.0)
                
            await session.exec(update_stmt)
            await session.commit()
            
            logger.info(f"Successfully added leave for {len(user_ids)} users.")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error in monthly leave job: {e}")
        

# 스케줄러 객체 생성
scheduler = AsyncIOScheduler()

# 매월 1일 0시 1분에 실행되도록 등록
scheduler.add_job(add_monthly_leave_job, 'cron', month='*', day=1, hour=0, minute=1)