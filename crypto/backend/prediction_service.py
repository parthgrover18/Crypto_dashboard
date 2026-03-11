from __future__ import annotations

import hashlib
import json
import math
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests
import yfinance as yf
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_percentage_error
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import MinMaxScaler

try:
    from xgboost import XGBRegressor
except Exception:  # pragma: no cover - optional dependency
    XGBRegressor = None

try:
    from tensorflow.keras.layers import Dense, Dropout, Input, LSTM
    from tensorflow.keras.models import Sequential

    TENSORFLOW_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    TENSORFLOW_AVAILABLE = False

try:
    import mwclient
except Exception:  # pragma: no cover - optional dependency
    mwclient = None

try:
    from transformers import pipeline
except Exception:  # pragma: no cover - optional dependency
    pipeline = None

try:
    from pymongo import MongoClient
except Exception:  # pragma: no cover - optional dependency
    MongoClient = None


COINGECKO_BASE_URL = os.getenv("COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3")
BINANCE_BASE_URL = os.getenv("BINANCE_BASE_URL", "https://api.binance.com")
CACHE_TTL_MINUTES = int(os.getenv("PREDICTION_CACHE_TTL_MINUTES", "30"))
CACHE_FILE = Path(__file__).with_name("prediction_cache.json")
USE_MONGO_CACHE = os.getenv("USE_MONGO_CACHE", "true").lower() == "true"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")
MONGO_DB = os.getenv("MONGO_DB", "crypto_database")
MONGO_COLLECTION = os.getenv("MONGO_PREDICTIONS_COLLECTION", "coin_predictions")
LSTM_EPOCHS = int(os.getenv("LSTM_EPOCHS", "8"))
WIKI_REVISION_LIMIT = int(os.getenv("WIKI_REVISION_LIMIT", "120"))
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
REQUEST_RETRIES = int(os.getenv("REQUEST_RETRIES", "3"))


@dataclass(frozen=True)
class HorizonConfig:
    label: str
    period: str
    interval: str
    steps: int
    sequence_length: int
    min_rows: int


HORIZONS: Dict[str, HorizonConfig] = {
    "1h": HorizonConfig(
        label="1 Hour",
        period="90d",
        interval="1h",
        steps=1,
        sequence_length=48,
        min_rows=180,
    ),
    "1d": HorizonConfig(
        label="1 Day",
        period="5y",
        interval="1d",
        steps=1,
        sequence_length=45,
        min_rows=160,
    ),
    "1w": HorizonConfig(
        label="1 Week",
        period="max",
        interval="1d",
        steps=7,
        sequence_length=60,
        min_rows=220,
    ),
}


COIN_TICKER_OVERRIDES = {
    "bitcoin": "BTC-USD",
    "ethereum": "ETH-USD",
    "tether": "USDT-USD",
    "binancecoin": "BNB-USD",
    "solana": "SOL-USD",
    "ripple": "XRP-USD",
    "usd-coin": "USDC-USD",
    "dogecoin": "DOGE-USD",
    "cardano": "ADA-USD",
    "tron": "TRX-USD",
    "avalanche-2": "AVAX-USD",
    "shiba-inu": "SHIB-USD",
    "chainlink": "LINK-USD",
    "polkadot": "DOT-USD",
    "litecoin": "LTC-USD",
    "uniswap": "UNI7083-USD",
    "near": "NEAR-USD",
    "bitcoin-cash": "BCH-USD",
    "internet-computer": "ICP-USD",
    "aptos": "APT-USD",
    "render-token": "RNDR-USD",
    "arbitrum": "ARB11841-USD",
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if isinstance(value, float) and math.isnan(value):
            return default
        return float(value)
    except Exception:
        return default


def _base_symbol_from_ticker(ticker: str, fallback_symbol: str) -> str:
    if ticker and "-" in ticker:
        base = ticker.split("-")[0].strip().upper()
        if base:
            return base
    return fallback_symbol


def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def _normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

    rename_map = {
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "close",
        "Volume": "volume",
    }
    df = df.rename(columns=rename_map)

    for column in ["open", "high", "low", "close", "volume"]:
        if column not in df.columns:
            if column == "volume":
                df[column] = 0.0
            else:
                df[column] = df.get("close", pd.Series([0] * len(df), index=df.index))

    required = ["open", "high", "low", "close", "volume"]
    clean = df[required].copy()
    clean = clean.dropna()
    if isinstance(clean.index, pd.DatetimeIndex):
        clean.index = clean.index.tz_localize(None)
    clean = clean.sort_index()
    return clean


def _coingecko_request(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "CoinlyticsPrediction/1.0",
    }

    last_error: Optional[Exception] = None
    for attempt in range(REQUEST_RETRIES):
        try:
            response = requests.get(
                f"{COINGECKO_BASE_URL}{path}",
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            if attempt < REQUEST_RETRIES - 1:
                time.sleep(0.8 * (attempt + 1))

    if last_error is not None:
        raise last_error
    raise RuntimeError("Unknown CoinGecko request failure")


def resolve_coin_metadata(coin_id: str) -> Dict[str, Any]:
    fallback_name = coin_id.replace("-", " ").title()
    override_ticker = COIN_TICKER_OVERRIDES.get(coin_id)
    fallback_symbol = _base_symbol_from_ticker(
        override_ticker or "",
        coin_id.split("-")[0][:6].upper(),
    )

    metadata = {
        "coin_id": coin_id,
        "name": fallback_name,
        "symbol": fallback_symbol,
        "ticker": COIN_TICKER_OVERRIDES.get(coin_id, f"{fallback_symbol}-USD"),
        "current_price_usd": None,
    }

    try:
        payload = _coingecko_request(
            f"/coins/{coin_id}",
            params={
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false",
                "sparkline": "false",
            },
        )

        symbol = str(payload.get("symbol") or fallback_symbol).upper()
        metadata["name"] = payload.get("name") or fallback_name
        metadata["symbol"] = symbol
        metadata["ticker"] = COIN_TICKER_OVERRIDES.get(coin_id, f"{symbol}-USD")
        metadata["current_price_usd"] = payload.get("market_data", {}).get(
            "current_price", {}
        ).get("usd")
    except Exception:
        pass

    return metadata


def download_yfinance_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    for _ in range(3):
        try:
            data = yf.download(
                ticker,
                period=period,
                interval=interval,
                auto_adjust=True,
                progress=False,
                threads=False,
            )
            normalized = _normalize_ohlcv(data)
            if not normalized.empty:
                return normalized
        except Exception:
            time.sleep(1)
    return pd.DataFrame()


def download_coingecko_history(
    coin_id: str,
    horizon: HorizonConfig,
    days_override: Optional[int] = None,
) -> pd.DataFrame:
    if days_override is not None:
        days = int(days_override)
    else:
        days = 90 if horizon.interval == "1h" else 1800

    payload = _coingecko_request(
        f"/coins/{coin_id}/market_chart",
        params={
            "vs_currency": "usd",
            "days": str(days),
        },
    )

    prices = payload.get("prices", [])
    volumes = payload.get("total_volumes", [])
    if not prices:
        return pd.DataFrame()

    price_df = pd.DataFrame(prices, columns=["timestamp", "close"])
    volume_df = pd.DataFrame(volumes, columns=["timestamp", "volume"])
    df = price_df.merge(volume_df, on="timestamp", how="left")
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.tz_localize(None)
    df = df.sort_values("date").set_index("date")

    if horizon.interval == "1d":
        df = df.resample("1D").last().dropna()

    df["open"] = df["close"].shift(1).fillna(df["close"])
    df["high"] = np.maximum(df["open"], df["close"]) * 1.003
    df["low"] = np.minimum(df["open"], df["close"]) * 0.997
    df["volume"] = df["volume"].fillna(method="ffill").fillna(0.0)

    return _normalize_ohlcv(df)


def download_binance_history(base_symbol: str, horizon: HorizonConfig) -> pd.DataFrame:
    interval = "1h" if horizon.interval == "1h" else "1d"
    quote_candidates = ["USDT", "FDUSD", "USDC", "BUSD", "USD"]
    headers = {"Accept": "application/json", "User-Agent": "CoinlyticsPrediction/1.0"}

    for quote in quote_candidates:
        pair = f"{base_symbol.upper()}{quote}"
        try:
            response = requests.get(
                f"{BINANCE_BASE_URL}/api/v3/klines",
                params={"symbol": pair, "interval": interval, "limit": 1000},
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            if response.status_code != 200:
                continue

            rows = response.json()
            if not isinstance(rows, list) or not rows:
                continue

            df = pd.DataFrame(
                rows,
                columns=[
                    "open_time",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "close_time",
                    "quote_volume",
                    "trade_count",
                    "taker_buy_base",
                    "taker_buy_quote",
                    "ignore",
                ],
            )
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            df["date"] = pd.to_datetime(df["open_time"], unit="ms").dt.tz_localize(None)
            df = df.set_index("date")[["open", "high", "low", "close", "volume"]].dropna()
            normalized = _normalize_ohlcv(df)
            if not normalized.empty:
                return normalized
        except Exception:
            continue

    return pd.DataFrame()


def load_local_bitcoin_history(horizon: HorizonConfig) -> pd.DataFrame:
    local_file = Path(__file__).resolve().parents[1] / "btc.txt"
    if not local_file.exists():
        return pd.DataFrame()

    try:
        raw = pd.read_csv(local_file)
    except Exception:
        return pd.DataFrame()

    close_col = "Adj Close" if "Adj Close" in raw.columns else "Close"
    if close_col not in raw.columns:
        return pd.DataFrame()

    for candidate in ["Open", "High", "Low", close_col]:
        if candidate not in raw.columns:
            return pd.DataFrame()

    if "Volume" not in raw.columns:
        # Old exported BTC file does not include volume; synthetic volume preserves shape only.
        raw["Volume"] = (raw[close_col].astype(float).fillna(0) * 10).clip(lower=0)

    freq = "h" if horizon.interval == "1h" else "D"
    dates = pd.date_range(end=datetime.now(timezone.utc), periods=len(raw), freq=freq)

    df = pd.DataFrame(
        {
            "open": pd.to_numeric(raw["Open"], errors="coerce").to_numpy(),
            "high": pd.to_numeric(raw["High"], errors="coerce").to_numpy(),
            "low": pd.to_numeric(raw["Low"], errors="coerce").to_numpy(),
            "close": pd.to_numeric(raw[close_col], errors="coerce").to_numpy(),
            "volume": pd.to_numeric(raw["Volume"], errors="coerce").to_numpy(),
        },
        index=dates.tz_localize(None),
    ).dropna()

    return _normalize_ohlcv(df)


def load_proxy_history_from_bitcoin(
    coin_id: str,
    horizon: HorizonConfig,
    current_price_usd: Optional[float],
) -> pd.DataFrame:
    if not current_price_usd or current_price_usd <= 0:
        return pd.DataFrame()

    base = load_local_bitcoin_history(horizon)
    if base.empty:
        return pd.DataFrame()

    seed_hex = hashlib.sha256(coin_id.encode("utf-8")).hexdigest()[:8]
    seed_int = int(seed_hex, 16)
    volatility_factor = 0.8 + ((seed_int % 60) / 100.0)

    last_close = float(base["close"].iloc[-1])
    if last_close <= 0:
        return pd.DataFrame()

    relative = (base["close"] / last_close).clip(lower=1e-9)
    proxy_close = current_price_usd * np.power(relative, volatility_factor)
    close_ratio = proxy_close / base["close"].replace(0, np.nan)
    close_ratio = close_ratio.ffill().bfill().fillna(1.0)

    proxy = base.copy()
    proxy["open"] = proxy["open"] * close_ratio
    proxy["high"] = proxy["high"] * close_ratio
    proxy["low"] = proxy["low"] * close_ratio
    proxy["close"] = proxy_close
    proxy["volume"] = proxy["volume"] * max(current_price_usd / last_close, 0.1)
    return _normalize_ohlcv(proxy)


def fetch_history_for_horizon(
    coin_id: str,
    ticker: str,
    horizon: HorizonConfig,
    current_price_hint: Optional[float] = None,
) -> Tuple[pd.DataFrame, str, List[str]]:
    history = pd.DataFrame()
    errors: List[str] = []
    base_symbol = _base_symbol_from_ticker(ticker, coin_id.split("-")[0][:6].upper())

    try:
        history = download_yfinance_history(
            ticker,
            period=horizon.period,
            interval=horizon.interval,
        )
        if not history.empty:
            return history, "yfinance", errors
        errors.append("yfinance: empty dataset")
    except Exception:
        errors.append("yfinance: request failed")

    if history.empty:
        try:
            history = download_coingecko_history(coin_id, horizon)
            if not history.empty:
                return history, "coingecko", errors
            errors.append("coingecko: empty dataset")
        except Exception:
            errors.append("coingecko: request failed")

    if history.empty:
        try:
            if horizon.interval == "1h":
                history = download_coingecko_history(coin_id, horizon, days_override=30)
            elif horizon.label == "1 Week":
                history = download_coingecko_history(coin_id, horizon, days_override=1200)
            else:
                history = download_coingecko_history(coin_id, horizon, days_override=1095)
            if not history.empty:
                return history, "coingecko-short-window", errors
            errors.append("coingecko-short-window: empty dataset")
        except Exception:
            errors.append("coingecko-short-window: request failed")

    if history.empty:
        try:
            history = download_binance_history(base_symbol, horizon)
            if not history.empty:
                return history, "binance", errors
            errors.append("binance: empty dataset")
        except Exception:
            errors.append("binance: request failed")

    if history.empty and coin_id == "bitcoin":
        history = load_local_bitcoin_history(horizon)
        if not history.empty:
            return history, "local-btc-file", errors
        errors.append("local-btc-file: unavailable")

    if history.empty:
        history = load_proxy_history_from_bitcoin(
            coin_id=coin_id,
            horizon=horizon,
            current_price_usd=current_price_hint,
        )
        if not history.empty:
            return history, "local-btc-proxy", errors
        errors.append("local-btc-proxy: unavailable")

    return history, "none", errors


class SentimentAnalyzer:
    def __init__(self) -> None:
        self._site = None
        self._pipeline = None
        self._cache: Dict[str, Dict[str, float]] = {}

    def _get_pipeline(self):
        if pipeline is None:
            return None
        if self._pipeline is None:
            try:
                self._pipeline = pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                )
            except Exception:
                self._pipeline = None
        return self._pipeline

    def _get_site(self):
        if mwclient is None:
            return None
        if self._site is None:
            try:
                self._site = mwclient.Site("en.wikipedia.org")
            except Exception:
                self._site = None
        return self._site

    def score_coin(self, coin_name: str) -> Dict[str, float]:
        if coin_name in self._cache:
            return self._cache[coin_name]

        neutral = {"sentiment": 0.0, "neg_sentiment": 0.0, "sample_size": 0}
        model = self._get_pipeline()
        site = self._get_site()

        if model is None or site is None:
            self._cache[coin_name] = neutral
            return neutral

        comments: List[str] = []
        page_titles = [coin_name, coin_name.title(), coin_name.replace("-", " ").title()]

        page = None
        for title in page_titles:
            candidate = site.pages[title]
            if candidate.exists:
                page = candidate
                break

        if page is None:
            self._cache[coin_name] = neutral
            return neutral

        try:
            for rev in page.revisions(limit=WIKI_REVISION_LIMIT):
                comment = str(rev.get("comment") or "").strip()
                if comment:
                    comments.append(comment)
        except Exception:
            self._cache[coin_name] = neutral
            return neutral

        if not comments:
            self._cache[coin_name] = neutral
            return neutral

        scores: List[float] = []
        neg_count = 0

        try:
            batch_size = 16
            for i in range(0, len(comments), batch_size):
                batch = comments[i : i + batch_size]
                results = model(batch)
                for result in results:
                    score = _safe_float(result.get("score"))
                    label = result.get("label")
                    if label == "NEGATIVE":
                        score *= -1
                        neg_count += 1
                    scores.append(score)
        except Exception:
            self._cache[coin_name] = neutral
            return neutral

        response = {
            "sentiment": float(np.mean(scores)) if scores else 0.0,
            "neg_sentiment": float(neg_count / len(scores)) if scores else 0.0,
            "sample_size": len(scores),
        }
        self._cache[coin_name] = response
        return response


def build_features(
    history: pd.DataFrame,
    sentiment_score: float,
    negative_sentiment: float,
    horizon_steps: int,
) -> Tuple[pd.DataFrame, List[str]]:
    df = history.copy()

    df["return_1"] = df["close"].pct_change()
    df["return_3"] = df["close"].pct_change(3)
    df["return_7"] = df["close"].pct_change(7)

    df["ma_5"] = df["close"].rolling(5).mean()
    df["ma_20"] = df["close"].rolling(20).mean()
    df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()

    df["volatility_10"] = df["return_1"].rolling(10).std()
    df["rsi_14"] = _compute_rsi(df["close"], 14)

    df["volume_change"] = df["volume"].pct_change()
    df["hl_spread"] = (df["high"] - df["low"]) / df["close"].replace(0, np.nan)
    df["oc_spread"] = (df["close"] - df["open"]) / df["open"].replace(0, np.nan)

    df["sentiment"] = sentiment_score
    df["neg_sentiment"] = negative_sentiment

    df["target"] = df["close"].shift(-horizon_steps)
    df = df.replace([np.inf, -np.inf], np.nan).dropna()

    feature_columns = [
        "close",
        "volume",
        "return_1",
        "return_3",
        "return_7",
        "ma_5",
        "ma_20",
        "ema_12",
        "ema_26",
        "volatility_10",
        "rsi_14",
        "volume_change",
        "hl_spread",
        "oc_spread",
        "sentiment",
        "neg_sentiment",
    ]

    return df, feature_columns


def _split_train_test(df: pd.DataFrame, split_ratio: float = 0.8) -> Tuple[pd.DataFrame, pd.DataFrame]:
    split_index = int(len(df) * split_ratio)
    split_index = min(max(split_index, 1), len(df) - 1)
    return df.iloc[:split_index].copy(), df.iloc[split_index:].copy()


def _compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    base_price: np.ndarray,
) -> Dict[str, float]:
    if len(y_true) == 0:
        return {"accuracy": 0.0, "directional_accuracy": 0.0, "mape": 100.0}

    safe_true = np.where(np.abs(y_true) < 1e-9, 1e-9, y_true)
    mape = mean_absolute_percentage_error(safe_true, y_pred)
    accuracy = max(0.0, 100.0 - (mape * 100.0))

    true_direction = np.sign(y_true - base_price)
    pred_direction = np.sign(y_pred - base_price)
    directional_accuracy = float(np.mean(true_direction == pred_direction) * 100.0)

    return {
        "accuracy": round(float(accuracy), 2),
        "directional_accuracy": round(directional_accuracy, 2),
        "mape": round(float(mape * 100.0), 2),
    }


def run_xgboost_model(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    features: List[str],
) -> Dict[str, Any]:
    x_train = train_df[features].values
    y_train = train_df["target"].values
    x_test = test_df[features].values
    y_test = test_df["target"].values

    if XGBRegressor is not None:
        model = XGBRegressor(
            n_estimators=260,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            objective="reg:squarederror",
            n_jobs=2,
        )
    else:
        model = GradientBoostingRegressor(random_state=42)

    model.fit(x_train, y_train)
    test_predictions = model.predict(x_test)
    next_prediction = float(model.predict(test_df[features].iloc[[-1]])[0])

    metrics = _compute_metrics(
        y_true=y_test,
        y_pred=test_predictions,
        base_price=test_df["close"].values,
    )

    return {
        "model": "XGBoost" if XGBRegressor is not None else "GradientBoosting",
        "prediction": round(next_prediction, 6),
        **metrics,
    }


def run_sentiment_model(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> Dict[str, Any]:
    feature_cols = [
        "close",
        "return_1",
        "return_3",
        "volatility_10",
        "sentiment",
        "neg_sentiment",
    ]

    model = LinearRegression()
    model.fit(train_df[feature_cols], train_df["target"])

    test_predictions = model.predict(test_df[feature_cols])
    next_prediction = float(model.predict(test_df[feature_cols].iloc[[-1]])[0])

    metrics = _compute_metrics(
        y_true=test_df["target"].values,
        y_pred=test_predictions,
        base_price=test_df["close"].values,
    )

    return {
        "model": "Transformer Sentiment",
        "prediction": round(next_prediction, 6),
        **metrics,
    }


def _build_lstm_sequences(
    df: pd.DataFrame,
    features: List[str],
    sequence_length: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, MinMaxScaler, MinMaxScaler]:
    feature_scaler = MinMaxScaler()
    target_scaler = MinMaxScaler()

    x_scaled = feature_scaler.fit_transform(df[features].values)
    y_scaled = target_scaler.fit_transform(df[["target"]].values).flatten()

    sequences = []
    targets = []
    close_reference = []

    for idx in range(sequence_length, len(df)):
        sequences.append(x_scaled[idx - sequence_length : idx])
        targets.append(y_scaled[idx])
        close_reference.append(df["close"].iloc[idx])

    return (
        np.array(sequences),
        np.array(targets),
        np.array(close_reference),
        feature_scaler,
        target_scaler,
    )


def run_lstm_model(
    feature_df: pd.DataFrame,
    features: List[str],
    sequence_length: int,
) -> Dict[str, Any]:
    sequences, targets, close_ref, feature_scaler, target_scaler = _build_lstm_sequences(
        feature_df,
        features,
        sequence_length,
    )

    if len(sequences) < 150:
        return {
            "model": "LSTM",
            "prediction": round(float(feature_df["close"].iloc[-1]), 6),
            "accuracy": 0.0,
            "directional_accuracy": 0.0,
            "mape": 100.0,
        }

    split = int(len(sequences) * 0.8)
    split = min(max(split, 50), len(sequences) - 1)

    x_train, x_test = sequences[:split], sequences[split:]
    y_train, y_test = targets[:split], targets[split:]
    close_test = close_ref[split:]

    model_name = "LSTM"

    if TENSORFLOW_AVAILABLE:
        model = Sequential(
            [
                Input(shape=(x_train.shape[1], x_train.shape[2])),
                LSTM(64, return_sequences=False),
                Dropout(0.15),
                Dense(32, activation="relu"),
                Dense(1),
            ]
        )
        model.compile(optimizer="adam", loss="mse")
        model.fit(
            x_train,
            y_train,
            epochs=LSTM_EPOCHS,
            batch_size=32,
            verbose=0,
            validation_split=0.1,
        )

        pred_test_scaled = model.predict(x_test, verbose=0).flatten()
        next_sequence = feature_scaler.transform(feature_df[features].values)[-sequence_length:]
        next_scaled = float(model.predict(np.array([next_sequence]), verbose=0).flatten()[0])
    else:
        model_name = "LSTM (MLP fallback)"
        mlp = MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=300, random_state=42)
        x_train_flat = x_train.reshape((x_train.shape[0], -1))
        x_test_flat = x_test.reshape((x_test.shape[0], -1))
        mlp.fit(x_train_flat, y_train)
        pred_test_scaled = mlp.predict(x_test_flat)
        next_sequence = feature_scaler.transform(feature_df[features].values)[-sequence_length:]
        next_scaled = float(mlp.predict(next_sequence.reshape(1, -1))[0])

    pred_test = target_scaler.inverse_transform(pred_test_scaled.reshape(-1, 1)).flatten()
    y_test_unscaled = target_scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
    next_prediction = float(target_scaler.inverse_transform([[next_scaled]])[0][0])

    metrics = _compute_metrics(
        y_true=y_test_unscaled,
        y_pred=pred_test,
        base_price=close_test,
    )

    return {
        "model": model_name,
        "prediction": round(next_prediction, 6),
        **metrics,
    }


def ensemble_models(models: List[Dict[str, Any]]) -> Dict[str, float]:
    available = [m for m in models if _safe_float(m.get("prediction")) > 0]
    if not available:
        return {
            "prediction": 0.0,
            "accuracy": 0.0,
            "directional_accuracy": 0.0,
        }

    weights = []
    for model in available:
        score = max(_safe_float(model.get("accuracy")), 1.0)
        weights.append(score)

    total_weight = sum(weights)
    prediction = 0.0
    accuracy = 0.0
    directional_accuracy = 0.0

    for model, weight in zip(available, weights):
        normalized = weight / total_weight
        prediction += _safe_float(model.get("prediction")) * normalized
        accuracy += _safe_float(model.get("accuracy")) * normalized
        directional_accuracy += _safe_float(model.get("directional_accuracy")) * normalized

    return {
        "prediction": round(prediction, 6),
        "accuracy": round(accuracy, 2),
        "directional_accuracy": round(directional_accuracy, 2),
    }


class PredictionCache:
    def __init__(self) -> None:
        self._memory: Dict[str, Dict[str, Any]] = {}
        self._mongo_collection = None

        if USE_MONGO_CACHE and MongoClient is not None:
            try:
                client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=1500)
                client.admin.command("ping")
                self._mongo_collection = client[MONGO_DB][MONGO_COLLECTION]
                self._mongo_collection.create_index("coin_id", unique=True)
            except Exception:
                self._mongo_collection = None

        if CACHE_FILE.exists():
            try:
                self._memory = json.loads(CACHE_FILE.read_text())
            except Exception:
                self._memory = {}

    def _is_fresh(self, payload: Dict[str, Any], ttl_minutes: int) -> bool:
        generated_at = payload.get("generated_at")
        if not generated_at:
            return False

        try:
            generated_time = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        except Exception:
            return False

        age = datetime.now(timezone.utc) - generated_time
        return age <= timedelta(minutes=ttl_minutes)

    def _has_usable_prediction(self, payload: Dict[str, Any]) -> bool:
        predictions = payload.get("predictions") or {}
        if not isinstance(predictions, dict):
            return False

        for horizon in predictions.values():
            if not isinstance(horizon, dict):
                continue
            prediction = horizon.get("prediction")
            if prediction is not None:
                return True
        return False

    def get(self, coin_id: str, ttl_minutes: int) -> Optional[Dict[str, Any]]:
        key = coin_id.lower()

        memory_item = self._memory.get(key)
        if (
            memory_item
            and self._is_fresh(memory_item, ttl_minutes)
            and self._has_usable_prediction(memory_item)
        ):
            return memory_item

        if self._mongo_collection is not None:
            record = self._mongo_collection.find_one({"coin_id": key}, {"_id": 0})
            if (
                record
                and self._is_fresh(record, ttl_minutes)
                and self._has_usable_prediction(record)
            ):
                self._memory[key] = record
                return record

        return None

    def set(self, coin_id: str, payload: Dict[str, Any]) -> None:
        key = coin_id.lower()
        self._memory[key] = payload

        try:
            CACHE_FILE.write_text(json.dumps(self._memory, indent=2))
        except Exception:
            pass

        if self._mongo_collection is not None:
            try:
                self._mongo_collection.update_one(
                    {"coin_id": key},
                    {"$set": payload},
                    upsert=True,
                )
            except Exception:
                pass


class PredictionService:
    def __init__(self) -> None:
        self.cache = PredictionCache()
        self.sentiment_analyzer = SentimentAnalyzer()

    def _predict_horizon(
        self,
        coin_id: str,
        coin_meta: Dict[str, Any],
        sentiment: Dict[str, float],
        horizon: HorizonConfig,
        current_price_hint: Optional[float] = None,
    ) -> Dict[str, Any]:
        history, source, source_errors = fetch_history_for_horizon(
            coin_id,
            coin_meta["ticker"],
            horizon,
            current_price_hint=current_price_hint,
        )
        if history.empty or len(history) < horizon.min_rows:
            return {
                "horizon": horizon.label,
                "error": "Not enough market history for robust training",
                "prediction": None,
                "change_pct": None,
                "accuracy": None,
                "directional_accuracy": None,
                "available_rows": int(len(history)),
                "required_rows": int(horizon.min_rows),
                "data_source": source,
                "data_errors": source_errors,
                "models": [],
            }

        feature_df, feature_cols = build_features(
            history,
            sentiment_score=_safe_float(sentiment.get("sentiment")),
            negative_sentiment=_safe_float(sentiment.get("neg_sentiment")),
            horizon_steps=horizon.steps,
        )

        if len(feature_df) < horizon.min_rows:
            return {
                "horizon": horizon.label,
                "error": "Not enough engineered rows after preprocessing",
                "prediction": None,
                "change_pct": None,
                "accuracy": None,
                "directional_accuracy": None,
                "models": [],
            }

        train_df, test_df = _split_train_test(feature_df)

        models: List[Dict[str, Any]] = []

        try:
            models.append(run_lstm_model(feature_df, feature_cols, horizon.sequence_length))
        except Exception:
            models.append(
                {
                    "model": "LSTM",
                    "prediction": round(float(feature_df["close"].iloc[-1]), 6),
                    "accuracy": 0.0,
                    "directional_accuracy": 0.0,
                    "mape": 100.0,
                }
            )

        try:
            models.append(run_xgboost_model(train_df, test_df, feature_cols))
        except Exception:
            models.append(
                {
                    "model": "XGBoost",
                    "prediction": round(float(feature_df["close"].iloc[-1]), 6),
                    "accuracy": 0.0,
                    "directional_accuracy": 0.0,
                    "mape": 100.0,
                }
            )

        try:
            models.append(run_sentiment_model(train_df, test_df))
        except Exception:
            models.append(
                {
                    "model": "Transformer Sentiment",
                    "prediction": round(float(feature_df["close"].iloc[-1]), 6),
                    "accuracy": 0.0,
                    "directional_accuracy": 0.0,
                    "mape": 100.0,
                }
            )

        ensemble = ensemble_models(models)
        last_close = float(feature_df["close"].iloc[-1])
        predicted = _safe_float(ensemble.get("prediction"), last_close)
        change_pct = ((predicted - last_close) / last_close) * 100 if last_close else 0.0

        return {
            "horizon": horizon.label,
            "prediction": round(predicted, 6),
            "change_pct": round(change_pct, 3),
            "current_price": round(last_close, 6),
            "accuracy": ensemble["accuracy"],
            "directional_accuracy": ensemble["directional_accuracy"],
            "available_rows": int(len(history)),
            "required_rows": int(horizon.min_rows),
            "data_source": source,
            "data_errors": source_errors,
            "models": models,
        }

    def generate_predictions(
        self,
        coin_id: str,
        force_refresh: bool = False,
        current_price_hint: Optional[float] = None,
    ) -> Dict[str, Any]:
        key = coin_id.lower().strip()

        if not force_refresh:
            cached = self.cache.get(key, ttl_minutes=CACHE_TTL_MINUTES)
            if cached:
                return cached

        meta = resolve_coin_metadata(key)
        if meta.get("current_price_usd") is None and current_price_hint is not None:
            meta["current_price_usd"] = current_price_hint
        sentiment = self.sentiment_analyzer.score_coin(meta["name"])

        horizon_results: Dict[str, Any] = {}
        for horizon_key, horizon in HORIZONS.items():
            try:
                horizon_results[horizon_key] = self._predict_horizon(
                    key,
                    meta,
                    sentiment,
                    horizon,
                    current_price_hint=current_price_hint,
                )
            except Exception as exc:
                horizon_results[horizon_key] = {
                    "horizon": horizon.label,
                    "error": f"Prediction failed: {exc}",
                    "prediction": None,
                    "change_pct": None,
                    "accuracy": None,
                    "directional_accuracy": None,
                    "models": [],
                }

        payload = {
            "coin_id": key,
            "coin_name": meta["name"],
            "coin_symbol": meta["symbol"],
            "ticker": meta["ticker"],
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "sentiment": {
                "score": round(_safe_float(sentiment.get("sentiment")), 4),
                "negative_ratio": round(_safe_float(sentiment.get("neg_sentiment")), 4),
                "sample_size": int(sentiment.get("sample_size") or 0),
            },
            "predictions": horizon_results,
        }

        if self.cache._has_usable_prediction(payload):
            self.cache.set(key, payload)
        return payload


prediction_service = PredictionService()
