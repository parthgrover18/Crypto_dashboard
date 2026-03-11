import { makeStyles } from '@mui/styles';
import axios from 'axios';
import React, { useEffect, useState } from 'react';
import { cryptoState } from '../CryptoContext';
import { TrendingCoins } from '../config/api';
import AliceCarousel from 'react-alice-carousel';
import { Link } from 'react-router-dom';

const useStyles = makeStyles(() => ({
  carouselWrapper: {
    backgroundColor: '#000',
    paddingLeft: '10vw',
    paddingRight: '10vw',
    '@media (max-width: 768px)': {
      paddingLeft: '16px',
      paddingRight: '16px',
    },
  },
  carousel: {
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    padding: '5vh 0',
  },
  carouselItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textDecoration: 'none',
    color: '#fff',
    height: '24vh',
    margin: '2vh',
    background: 'linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02))',
    padding: '24px',
    borderRadius: '20px',
    transition: 'all 0.4s ease-in-out',
    backdropFilter: 'blur(10px)',
    boxShadow: '0 4px 12px rgba(0,0,0,0.12)',
    border: '1px solid rgba(255,255,255,0.06)',
    '&:hover': {
      transform: 'scale(1.05)',
      boxShadow: '0 2px 30px rgba(110, 231, 85, 0.2)',
      background: 'linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03))',
    },
  },
  coinImage: {
    height: 64,
    marginBottom: 14,
    transition: 'transform 0.3s ease-in-out',
    '&:hover': {
      transform: 'scale(1.1)',
    },
  },
  coinSymbol: {
    fontSize: 18,
    fontWeight: 600,
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  coinChange: {
    fontSize: 14,
    fontWeight: 500,
  },
  coinPrice: {
    fontSize: 20,
    fontWeight: 600,
    marginTop: 14,
    color: '#cfcfcf',
  },
}));

function numberWithCommas(number) {
  return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function Carousel() {
  const [trending, setTrending] = useState([]);
  const classes = useStyles();
  const { currency, symbol } = cryptoState();

  const fetchTrendingCoins = async () => {
    const { data } = await axios.get(TrendingCoins(currency));
    setTrending(data);
  };

  useEffect(() => {
    fetchTrendingCoins();
  }, [currency]);

  const items = trending.map((coin) => {
    const profit = coin.price_change_percentage_24h >= 0;

    return (
      <Link className={classes.carouselItem} to={`/coins/${coin.id}`} key={coin.id}>
        <img src={coin?.image} alt={coin.name} className={classes.coinImage} />
        <span className={classes.coinSymbol}>
          {coin?.symbol}{' '}
          <span
            className={classes.coinChange}
            style={{ color: profit ? '#6ee755' : '#ff4b4b' }}
          >
            {profit && '+'}
            {coin?.price_change_percentage_24h?.toFixed(2)}%
          </span>
        </span>
        <span className={classes.coinPrice}>
          {symbol} {numberWithCommas(coin?.current_price.toFixed(2))}
        </span>
      </Link>
    );
  });

  const responsive = {
    0: { items: 2 },
    600: { items: 3 },
    1024: { items: 5 },
  };

  return (
    <div className={classes.carouselWrapper}>
      <div className={classes.carousel}>
        <AliceCarousel
          mouseTracking
          infinite
          autoPlayInterval={3000}
          animationDuration={1800}
          disableDotsControls
          disableButtonsControls
          responsive={responsive}
          items={items}
          autoPlay
        />
      </div>
    </div>
  );
}

export default Carousel;