const PREDICTION_API_BASE = (
  import.meta.env.VITE_PREDICTION_API_URL || 'http://127.0.0.1:8000'
).replace(/\/$/, '');

export const PredictionEndpoint = (coinId) =>
  `${PREDICTION_API_BASE}/api/predictions/${coinId}`;
