"""app/api/routes/goals.py — user career goals (dashboard widget)."""
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.database import get_db
from app.models.phase4_models import Goal
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/goals", tags=["Goals"])


class GoalCreate(BaseModel):
    title:       str = Field(..., min_length=1, max_length=200)
    target_date: str | None = Field(default=None, max_length=30)


class GoalUpdate(BaseModel):
    is_completed: bool | None = None
    title:        str | None = Field(default=None, max_length=200)


class GoalOut(BaseModel):
    id:           str
    title:        str
    target_date:  str | None
    is_completed: bool
    created_at:   str


def _out(g: Goal) -> GoalOut:
    return GoalOut(
        id=str(g.id), title=g.title, target_date=g.target_date,
        is_completed=g.is_completed, created_at=g.created_at.isoformat(),
    )


@router.get("", response_model=list[GoalOut], summary="List the user's goals")
async def list_goals(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[GoalOut]:
    rows = await db.execute(
        select(Goal).where(Goal.user_id == current_user.id).order_by(Goal.is_completed, desc(Goal.created_at))
    )
    return [_out(g) for g in rows.scalars().all()]


@router.post("", response_model=GoalOut, summary="Add a goal")
async def create_goal(
    body: GoalCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    goal = Goal(user_id=current_user.id, title=body.title.strip(), target_date=body.target_date)
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return _out(goal)


@router.patch("/{goal_id}", response_model=GoalOut, summary="Update / toggle a goal")
async def update_goal(
    goal_id: str,
    body: GoalUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GoalOut:
    try:
        gid = uuid.UUID(goal_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    goal = (await db.execute(
        select(Goal).where(Goal.id == gid, Goal.user_id == current_user.id)
    )).scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    if body.is_completed is not None:
        goal.is_completed = body.is_completed
    if body.title is not None and body.title.strip():
        goal.title = body.title.strip()
    await db.commit()
    await db.refresh(goal)
    return _out(goal)


@router.delete("/{goal_id}", summary="Delete a goal")
async def delete_goal(
    goal_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        gid = uuid.UUID(goal_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    await db.execute(delete(Goal).where(Goal.id == gid, Goal.user_id == current_user.id))
    await db.commit()
    return {"deleted": True}
