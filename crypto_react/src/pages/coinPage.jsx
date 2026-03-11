import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { cryptoState } from '../CryptoContext';
import axios from 'axios';
import { SingleCoin } from '../config/api';
import CoinInfo from '../components/CoinInfo';
import PredictionPanel from '../components/PredictionPanel';
import {
  Box,
  Typography,
  useTheme,
  useMediaQuery,
  Divider,
  Paper,
} from '@mui/material';
import HTMLReactParser from 'html-react-parser';

const numberWithCommas = (x) => {
  return x?.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
};

const CoinPage = () => {
  const { id } = useParams();
  const [coin, setCoin] = useState();

  const { currency, symbol } = cryptoState();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const fetchCoin = async () => {
    const { data } = await axios.get(SingleCoin(id));
    setCoin(data);
  };

  useEffect(() => {
    fetchCoin();
  }, []);

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        alignItems: isMobile ? 'center' : 'flex-start',
        padding: 2,
      }}
    >
      <Paper
        elevation={4}
        sx={{
          background: '#121212',
          borderRadius: '16px',
          padding: 4,
          width: isMobile ? '100%' : '28%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          marginTop: 4,
          marginBottom: isMobile ? 4 : 0,
          marginRight: isMobile ? 0 : 4,
        }}
      >
        {coin?.image?.large && (
          <img
            src={coin.image.large}
            alt={coin?.name}
            height="120"
            style={{ marginBottom: 20 }}
          />
        )}

        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            fontFamily: 'Montserrat',
            textAlign: 'center',
            marginBottom: 1,
            color: '#fff',
          }}
        >
          {coin?.name}
        </Typography>

        {coin?.description?.en && (
          <Typography
            variant="body2"
            sx={{
              fontFamily: 'Montserrat',
              textAlign: 'justify',
              color: '#bbb',
              marginBottom: 2,
            }}
          >
            {HTMLReactParser(coin.description.en.split('. ')[0] + '.')}
          </Typography>
        )}

        <Divider sx={{ width: '100%', marginBottom: 2, background: '#333' }} />

        <Box sx={{ width: '100%' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body1" sx={{ color: '#aaa' }}>Rank:</Typography>
            <Typography variant="body1" sx={{ color: '#fff' }}>
              {numberWithCommas(coin?.market_cap_rank)}
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body1" sx={{ color: '#aaa' }}>Current Price:</Typography>
            <Typography variant="body1" sx={{ color: '#fff' }}>
              {symbol}{' '}
              {numberWithCommas(coin?.market_data?.current_price?.[currency.toLowerCase()])}
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="body1" sx={{ color: '#aaa' }}>Market Cap:</Typography>
            <Typography variant="body1" sx={{ color: '#fff' }}>
              {symbol}{' '}
              {numberWithCommas(
                coin?.market_data?.market_cap?.[currency.toLowerCase()]?.toString().slice(0, -6)
              )}M
            </Typography>
          </Box>
        </Box>
      </Paper>

      <Box sx={{ width: '100%', flex: 1 }}>
        <CoinInfo coin={coin} />
        {coin?.id && (
          <PredictionPanel
            coinId={coin.id}
            currentPriceUsd={coin?.market_data?.current_price?.usd}
          />
        )}
      </Box>
    </Box>
  );
};

export default CoinPage;
