from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.concurrency import run_in_threadpool
from core.config import settings
from ml_pipeline.engine import IntelligentDocumentProcessor
from api.dependencies import get_db
from database.repository import DocumentRepository
import aiofiles
import os
import uuid
import io
import pandas as pd

router = APIRouter()

# Load the ML engine directly into the API memory (Bypassing Celery/Redis)
print("Loading ML Models directly into FastAPI...")
ocr_engine = IntelligentDocumentProcessor()

@router.post("/documents/process")
async def upload_and_process_document(file: UploadFile = File(...), db = Depends(get_db)):
    """
    Accepts an industrial scan and processes it IMMEDIATELY, 
    returning the extracted JSON data and storing it in the database.
    """
    allowed_types = ["image/jpeg", "image/png", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use JPG, PNG, or PDF.")

    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    # Save file
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    try:
        extracted_results = await run_in_threadpool(ocr_engine.process_document, file_path)
        
        print(f"DEBUG - Extracted results payload: {extracted_results}")
        
        if isinstance(extracted_results, dict) and "error" in extracted_results:
            raise HTTPException(
                status_code=422, 
                detail=f"AI Extraction Pipeline Error: {extracted_results['error']}"
            )
            
        # Save to database (MongoDB with automatic local JSON fallback)
        task_id = uuid.uuid4().hex
        repo = DocumentRepository(db)
        await repo.save_document(task_id, extracted_results)
        
        return {
            "message": "Document processed successfully",
            "filename": unique_filename,
            "task_id": task_id,
            "data": extracted_results 
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed inside route: {str(e)}")

@router.get("/documents")
async def get_all_processed_documents(db = Depends(get_db)):
    """
    Retrieves all processed document records from the database or local file fallback.
    """
    try:
        repo = DocumentRepository(db)
        records = await repo.get_all_documents()
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve records: {str(e)}")

@router.get("/documents/export")
async def export_all_data_to_excel(db = Depends(get_db)):
    """
    Aggregates all processed document records and dynamically builds a multi-sheet Excel file 
    mapped to the Induction Furnace schema.
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
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")

@router.get("/documents/status/{task_id}")
async def get_processing_status(task_id: str):
    return {"task_id": task_id, "status": "SYNC_MODE_ACTIVE", "message": "Redis is disabled. Check the main /process route for output."}