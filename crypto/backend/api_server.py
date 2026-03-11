from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

_prediction_service = None


def _get_prediction_service():
    global _prediction_service
    if _prediction_service is None:
        try:
            from .prediction_service import prediction_service as service
        except ImportError:  # Script execution fallback
            from prediction_service import prediction_service as service
        _prediction_service = service
    return _prediction_service


def _parse_origins() -> list[str]:
    raw = os.getenv(
        "PREDICTION_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(
    title="Crypto Prediction API",
    description=(
        "Multi-model crypto prediction service with LSTM, XGBoost, and "
        "transformer-based sentiment features."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "crypto-prediction-api",
    }


@app.get("/api/predictions/{coin_id}")
def get_predictions(
    coin_id: str,
    force_refresh: bool = Query(False, description="Bypass cache and retrain models"),
    current_price_usd: float | None = Query(
        None,
        description="Optional USD price hint from frontend when backend market sources are blocked",
    ),
) -> Dict[str, Any]:
    try:
        service = _get_prediction_service()
        response = service.generate_predictions(
            coin_id=coin_id,
            force_refresh=force_refresh,
            current_price_hint=current_price_usd,
        )
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api_server:app",
        host=os.getenv("PREDICTION_HOST", "0.0.0.0"),
        port=int(os.getenv("PREDICTION_PORT", "8000")),
        reload=os.getenv("PREDICTION_RELOAD", "false").lower() == "true",
    )
