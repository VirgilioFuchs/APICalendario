import hashlib
import json
from fastapi import APIRouter, HTTPException, Request, status
from typing import List

from fastapi.responses import JSONResponse, Response

from app.models.event import EventIn, EventOut
from app.database import get_connection
from app.utils import timedelta_convert, list_events_cache

router = APIRouter()

@router.get("/events_list", response_model=List[EventOut])
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


@router.get("/api/events_list_cache")
async def get_events(
        startDate: str,
        endDate: str,
        request: Request
):
    try:
        events = list_events_cache(startDate, endDate)

        content = json.dumps(events, sort_keys=True, default=str)
        etag = f'"{hashlib.md5(content.encode()).hexdigest()}"'

        client_etag = request.headers.get("if-none-match")

        if client_etag == etag:
            return Response(
                status_code=status.HTTP_304_NOT_MODIFIED,
                headers={"ETag": etag}
            )

        return JSONResponse(
            content=events,
            status_code=status.HTTP_200_OK,
            headers={
                "ETag": etag,
                "Cache-Control": "no-cache, must-revalidate"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro no endpoint cache: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error when fetch events with cache: {str(e)}"
        )


@router.post("/events_create", response_model=EventOut, status_code=201)
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

@router.get("/health")
async def health_check():
    try:
        conn = get_connection()
        if conn.is_connected():
            conn.close()
            return { "status": "healthy", "database": "connected" }
    except:
        return { "status": "unhealthy", "database": "disconnected" }