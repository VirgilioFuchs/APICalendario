# APICalendario

A RESTful API for managing calendar events (feriados/holidays), built with **FastAPI** and **MySQL**.

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Configuration](#configuration)
- [Running the API](#running-the-api)
- [API Endpoints](#api-endpoints)
  - [Root](#root)
  - [Health Check](#health-check)
  - [List All Events](#list-all-events)
  - [List Events by Date Range (with ETag caching)](#list-events-by-date-range-with-etag-caching)
  - [Create Event](#create-event)
- [Data Model](#data-model)

---

## Overview

APICalendario exposes CRUD operations over a MySQL table (`calendario.feriado`) that stores holiday/event data. It supports:

- Listing all events
- Filtering events by date range with HTTP `ETag`-based caching (returns `304 Not Modified` when data has not changed)
- Creating new events
- Health checking the database connection

---

## Project Structure

```
APICalendario/
├── app/
│   ├── main.py              # FastAPI application entry point, CORS middleware
│   ├── api/
│   │   └── routes/
│   │       └── routes.py    # All API route handlers
│   ├── database/
│   │   ├── config.py        # Loads DB credentials from environment variables
│   │   └── connection.py    # Returns a mysql-connector connection
│   ├── models/
│   │   └── event.py         # Pydantic models: EventIn and EventOut
│   └── utils/
│       └── converters.py    # Helper: timedelta→time conversion, cached list query
├── requirements.txt
└── .gitignore
```

---

## Requirements

- Python 3.9+
- MySQL 8.x database with a `calendario.feriado` table

Install Python dependencies:

```bash
pip install -r requirements.txt
```

---

## Configuration

Create a `.env` file in the project root (it is git-ignored) with the following variables:

```env
DB_HOST=localhost
DB_USER=your_db_user
DB_PASS=your_db_password
DB_NAME=calendario
DB_PORT=3306
```

---

## Running the API

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

Interactive documentation (Swagger UI) is automatically available at `http://localhost:8000/docs`.

---

## API Endpoints

### Root

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/`  | Returns a simple status message |

**Response:**
```json
{ "status": "ok", "message": "API Event - First Step" }
```

---

### Health Check

| Method | Path      | Description                          |
|--------|-----------|--------------------------------------|
| `GET`  | `/health` | Verifies connectivity to the database |

**Response (healthy):**
```json
{ "status": "healthy", "database": "connected" }
```

**Response (unhealthy):**
```json
{ "status": "unhealthy", "database": "disconnected" }
```

---

### List All Events

| Method | Path            | Description              |
|--------|-----------------|--------------------------|
| `GET`  | `/events_list`  | Returns all events, ordered by date descending |

**Response:** Array of [`EventOut`](#data-model) objects.

---

### List Events by Date Range (with ETag caching)

| Method | Path                      | Description                                     |
|--------|---------------------------|-------------------------------------------------|
| `GET`  | `/api/events_list_cache`  | Returns events within a date range with ETag support |

**Query Parameters:**

| Parameter   | Type   | Required | Description              |
|-------------|--------|----------|--------------------------|
| `startDate` | string | Yes      | Start date (`YYYY-MM-DD`) |
| `endDate`   | string | Yes      | End date (`YYYY-MM-DD`)   |

**Caching behaviour:**  
The response includes an `ETag` header. Subsequent requests that send `If-None-Match` with the same ETag will receive `304 Not Modified` instead of the full payload.

**Example:**
```
GET /api/events_list_cache?startDate=2025-01-01&endDate=2025-12-31
```

---

### Create Event

| Method | Path             | Description          |
|--------|------------------|----------------------|
| `POST` | `/events_create` | Creates a new event  |

**Request Body:** [`EventIn`](#data-model) JSON object.

**Response:** [`EventOut`](#data-model) — the newly created event with its generated `feriado_id`. HTTP status `201 Created`.

---

## Data Model

### EventIn (request body for create)

| Field                  | Type            | Required | Description                         |
|------------------------|-----------------|----------|-------------------------------------|
| `feriado_titulo`       | string          | Yes      | Event title                         |
| `feriado_descricao`    | string          | Yes      | Event description                   |
| `feriado_tipo`         | string          | Yes      | Event type/category                 |
| `feriado_dia_inteiro`  | boolean         | No       | Whether the event lasts all day     |
| `feriado_inicio`       | time (HH:MM:SS) | No       | Start time (for non-all-day events) |
| `feriado_fim`          | time (HH:MM:SS) | No       | End time (for non-all-day events)   |
| `feriado_data`         | date (YYYY-MM-DD) | Yes    | Event date                          |
| `feriado_duracao_dias` | integer         | Yes      | Duration in days                    |

### EventOut

All fields from `EventIn`, plus:

| Field          | Type    | Description          |
|----------------|---------|----------------------|
| `feriado_id`   | integer | Auto-generated ID    |
