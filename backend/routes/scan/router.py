from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.dependencies import get_tenant_db, require_doctor
from core.exceptions import BadRequestException, NotFoundException
from routes.scan.schemas import ScanCreateSchema
from routes.scan.service import create_scan, delete_scan, get_scan, list_scans

router = APIRouter(prefix="/scans", tags=["Scans"])

# ── Security: upload directory boundary and allowed file types ──────────────
UPLOAD_ROOT = Path("uploads").resolve()
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".dcm", ".dicom"}
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB


def _safe_file_path(stored_path: str) -> Path:
    """Resolve a stored path and ensure it stays within the uploads directory."""
    resolved = Path(stored_path).resolve()
    if not resolved.is_relative_to(UPLOAD_ROOT):
        raise NotFoundException("File not found")
    if not resolved.exists():
        raise NotFoundException("File not found")
    return resolved


@router.post("/")
async def create(
    data: ScanCreateSchema,
    user: dict = Depends(require_doctor),
    tenant_db: AsyncIOMotorDatabase = Depends(get_tenant_db),
):
    return await create_scan(data.model_dump(), user["email"], tenant_db)


@router.get("/")
async def list_all(
    patient_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(require_doctor),
    tenant_db: AsyncIOMotorDatabase = Depends(get_tenant_db),
):
    return await list_scans(tenant_db, patient_id, skip=skip, limit=limit)


@router.get("/{scan_id}")
async def get_one(
    scan_id: str,
    user: dict = Depends(require_doctor),
    tenant_db: AsyncIOMotorDatabase = Depends(get_tenant_db),
):
    return await get_scan(scan_id, tenant_db)


@router.get("/{scan_id}/image")
async def get_image(
    scan_id: str,
    user: dict = Depends(require_doctor),
    tenant_db: AsyncIOMotorDatabase = Depends(get_tenant_db),
):
    scan = await get_scan(scan_id, tenant_db)
    image_path = scan.get("image_path")
    if not image_path:
        raise NotFoundException("Scan image not found.")

    safe_path = _safe_file_path(image_path)

    suffix = safe_path.suffix.lower()
    media_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".dcm": "application/dicom",
        ".dicom": "application/dicom",
    }.get(suffix, "application/octet-stream")

    return FileResponse(
        path=str(safe_path),
        media_type=media_type,
        filename=safe_path.name,
    )


@router.post("/{scan_id}/upload")
async def upload_image(
    scan_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(require_doctor),
    tenant_db: AsyncIOMotorDatabase = Depends(get_tenant_db),
):
    # ── Ensure the scan exists in this tenant before accepting an upload ──────
    scan = await tenant_db.scans.find_one({"scan_id": scan_id}, {"_id": 1})
    if not scan:
        raise NotFoundException("Scan")

    # ── Validate file type ──────────────────────────────────────────────────
    suffix = Path(file.filename).suffix.lower() if file.filename else ""
    if suffix not in ALLOWED_EXTENSIONS:
        raise BadRequestException(
            f"File type '{suffix}' not allowed. Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    if file.content_type and not (
        file.content_type.startswith("image/")
        or file.content_type == "application/dicom"
        or file.content_type == "application/octet-stream"
    ):
        raise BadRequestException("Only image files are allowed")

    tenant_id = user["tenant_id"]

    # Build a safe directory and write the file to disk
    upload_dir = UPLOAD_ROOT / tenant_id / scan_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = Path(file.filename).name  # strip any path components
    dest = upload_dir / safe_filename

    # ── Stream to disk with an enforced size cap to prevent unbounded uploads ─
    bytes_written = 0
    chunk_size = 1024 * 1024  # 1 MB
    try:
        with dest.open("wb") as out:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                bytes_written += len(chunk)
                if bytes_written > MAX_UPLOAD_SIZE:
                    raise BadRequestException(
                        f"File exceeds the maximum allowed size of "
                        f"{MAX_UPLOAD_SIZE // (1024 * 1024)} MB."
                    )
                out.write(chunk)
    except BadRequestException:
        # Remove the partial file so we don't leave truncated uploads on disk
        dest.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    image_path = str(dest)
    await tenant_db.scans.update_one(
        {"scan_id": scan_id},
        {"$set": {"image_path": image_path, "status": "uploaded"}},
    )
    return {"message": "Image uploaded", "path": image_path}


@router.delete("/{scan_id}")
async def delete(
    scan_id: str,
    user: dict = Depends(require_doctor),
    tenant_db: AsyncIOMotorDatabase = Depends(get_tenant_db),
):
    await delete_scan(scan_id, tenant_db)
    return {"message": "Scan deleted"}
