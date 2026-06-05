from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class HeaderMetadata(BaseModel):
    date: Optional[str] = None
    grade: Optional[str] = None
    melt_number: Optional[str] = None
    crucible_no: Optional[str] = None
    melts_in_month: Optional[str] = None
    day: Optional[str] = None

class FurnaceReading(BaseModel):
    time_hrs: Optional[str] = None
    freq: Optional[str] = None
    kw: Optional[str] = None
    voltage: Optional[str] = None
    inlet: Optional[str] = None
    outlet: Optional[str] = None
    gld: Optional[str] = None

class TimeAndEnergy(BaseModel):
    furnace_readings: List[FurnaceReading] = Field(default_factory=list)
    furnace_started_at: Optional[str] = None
    sample_times: List[str] = Field(default_factory=list)
    melt_tapped_at: Optional[str] = None
    total_time_consumed: Optional[str] = None
    power_initial_reading: Optional[float] = None
    power_final_reading: Optional[float] = None
    power_total_units: Optional[float] = None

class ElementComposition(BaseModel):
    element: str 
    inti_min: Optional[float] = None
    inti_max: Optional[float] = None
    uapl_min: Optional[float] = None
    uapl_max: Optional[float] = None
    bath_readings: List[Optional[float]] = Field(default_factory=list)
    final_sample: Optional[float] = None

class ChargeAdditionItem(BaseModel):
    material_name: str
    quantity_kgs: Optional[float] = None
    quantity_ladle_kgs: Optional[float] = None

class ProcessParameters(BaseModel):
    tapping_temp_c: Optional[str] = None
    pouring_temp_c: Optional[str] = None
    shank_ladle_temp_c: Optional[str] = None
    furnace_lining_condition: Optional[str] = None
    slag_condition: Optional[str] = None
    shank_ladle_condition: Optional[str] = None
    dissolved_gas_level: Optional[str] = None
    hind_tags_checked: Optional[str] = None
    tags_punched: Optional[str] = None

class YieldAndDispatch(BaseModel):
    total_charges_kgs: Optional[float] = None
    total_addition_kgs: Optional[float] = None
    total_metal_tapped_kgs: Optional[float] = None
    no_of_moulds_poured: Optional[int] = None
    no_of_test_bars: Optional[int] = None
    spilage_metal_kgs: Optional[float] = None
    extra_metal_kgs: Optional[float] = None
    tags_discard: Optional[str] = None
    melting_incharge: Optional[str] = None
    qc_incharge: Optional[str] = None
    fic_charge_hand: Optional[str] = None
    qc_remarks: Optional[str] = None

class PouringRow(BaseModel):
    item_description: Optional[str] = None
    quantity: Optional[int] = None
    planned_weight_kg: Optional[float] = None
    poured_weight_kg: Optional[float] = None

class StructuredDocument(BaseModel):
    header: HeaderMetadata
    time_and_energy: TimeAndEnergy
    chemical_composition: List[ElementComposition] = Field(default_factory=list)
    scrap_and_returns: List[ChargeAdditionItem] = Field(default_factory=list)
    ferro_pure_alloys: List[ChargeAdditionItem] = Field(default_factory=list)
    deoxidants: List[ChargeAdditionItem] = Field(default_factory=list)
    process_parameters: ProcessParameters
    yield_and_dispatch: YieldAndDispatch
    pouring_table: List[PouringRow] = Field(default_factory=list)
    raw_notes: Optional[List[Dict[str, Any]]] = None