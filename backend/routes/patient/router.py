from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.dependencies import get_tenant_db, require_doctor
from routes.patient.schemas import PatientCreateSchema, PatientUpdateSchema
from routes.patient.service import (
    create_patient,
    delete_patient,
    get_patient,
    list_patients,
    update_patient,
)

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post("/")
async def create(
    data: PatientCreateSchema,
    user: dict = Depends(require_doctor),
    tenant_db: AsyncIOMotorDatabase = Depends(get_tenant_db),
):
    return await create_patient(data.model_dump(), user["email"], tenant_db)


@router.get("/")
async def list_all(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(require_doctor),
    tenant_db: AsyncIOMotorDatabase = Depends(get_tenant_db),
):
    return await list_patients(tenant_db, skip=skip, limit=limit)


@router.get("/{patient_id}")
async def get_one(
    patient_id: str,
    user: dict = Depends(require_doctor),
    tenant_db: AsyncIOMotorDatabase = Depends(get_tenant_db),
):
    return await get_patient(patient_id, tenant_db)


@router.patch("/{patient_id}")
async def update(
    patient_id: str,
    data: PatientUpdateSchema,
    user: dict = Depends(require_doctor),
    tenant_db: AsyncIOMotorDatabase = Depends(get_tenant_db),
):
    return await update_patient(patient_id, data.model_dump(exclude_none=True), tenant_db)


@router.delete("/{patient_id}")
async def delete(
    patient_id: str,
    user: dict = Depends(require_doctor),
    tenant_db: AsyncIOMotorDatabase = Depends(get_tenant_db),
):
    await delete_patient(patient_id, tenant_db)
    return {"message": "Patient deleted"}
