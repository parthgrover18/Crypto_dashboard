# Crypto Prediction Backend

FastAPI service that generates per-coin forecasts for:
- 1 hour
- 1 day
- 1 week

It combines:
- LSTM (TensorFlow)
- XGBoost regressor
- Transformer-based sentiment features from Wikipedia edits (MWClient + HuggingFace pipeline)

## Run

```bash
cd /Users/dell/non\ icloud\ files/websites/crypto\ website/crypto/backend
python3 -m pip install -r requirements.txt
python3 api_server.py
```

Default API URL: `http://127.0.0.1:8000`

## Endpoint

- `GET /health`
- `GET /api/predictions/{coin_id}`
- `GET /api/predictions/{coin_id}?force_refresh=true`
- `GET /api/predictions/{coin_id}?current_price_usd=50443.12`

Example:

```bash
curl http://127.0.0.1:8000/api/predictions/bitcoin
```

## Batch Warmup

```bash
python3 train_top_coins.py --limit 20
```

This precomputes and caches predictions for top coins in memory, local cache file, and MongoDB (if reachable).

## Optional Environment Variables

- `PREDICTION_ALLOWED_ORIGINS` (comma-separated origins)
- `PREDICTION_PORT` (default `8000`)
- `PREDICTION_CACHE_TTL_MINUTES` (default `30`)
- `USE_MONGO_CACHE` (`true`/`false`)
- `MONGO_URI` (default `mongodb://127.0.0.1:27017/`)
- `MONGO_DB` (default `crypto_database`)
- `MONGO_PREDICTIONS_COLLECTION` (default `coin_predictions`)
- `LSTM_EPOCHS` (default `8`)
