import {
  AppBar,
  Container,
  MenuItem,
  Select,
  Toolbar,
  Typography,
  Box,
  TextField,
  List,
  ListItem,
  ListItemText,
  Paper,
  Backdrop,
  ClickAwayListener,
} from '@mui/material';
import { ThemeProvider, createTheme, styled } from '@mui/material/styles';
import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { cryptoState } from '../CryptoContext';
import { CoinList } from '../config/api';
import axios from 'axios';
import { handleSearch } from '../components/Coinstable';

const Title = styled(Typography)({
  color: 'white',
  fontFamily: "'Great Vibes', cursive",
  fontWeight: 'bold',
  cursor: 'pointer',
  fontSize: 30,
  padding: '12px 0',
  whiteSpace: 'nowrap',
  flexShrink: 0,
});

const HeaderLink = styled(Typography, {
  shouldForwardProp: (prop) => prop !== 'active',
})(({ active }) => ({
  color: 'white',
  fontFamily: 'Montserrat',
  fontWeight: 500,
  cursor: 'pointer',
  fontSize: 18,
  padding: '8px 16px',
  transition: 'all 0.3s ease',
  borderBottom: active ? '3px solid #6ee755' : '3px solid transparent',
  '&:hover': {
    color: '#ccc',
  },
}));

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#fff',
    },
  },
});

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { currency, setCurrency } = cryptoState();
  const [search, setSearch] = useState('');
  const [coins, setCoins] = useState([]);
  const [searchFocused, setSearchFocused] = useState(false);

  const fetchCoins = async () => {
    const { data } = await axios.get(CoinList(currency));
    setCoins(data);
  };

  useEffect(() => {
    fetchCoins();
  }, [currency]);

  const isActive = (path) => location.pathname === path;
  const filteredCoins = handleSearch(coins, search);

  return (
    <ThemeProvider theme={darkTheme}>

      <Backdrop
        open={searchFocused}
        sx={{
          zIndex: 1090,
          backgroundColor: 'rgba(0, 0, 0, 0.6)',
        }}
        onClick={() => {
          if (search === '') setSearchFocused(false);
        }}
      />

      <AppBar
        position="sticky"
        sx={{
          top: 0,
          zIndex: 1101,
          background: 'rgba(0, 0, 0, 0.6)',
          backdropFilter: 'blur(10px)',
          boxShadow: '0 4px 10px rgba(0, 0, 0, 0.2)',
        }}
      >
        <Container maxWidth="xl">
          <Toolbar sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            
            <Title onClick={() => navigate('/')}>Coinlytics</Title>

            <ClickAwayListener onClickAway={() => {
              if (search === '') setSearchFocused(false);
            }}>
              <Box
                sx={{
                  flexGrow: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 3,
                  position: 'relative',
                }}
              >
                <Box sx={{ position: 'relative', width: searchFocused ? 500 : 300, transition: 'width 0.3s ease' }}>
                  <TextField
                    variant="outlined"
                    placeholder="Search..."
                    onFocus={() => setSearchFocused(true)}
                    onChange={(e) => setSearch(e.target.value)}
                    value={search}
                    fullWidth
                    InputProps={{
                      startAdornment: (
                        <Box sx={{ pl: 1, display: 'flex', alignItems: 'center' }}>
                          <img
                            src="https://img.icons8.com/ios-glyphs/30/ffffff/search--v1.png"
                            alt="search"
                            style={{ width: 18, height: 18, opacity: 0.7 }}
                          />
                        </Box>
                      ),
                      sx: {
                        backgroundColor: 'rgba(255, 255, 255, 0.05)',
                        color: 'white',
                        height: 40,
                        borderRadius: '25px',
                        fontSize: 14,
                        paddingX: 1.5,
                        '& .MuiOutlinedInput-notchedOutline': {
                          border: 'none',
                        },
                        '&:hover .MuiOutlinedInput-notchedOutline': {
                          borderColor: 'transparent',
                        },
                        '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                          borderColor: '#6ee755',
                        },
                      },
                    }}
                    sx={{
                      input: {
                        color: 'white',
                        padding: '10px',
                      },
                    }}
                  />

                  {searchFocused && search && (
                    <Paper
                      sx={{
                        position: 'absolute',
                        top: 50,
                        width: '100%',
                        backgroundColor: '#121212',
                        color: 'white',
                        borderRadius: '12px',
                        zIndex: 1200,
                        boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
                        maxHeight: 300,
                        overflowY: 'auto',
                      }}
                    >
                      <List>
                        {filteredCoins.slice(0, 8).map((coin) => (
                          <ListItem
                            button
                            key={coin.id}
                            onMouseDown={() => navigate(`/coins/${coin.id}`)}
                          >
                            <img src={coin.image} alt={coin.name} height="20" style={{ marginRight: 10 }} />
                            <ListItemText
                              primary={coin.name}
                              secondary={coin.symbol.toUpperCase()}
                              primaryTypographyProps={{ style: { color: 'white', fontWeight: 500 } }}
                              secondaryTypographyProps={{ style: { color: '#ccc' } }}
                            />
                          </ListItem>
                        ))}
                      </List>
                    </Paper>
                  )}
                </Box>

                {!searchFocused && (
                  <>
                    <HeaderLink active={isActive('/')} onClick={() => navigate('/')}>Home</HeaderLink>
                    <HeaderLink active={isActive('/news')} onClick={() => navigate('/news')}>News</HeaderLink>
                    <HeaderLink active={isActive('/indicators')} onClick={() => navigate('/indicators')}>Indicators</HeaderLink>
                    <HeaderLink active={isActive('/blog')} onClick={() => navigate('/blog')}>Blog</HeaderLink>
                  </>
                )}
              </Box>
            </ClickAwayListener>

            <Box sx={{ flexShrink: 0 }}>
              <Select
                variant="outlined"
                sx={{
                  width: 100,
                  height: 40,
                  color: 'white',
                  background: 'rgba(255, 255, 255, 0.2)',
                  borderRadius: '8px',
                  '& .MuiOutlinedInput-notchedOutline': {
                    border: 'none',
                  },
                  '& .MuiSelect-select': {
                    color: 'white',
                  },
                  '& .MuiSvgIcon-root': {
                    color: 'white',
                  },
                }}
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
              >
                <MenuItem value="USD">USD</MenuItem>
                <MenuItem value="GBP">GBP</MenuItem>
              </Select>
            </Box>
          </Toolbar>
        </Container>
      </AppBar>
    </ThemeProvider>
  );
};

export default Header;