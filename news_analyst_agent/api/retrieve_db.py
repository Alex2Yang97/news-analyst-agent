import json
from loguru import logger
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from langchain_core.messages.base import BaseMessage
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from news_analyst_agent.db.database import get_db
from news_analyst_agent.db.models import User, Thread, Step, Feedback
from news_analyst_agent.api.auth import verify_admin

router = APIRouter()


# Thread endpoints
@router.get("/threads", response_model=List[dict], tags=["Threads"])
async def get_threads(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin)
):
    """Get all threads with pagination"""
    query = select(Thread).offset(skip).limit(limit)
    result = await db.execute(query)
    threads = result.scalars().all()
    
    return [
        {
            "id": str(thread.id),
            "name": thread.name,
            "createdAt": thread.createdAt,
            "userIdentifier": thread.userIdentifier,
            "tags": thread.tags,
            "metadata": thread.metadata_
        }
        for thread in threads
    ]

@router.get("/threads/{thread_id}", response_model=dict, tags=["Threads"])
async def get_thread(
    thread_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin)
):
    """Get a specific thread by ID"""
    query = select(Thread).where(Thread.id == thread_id)
    result = await db.execute(query)
    thread = result.scalar_one_or_none()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    return {
        "id": str(thread.id),
        "name": thread.name,
        "createdAt": thread.createdAt,
        "userIdentifier": thread.userIdentifier,
        "tags": thread.tags,
        "metadata": thread.metadata_
    }

# Step endpoints
@router.get("/threads/{thread_id}/steps", response_model=List[dict], tags=["Steps"])
async def get_thread_steps(
    thread_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin)
):
    """Get all steps for a specific thread"""
    query = select(Step).where(Step.threadId == thread_id)
    result = await db.execute(query)
    steps = result.scalars().all()
    
    return [
        {
            "id": str(step.id),
            "name": step.name,
            "type": step.type,
            "input": step.input,
            "output": step.output,
            "createdAt": step.createdAt,
            "isError": step.isError,
            "metadata": step.metadata_
        }
        for step in steps
    ]

@router.get("/steps/{step_id}", response_model=dict, tags=["Steps"])
async def get_step(
    step_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin)
):
    """Get a specific step by ID"""
    query = select(Step).where(Step.id == step_id)
    result = await db.execute(query)
    step = result.scalar_one_or_none()
    
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    
    return {
        "id": str(step.id),
        "name": step.name,
        "type": step.type,
        "input": step.input,
        "output": step.output,
        "createdAt": step.createdAt,
        "isError": step.isError,
        "metadata": step.metadata_
    }

# Feedback endpoints
@router.get("/threads/{thread_id}/feedbacks", response_model=List[dict], tags=["Feedback"])
async def get_thread_feedbacks(
    thread_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin)
):
    """Get all feedbacks for a specific thread"""
    query = select(Feedback).where(Feedback.threadId == thread_id)
    result = await db.execute(query)
    feedbacks = result.scalars().all()
    
    return [
        {
            "id": str(feedback.id),
            "forId": str(feedback.forId),
            "value": feedback.value,
            "comment": feedback.comment
        }
        for feedback in feedbacks
    ]

@router.get("/feedbacks/{feedback_id}", response_model=dict, tags=["Feedback"])
async def get_feedback(
    feedback_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin)
):
    """Get a specific feedback by ID"""
    query = select(Feedback).where(Feedback.id == feedback_id)
    result = await db.execute(query)
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    return {
        "id": str(feedback.id),
        "forId": str(feedback.forId),
        "value": feedback.value,
        "comment": feedback.comment
    }