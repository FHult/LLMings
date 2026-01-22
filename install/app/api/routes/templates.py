"""Council template routes."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sql_delete
from pydantic import BaseModel
from typing import Optional
import json
import uuid

from app.core.database import get_db
from app.models.council_template import CouncilTemplate

router = APIRouter()


class SaveTemplateRequest(BaseModel):
    """Request to save a council template."""
    name: str
    description: Optional[str] = None
    members: list[dict]


class TemplateResponse(BaseModel):
    """Council template response."""
    id: str
    name: str
    description: Optional[str]
    members: list[dict]
    created_at: Optional[str]
    updated_at: Optional[str]


@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates(db: AsyncSession = Depends(get_db)):
    """List all saved council templates."""
    result = await db.execute(
        select(CouncilTemplate).order_by(CouncilTemplate.updated_at.desc())
    )
    templates = result.scalars().all()
    return [template.to_dict() for template in templates]


@router.post("/templates", response_model=TemplateResponse)
async def save_template(request: SaveTemplateRequest, db: AsyncSession = Depends(get_db)):
    """Save a new council template."""
    template_id = str(uuid.uuid4())

    template = CouncilTemplate(
        id=template_id,
        name=request.name,
        description=request.description,
        members_json=json.dumps(request.members)
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)

    return template.to_dict()


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific council template."""
    result = await db.execute(
        select(CouncilTemplate).filter(CouncilTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template.to_dict()


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a council template."""
    result = await db.execute(
        select(CouncilTemplate).filter(CouncilTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    await db.delete(template)
    await db.commit()

    return {"message": "Template deleted successfully"}


@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    request: SaveTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing council template."""
    result = await db.execute(
        select(CouncilTemplate).filter(CouncilTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    template.name = request.name
    template.description = request.description
    template.members_json = json.dumps(request.members)

    await db.commit()
    await db.refresh(template)

    return template.to_dict()
