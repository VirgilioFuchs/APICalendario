import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, timedelta, time
import mysql.connector

app = FastAPI(title="API Events - first step")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT"))
}

def timedelta_convert(value):
    if value is None:
        return None
    if isinstance(value, time):
        return value
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        h = (total_seconds // 3600) % 24
        m = (total_seconds // 3600) % 60
        s = total_seconds % 60
        return time(hour=h, minute=m, second=s)
    return value

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


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


@app.get("/")
def root():
    return {"status": "ok", "message": "API Event - First Step"}


# Endpoint to list events
@app.get("/events_list", response_model=List[EventOut])
def list_events():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT feriado_id,
                   feriado_titulo,
                   feriado_descricao,
                   feriado_tipo,
                   feriado_dia_inteiro,
                   feriado_inicio,
                   feriado_fim,
                   feriado_data,
                   feriado_duracao_dias
            FROM calendario.feriado
            ORDER BY feriado_data DESC, feriado_id DESC
            LIMIT 100
            """
        )
        rows = cursor.fetchall()

        for row in rows:
            row["feriado_inicio"] = timedelta_convert(row.get("feriado_inicio"))
            row["feriado_fim"] = timedelta_convert(row.get("feriado_fim"))

        return rows
    except Exception:
        raise HTTPException(status_code=500, detail="Error when fetch events")
    finally:
        cursor.close()
        conn.close()


@app.post("/events_create", response_model=EventOut, status_code=201)
def create_event(event: EventIn):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO calendario.feriado
            ("feriado_titulo", "feriado_descricao", "feriado_tipo", "feriado_dia_inteiro", "feriado_inicio",
             "feriado_fim", "feriado_data", "feriado_duracao_dias")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                event.feriado_titulo,
                event.feriado_descricao,
                event.feriado_tipo,
                event.feriado_dia_inteiro,
                event.feriado_inicio,
                event.feriado_fim,
                event.feriado_data,
                event.feriado_duracao_dias
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid

        cursor.execute(
            """
            SELECT feriado_id,
                   feriado_titulo,
                   feriado_descricao,
                   feriado_tipo,
                   feriado_dia_inteiro,
                   feriado_inicio,
                   feriado_fim,
                   feriado_data,
                   feriado_duracao_dias
            FROM calendario.feriado
            Where feriado_id = %s
            """,
            (new_id,),
        )
        row = cursor.fetchone()
        return row
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Error when create event")
    finally:
        cursor.close()
        conn.close()