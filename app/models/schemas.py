from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import List, Dict, Any, Optional

class WaterBalanceRequest(BaseModel):
    latitude: float = Field(..., description="Latitude da propriedade (-90 a 90)")
    longitude: float = Field(..., description="Longitude da propriedade (-180 a 180)")
    cultura: str = Field(..., description="Cultura plantada (soja ou milho)")
    data_plantio: date = Field(..., description="Data do plantio no formato YYYY-MM-DD")

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError('Campo latitude incorreto: deve estar entre -90 e 90')
        return v

    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError('Campo longitude incorreto: deve estar entre -180 e 180')
        return v

    @field_validator('cultura')
    @classmethod
    def validate_cultura(cls, v: str) -> str:
        if v.lower() not in ["soja", "milho"]:
            raise ValueError(f'Campo cultura incorreto: "{v}" não é suportado. Use "soja" ou "milho".')
        return v.lower()

class DashboardEntry(BaseModel):
    date: date
    arm_mm: float
    chuva_mm: float
    eto_mm: float

class WaterBalanceResponse(BaseModel):
    coord: str
    tipo_solo: str
    cad_maxima_mm: float
    armazenamento_atual_mm: float
    status: str
    alerta_irrigacao: bool
    previsao_irrigacao_dias: int
    mensagem_status: str
    insight_especialista: Optional[str] = None
    clay_bruto: Optional[float] = None
    sand_bruto: Optional[float] = None
    dashboard_data: List[DashboardEntry]
