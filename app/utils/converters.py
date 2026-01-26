from datetime import timedelta, time
from typing import List, Any, Dict
from fastapi import HTTPException
from app.database import get_connection


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


def list_events_cache(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
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
                WHERE feriado.feriado_data BETWEEN %s AND %s
                ORDER BY feriado_data DESC, feriado_id DESC
                """

        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()

        for row in rows:
            if row.get('feriado_data'):
                row['feriado_data'] = row['feriado_data'].isoformat()
            if row.get('feriado_inicio'):
                row['feriado_inicio'] = str(row['feriado_inicio'])
            if row.get('feriado_fim'):
                row['feriado_fim'] = str(row['feriado_fim'])

        return rows

    except Exception as e:
        print(f"Erro ao buscar eventos: {e}")
        raise HTTPException(status_code=500, detail=f"Error when fetch events: {str(e)}")
    finally:
        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()
