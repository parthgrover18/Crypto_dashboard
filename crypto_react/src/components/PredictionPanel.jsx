import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  Divider,
  Chip,
} from '@mui/material';
import { PredictionEndpoint } from '../config/predictionApi';

const HORIZON_ORDER = ['1h', '1d', '1w'];

const formatCurrency = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '--';
  }

  return Number(value).toLocaleString(undefined, {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: Number(value) >= 1 ? 2 : 6,
  });
};

const formatPct = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '--';
  }

  const fixed = Number(value).toFixed(2);
  return `${Number(value) > 0 ? '+' : ''}${fixed}%`;
};

function PredictionPanel({ coinId, currentPriceUsd }) {
  const [predictionData, setPredictionData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let isMounted = true;

    const fetchPredictions = async () => {
      if (!coinId) return;

      setLoading(true);
      setError('');

      try {
        const query = new URLSearchParams();
        if (Number.isFinite(Number(currentPriceUsd))) {
          query.set('current_price_usd', String(currentPriceUsd));
        }
        const baseUrl = PredictionEndpoint(coinId);
        const url = query.toString() ? `${baseUrl}?${query.toString()}` : baseUrl;

        const { data } = await axios.get(url, {
          timeout: 60000,
        });

        const horizons = Object.values(data?.predictions || {});
        const allFailed =
          horizons.length > 0 &&
          horizons.every(
            (item) => item && (item.prediction === null || item.prediction === undefined)
          );

        let finalData = data;

        if (allFailed) {
          if (Number.isFinite(Number(currentPriceUsd))) {
            query.set('current_price_usd', String(currentPriceUsd));
          }
          query.set('force_refresh', 'true');
          const { data: refreshed } = await axios.get(
            `${PredictionEndpoint(coinId)}?${query.toString()}`,
            {
              timeout: 90000,
            }
          );
          finalData = refreshed;
        }

        if (isMounted) {
          setPredictionData(finalData);
        }
      } catch (err) {
        if (isMounted) {
          setError(
            err?.response?.data?.detail ||
              'Prediction backend is unavailable. Start backend/api_server.py to view AI predictions.'
          );
          setPredictionData(null);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchPredictions();

    return () => {
      isMounted = false;
    };
  }, [coinId]);

  return (
    <Paper
      elevation={6}
      sx={{
        width: '100%',
        maxWidth: '900px',
        mx: 'auto',
        mt: 3,
        p: { xs: 2, md: 3 },
        borderRadius: '20px',
        backgroundColor: '#050505',
        color: 'white',
        border: '1px solid #1b1b1b',
      }}
    >
      <Typography
        variant='h5'
        sx={{
          fontWeight: 700,
          color: '#6ee755',
          mb: 1,
          letterSpacing: 0.5,
        }}
      >
        AI Price Predictions
      </Typography>

      <Typography variant='body2' sx={{ color: '#9f9f9f', mb: 2 }}>
        Forecast horizons: 1 hour, 1 day, and 1 week. Prices are shown in USD.
      </Typography>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 5 }}>
          <CircularProgress sx={{ color: '#6ee755' }} />
        </Box>
      )}

      {!loading && error && (
        <Typography sx={{ color: '#ff6b6b', py: 2 }} variant='body2'>
          {error}
        </Typography>
      )}

      {!loading && !error && predictionData?.predictions && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {HORIZON_ORDER.map((horizonKey) => {
            const row = predictionData.predictions[horizonKey];
            if (!row) return null;

            const isPositive = Number(row.change_pct) >= 0;

            return (
              <Box
                key={horizonKey}
                sx={{
                  border: '1px solid #242424',
                  borderRadius: '14px',
                  p: 2,
                  background:
                    'linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01))',
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    rowGap: 1,
                  }}
                >
                  <Typography sx={{ fontWeight: 600, color: '#f1f1f1' }}>
                    {row.horizon}
                  </Typography>

                  {row.error ? (
                    <Box sx={{ textAlign: 'right' }}>
                      <Typography variant='body2' sx={{ color: '#ff9b9b' }}>
                        {row.error}
                      </Typography>
                      {row.data_source && (
                        <Typography variant='caption' sx={{ color: '#a0a0a0' }}>
                          Source: {row.data_source}
                        </Typography>
                      )}
                    </Box>
                  ) : (
                    <Box sx={{ textAlign: 'right' }}>
                      <Typography sx={{ color: '#d7d7d7', fontSize: 13 }}>
                        Predicted Price
                      </Typography>
                      <Typography sx={{ fontWeight: 700, fontSize: 20 }}>
                        {formatCurrency(row.prediction)}
                      </Typography>
                    </Box>
                  )}
                </Box>

                {!row.error && (
                  <>
                    <Typography
                      sx={{
                        mt: 1,
                        fontWeight: 600,
                        color: isPositive ? '#6ee755' : '#ff6b6b',
                      }}
                    >
                      {formatPct(row.change_pct)}
                    </Typography>

                    <Box
                      sx={{
                        display: 'flex',
                        gap: 1,
                        flexWrap: 'wrap',
                        mt: 1.5,
                      }}
                    >
                      <Chip
                        label={`Ensemble Accuracy: ${formatPct(row.accuracy)}`}
                        size='small'
                        sx={{ background: '#1d3117', color: '#cfffbd' }}
                      />
                      <Chip
                        label={`Directional: ${formatPct(row.directional_accuracy)}`}
                        size='small'
                        sx={{ background: '#10283a', color: '#aee3ff' }}
                      />
                    </Box>

                    {row.models?.length > 0 && (
                      <>
                        <Divider sx={{ my: 1.5, backgroundColor: '#252525' }} />
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                          {row.models.map((model) => (
                            <Chip
                              key={`${horizonKey}-${model.model}`}
                              label={`${model.model}: ${formatPct(model.accuracy)}`}
                              size='small'
                              sx={{
                                background: '#151515',
                                color: '#e7e7e7',
                                border: '1px solid #2e2e2e',
                              }}
                            />
                          ))}
                        </Box>
                      </>
                    )}
                  </>
                )}
              </Box>
            );
          })}
        </Box>
      )}
    </Paper>
  );
}

export default PredictionPanel;
