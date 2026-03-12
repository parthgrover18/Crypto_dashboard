# Coinlytics Dashboard (Frontend)

React dashboard for crypto market data with per-coin AI prediction cards.

## Features

- Live coin market data via CoinGecko
- Historical chart for each coin
- AI prediction panel on each coin page:
  - 1 hour forecast
  - 1 day forecast
  - 1 week forecast
  - Ensemble and model-wise accuracy

## Run

```bash
cd /Users/dell/non\ icloud\ files/websites/crypto\ website/crypto_react
npm install
npm run dev
```

Frontend expects prediction backend at `http://127.0.0.1:8000` by default.

Set custom backend URL:

```bash
cp .env.example .env
# edit VITE_PREDICTION_API_URL
```

