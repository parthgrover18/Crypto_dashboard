import React, { useEffect, useState } from 'react';
import { cryptoState } from '../CryptoContext';
import { HistoricalChart } from '../config/api';
import axios from 'axios';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import {
  CircularProgress,
  Box,
  Typography,
  Paper,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import { Line } from 'react-chartjs-2';
import SelectButton from '../components/SelectButton';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { chartDays } from '../config/data';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const CoinInfo = ({ coin }) => {
  const [historicData, setHistoricData] = useState();
  const [days, setDays] = useState(1);
  const { currency } = cryptoState();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const fetchHistoricData = async () => {
    if (!coin?.id) return;
    try {
      const { data } = await axios.get(HistoricalChart(coin.id, days, currency));
      setHistoricData(data.prices);
    } catch (err) {
      console.error('Error fetching chart data:', err);
    }
  };

  useEffect(() => {
    fetchHistoricData();
  }, [currency, days, coin]);

  const darkTheme = createTheme({
    palette: {
      mode: 'dark',
      primary: { main: '#6ee755' },
      background: { default: '#121212', paper: '#1e1e1e' },
    },
    typography: {
      fontFamily: 'Montserrat, sans-serif',
    },
  });

  return (
    <ThemeProvider theme={darkTheme}>
      <Paper
        elevation={6}
        sx={{
          width: '100%',
          maxWidth: '900px',
          mx: 'auto',
          mt: 4,
          p: isMobile ? 2 : 4,
          borderRadius: '20px',
          backgroundColor: 'black',
          color: 'white',
          boxShadow: '0 8px 30px rgba(0,0,0,0.4)',
        }}
      >
        <Typography
          variant="h5"
          sx={{
            textAlign: 'center',
            mb: 3,
            fontWeight: 600,
            letterSpacing: 1,
            color: 'primary.main',
          }}
        >
          {coin?.name} Price Chart
        </Typography>

        {!historicData ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 5 }}>
            <CircularProgress style={{ color: '#6ee755' }} size={200} thickness={1.2} />
          </Box>
        ) : (
          <Box sx={{ height: 400 }}>
            <Line
              data={{
                labels: historicData.map((point) => {
                  const date = new Date(point[0]);
                  const hours = date.getHours().toString().padStart(2, '0');
                  const minutes = date.getMinutes().toString().padStart(2, '0');
                  const time = `${hours}:${minutes}`;
                  return days === 1 ? time : date.toLocaleDateString();
                }),
                datasets: [
                  {
                    data: historicData.map((point) => point[1]),
                    label: `Price (Past ${days} Day${days > 1 ? 's' : ''}) in ${currency}`,
                    borderColor: '#6ee755',
                    backgroundColor: 'rgba(110, 231, 85, 0.08)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                  },
                ],
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { labels: { color: 'white' } },
                  tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: '#2a2a2a',
                    titleColor: '#fff',
                    bodyColor: '#6ee755',
                    borderColor: '#6ee755',
                    borderWidth: 1,
                  },
                },
                scales: {
                  x: {
                    ticks: { color: '#ccc' },
                    grid: { color: '#2a2a2a' },
                  },
                  y: {
                    ticks: { color: '#ccc' },
                    grid: { color: '#2a2a2a' },
                  },
                },
              }}
            />
          </Box>
        )}

        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            flexWrap: 'wrap',
            gap: 2,
            mt: 4,
          }}
        >
          {chartDays.map((day) => (
            <SelectButton
              key={day.value}
              onClick={() => setDays(day.value)}
              selected={day.value === days}
            >
              {day.label}
            </SelectButton>
          ))}
        </Box>
      </Paper>
    </ThemeProvider>
  );
};

export default CoinInfo;
