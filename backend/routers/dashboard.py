from fastapi import APIRouter, Depends, Query
from backend.schemas.dashboard import StudentDashboardView, TeacherDashboardView
from backend.services.dashboard import get_student_dashboard, get_teacher_dashboard
from backend.services.auth import get_current_actor


router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/student", response_model=StudentDashboardView)
async def student_dashboard(
    university_id: str = Query("UNI001"),
    actor=Depends(get_current_actor),
):
    result = await get_student_dashboard(actor, university_id=university_id)
    return result


@router.get("/dashboard/teacher", response_model=TeacherDashboardView)
async def teacher_dashboard(
    university_id: str = Query("UNI001"),
    course_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    actor=Depends(get_current_actor),
):
    result = await get_teacher_dashboard(
        actor,
        university_id=university_id,
        course_id=course_id,
        page=page,
        page_size=page_size,
    )
    return result

