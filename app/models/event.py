from pydantic import BaseModel
from typing import Optional
from datetime import date, time


class EventIn(BaseModel):
    feriado_titulo: str
    feriado_descricao: str
    feriado_tipo: str
    feriado_dia_inteiro: bool = None
    feriado_inicio: Optional[time] = None
    feriado_fim: Optional[time] = None
    feriado_data: date
    feriado_duracao_dias: int


class EventOut(EventIn):
    feriado_id: int
