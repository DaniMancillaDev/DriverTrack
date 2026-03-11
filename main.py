"""Punto de entrada principal de DriveTrack API.

Ejecutar con: uv run uvicorn app.main:app --reload
O directamente: uv run python main.py
"""

import uvicorn


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)