import datetime
from typing import Optional
from fastapi import HTTPException
from sqlmodel import Session, select

from src.course.models import Course
from src.course.schemas import CourseCreate, CourseUpdate, CourseListResponse, CourseResponse

async def create_course(
    course_data: CourseCreate,
    session: Session
) -> CourseResponse:
    """建立新課程"""
    course = Course(
        course_name=course_data.course_name,
        description=course_data.description
    )
    
    session.add(course)
    session.commit()
    session.refresh(course)
    
    return CourseResponse(
        course_id=course.course_id,
        course_name=course.course_name,
        description=course.description,
        created_at=course.created_at,
        updated_at=course.updated_at
    )

async def get_course(
    course_id: int,
    session: Session
) -> CourseResponse:
    """取得特定課程"""
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return CourseResponse(
        course_id=course.course_id,
        course_name=course.course_name,
        description=course.description,
        created_at=course.created_at,
        updated_at=course.updated_at
    )

async def list_courses(
    session: Session,
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None
) -> CourseListResponse:
    """取得課程列表"""
    query = select(Course)
    
    if search:
        query = query.where(Course.course_name.contains(search))
    
    total = len(session.exec(query).all())
    courses = session.exec(query.offset(skip).limit(limit)).all()
    
    return CourseListResponse(
        total=total,
        courses=[
            CourseResponse(
                course_id=course.course_id,
                course_name=course.course_name,
                description=course.description,
                created_at=course.created_at,
                updated_at=course.updated_at
            )
            for course in courses
        ]
    )

async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    session: Session
) -> CourseResponse:
    """更新課程"""
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if course_data.course_name is not None:
        course.course_name = course_data.course_name
    if course_data.description is not None:
        course.description = course_data.description
    
    course.updated_at = datetime.datetime.now()
    session.add(course)
    session.commit()
    session.refresh(course)
    
    return CourseResponse(
        course_id=course.course_id,
        course_name=course.course_name,
        description=course.description,
        created_at=course.created_at,
        updated_at=course.updated_at
    )

async def delete_course(
    course_id: int,
    session: Session
):
    """刪除課程"""
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if course.chapters:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete course with existing chapters"
        )
    
    session.delete(course)
    session.commit()
