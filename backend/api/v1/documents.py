import os
import shutil
import uuid
import io
from pathlib import Path
import pandas as pd

from fastapi import APIRouter, HTTPException, UploadFile, File, status, Depends
from fastapi.responses import JSONResponse, StreamingResponse

from ml_pipeline.engine import process_document
from api.dependencies import get_db
from database.repository import DocumentRepository
from core.config import settings

router = APIRouter(prefix="/documents", tags=["documents"])

# Where uploaded files are temporarily stored
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

GEMINI_API_KEY = settings.GEMINI_API_KEY


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/documents/process
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/process")
async def process_document_route(file: UploadFile = File(...), db = Depends(get_db)):
    """
    Upload a melt-certificate PDF and return the extracted chemical data.

    Success (200):
        { "status": "success", "data": { "chemical_composition": [...], ... } }

    Client error / AI error (400):
        { "status": "error", "message": "..." }

    Server error (500):
        { "status": "error", "message": "..." }
    """
    # ── Validate file type ────────────────────────────────────────────────────
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted.",
        )

    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GEMINI_API_KEY is not configured on the server.",
        )

    # ── Save upload to disk ───────────────────────────────────────────────────
    safe_name = f"{uuid.uuid4().hex}.pdf"
    save_path  = UPLOAD_DIR / safe_name
    try:
        with save_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {exc}",
        )

    # ── Run ML pipeline ───────────────────────────────────────────────────────
    result = process_document(str(save_path), GEMINI_API_KEY)

    # ── Clean up temp file (best-effort) ──────────────────────────────────────
    try:
        save_path.unlink(missing_ok=True)
    except Exception:
        pass   # not critical

    # ── Map engine result to HTTP response ────────────────────────────────────
    if result.get("status") == "success":
        # Save to database (MongoDB with automatic local JSON fallback)
        try:
            repo = DocumentRepository(db)
            task_id = uuid.uuid4().hex
            await repo.save_document(task_id, result.get("data"))
        except Exception as db_exc:
            # log or handle db write error but do not block return of success to user
            print(f"Failed to save processed document to repository: {db_exc}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result,
        )

    # Engine returned an error — decide on 400 vs 500
    message = result.get("message", "Unknown error from ML pipeline.")

    # 503 / network errors from Gemini are the server's problem, not the client's
    is_server_fault = any(
        kw in message.lower()
        for kw in ("503", "unavailable", "network", "timeout", "conversion failed")
    )
    http_code = (
        status.HTTP_503_SERVICE_UNAVAILABLE if "503" in message
        else status.HTTP_500_INTERNAL_SERVER_ERROR if is_server_fault
        else status.HTTP_400_BAD_REQUEST
    )

    return JSONResponse(
        status_code=http_code,
        content={"status": "error", "message": message},
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/documents
# ─────────────────────────────────────────────────────────────────────────────

@router.get("")
async def get_all_processed_documents(db = Depends(get_db)):
    """
    Retrieves all processed document records from the database or local file fallback.
    """
    try:
        repo = DocumentRepository(db)
        records = await repo.get_all_documents()
        return records
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve records: {str(e)}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/documents/export
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/export")
async def export_all_data_to_excel(db = Depends(get_db)):
    """
    Aggregates all processed document records and dynamically builds a multi-sheet Excel file 
    mapped to the Induction Furnace schema. Works with local fallback too.
    """
    try:
        repo = DocumentRepository(db)
        records = await repo.get_all_documents()
        
        summary_data = []
        chemical_data = []
        material_data = []

        for record in records:
            # Handle standard nested database wrapper if present, otherwise assume raw dump
            data = record.get("extracted_data", record)
            if not isinstance(data, dict):
                continue
            
            header = data.get("header", {})
            melt_no = header.get("melt_number", "UNKNOWN")
            
            time_energy = data.get("time_and_energy", {})
            process = data.get("process_parameters", {})
            yield_dispatch = data.get("yield_and_dispatch", {})

            # 1. Build Summary Row
            summary_data.append({
                "Melt Number": melt_no,
                "Date": header.get("date", ""),
                "Grade": header.get("grade", ""),
                "Crucible No": header.get("crucible_no", ""),
                "Furnace Started": time_energy.get("furnace_started_at", ""),
                "Melt Tapped": time_energy.get("melt_tapped_at", ""),
                "Total Time": time_energy.get("total_time_consumed", ""),
                "Power Initial": time_energy.get("power_initial_reading", ""),
                "Power Final": time_energy.get("power_final_reading", ""),
                "Total Units": time_energy.get("power_total_units", ""),
                "Tapping Temp (C)": process.get("tapping_temp_c", ""),
                "Pouring Temp (C)": process.get("pouring_temp_c", ""),
                "Total Metal Tapped (kg)": yield_dispatch.get("total_metal_tapped_kgs", ""),
                "Total Charges (kg)": yield_dispatch.get("total_charges_kgs", ""),
                "QC Remarks": yield_dispatch.get("qc_remarks", "")
            })

            # 2. Build Chemical Composition Rows
            for chem in data.get("chemical_composition", []):
                chemical_data.append({
                    "Melt Number": melt_no,
                    "Element": chem.get("element", ""),
                    "Inti Min": chem.get("inti_min", ""),
                    "Inti Max": chem.get("inti_max", ""),
                    "UAPL Min": chem.get("uapl_min", ""),
                    "UAPL Max": chem.get("uapl_max", ""),
                    "Final Sample": chem.get("final_sample", "")
                })

            # 3. Build Materials/Charge Additions Rows
            for scrap in data.get("scrap_and_returns", []):
                material_data.append({"Melt Number": melt_no, "Category": "Scrap & Returns", "Material": scrap.get("material_name", ""), "Quantity (kg)": scrap.get("quantity_kgs", "")})
            
            for alloy in data.get("ferro_pure_alloys", []):
                material_data.append({"Melt Number": melt_no, "Category": "Ferro/Pure Alloys", "Material": alloy.get("material_name", ""), "Quantity (kg)": alloy.get("quantity_kgs", "")})
            
            for deox in data.get("deoxidants", []):
                material_data.append({"Melt Number": melt_no, "Category": "Deoxidants", "Material": deox.get("material_name", ""), "Quantity (kg)": deox.get("quantity_kgs", "")})

        # Convert to Pandas DataFrames (with fallback empty schemas to prevent crash on 0 records)
        df_summary = pd.DataFrame(summary_data) if summary_data else pd.DataFrame(columns=["Melt Number", "Date", "Grade"])
        df_chem = pd.DataFrame(chemical_data) if chemical_data else pd.DataFrame(columns=["Melt Number", "Element", "Final Sample"])
        df_mat = pd.DataFrame(material_data) if material_data else pd.DataFrame(columns=["Melt Number", "Category", "Material", "Quantity (kg)"])

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_summary.to_excel(writer, index=False, sheet_name='Summary')
            df_chem.to_excel(writer, index=False, sheet_name='Chemical Composition')
            df_mat.to_excel(writer, index=False, sheet_name='Charge Additions')
            
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=induction_furnace_logs.xlsx"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/documents/status/{task_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/status/{task_id}")
async def get_processing_status(task_id: str):
    """
    Keep this just so the frontend doesn't break if it checks status.
    """
    return {
        "task_id": task_id,
        "status": "SYNC_MODE_ACTIVE",
        "message": "Redis is disabled. Check the main /process route for output."
    }