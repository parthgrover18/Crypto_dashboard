import axios from 'axios';
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CoinList } from '../config/api';
import { cryptoState } from '../CryptoContext';
import {
  Container,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Box,
  Pagination,
} from '@mui/material';
import { ThemeProvider, createTheme, styled } from '@mui/material/styles';

const GREEN = '#6ee755';
const ROWS_PER_PAGE = 10;

const Heading = styled(Box)({
  padding: '20vh 0 1vh',
  display: 'flex',
  justifyContent: 'flex-start',
  alignItems: 'flex-end',
});

const PageInfo = styled(Box)({
  paddingTop: '6vh',
  paddingBottom: '2vh',
  display: 'flex',
  justifyContent: 'flex-end',
});

const CoinRow = styled(TableRow)({
  backgroundColor: '#0f0f0f',
  cursor: 'pointer',
  '&:hover': {
    backgroundColor: '#1a1a1a',
  },
  transition: 'all 0.2s ease-in-out',
});

function numberWithCommas(x) {
  return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function Coinstable() {
  const [coins, setCoins] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  const { currency, symbol } = cryptoState();
  const navigate = useNavigate();

  const fetchCoins = async () => {
    setLoading(true);
    const { data } = await axios.get(CoinList(currency));
    setCoins(data);
    setLoading(false);
  };

  useEffect(() => {
    fetchCoins();
  }, [currency]);

  const handleSearch = () => {
    return coins.filter(
      (coin) =>
        coin.name.toLowerCase().includes(search.toLowerCase()) ||
        coin.symbol.toLowerCase().includes(search.toLowerCase())
    );
  };

  const filteredCoins = handleSearch();
  const totalPages = Math.ceil(filteredCoins.length / ROWS_PER_PAGE);
  const paginatedCoins = filteredCoins.slice(
    (page - 1) * ROWS_PER_PAGE,
    page * ROWS_PER_PAGE
  );

  const darkTheme = createTheme({
    palette: {
      mode: 'dark',
      primary: { main: '#fff' },
    },
  });

  return (
    <ThemeProvider theme={darkTheme}>
      <Container>
        <Heading>
          <Typography
            variant="h4"
            sx={{
              fontFamily: 'Montserrat',
              fontWeight: 700,
              color: 'white',
            }}
          >
            Market Summary
          </Typography>
        </Heading>

        <PageInfo>
          <Typography
            variant="body2"
            sx={{
              color: '#888',
              fontFamily: 'Montserrat',
            }}
          >
            Showing page {page} of {totalPages}
          </Typography>
        </PageInfo>

        <TableContainer>
          {loading ? (
            <LinearProgress style={{ backgroundColor: GREEN }} />
          ) : (
            <Table>
              <TableHead>
                <TableRow sx={{ backgroundColor: 'black' }}>
                  {[
                    'Rank',
                    'Name',
                    'Symbol',
                    'Last Price',
                    '24h %',
                    'Market Cap',
                    'Volume',
                    'Supply',
                  ].map((head) => (
                    <TableCell
                      key={head}
                      align="center"
                      sx={{
                        borderTop: '1px solid #2a2a2a',
                        color: 'white',
                        fontWeight: 'bold',
                        fontFamily: 'Montserrat',
                        fontSize: 14,
                        borderBottom: '1px solid #2a2a2a',
                      }}
                    >
                      {head}
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>

                <TableBody>
                {paginatedCoins.map((row) => {
                  const change24h = Number(row.price_change_percentage_24h);
                  const currentPrice = Number(row.current_price);
                  const marketCap = Number(row.market_cap);
                  const totalVolume = Number(row.total_volume);
                  const circulatingSupply = Number(row.circulating_supply);
                  const hasChange24h = Number.isFinite(change24h);
                  const profit = hasChange24h && change24h > 0;

                  return (
                    <CoinRow
                      key={row.id}
                      onClick={() => navigate(`/coins/${row.id}`)}
                    >
                      <TableCell align="center" sx={{ color: 'white' }}>
                        #{row.market_cap_rank}
                      </TableCell>

                      <TableCell
                        align="center"
                        sx={{ display: 'flex', alignItems: 'center', gap: 2 }}
                      >
                        <img src={row.image} alt={row.name} height="28" />
                        <Box>
                          <Typography sx={{ color: 'white', fontWeight: 600 }}>
                            {row.name}
                          </Typography>
                        </Box>
                      </TableCell>

                      <TableCell align="center" sx={{ color: '#bbb' }}>
                        {row.symbol.toUpperCase()}
                      </TableCell>

                      <TableCell align="center" sx={{ color: 'white' }}>
                        {Number.isFinite(currentPrice)
                          ? `${symbol} ${numberWithCommas(currentPrice.toFixed(2))}`
                          : '--'}
                      </TableCell>

                      <TableCell
                        align="center"
                        sx={{
                          color: hasChange24h ? (profit ? GREEN : 'red') : '#bbb',
                          fontWeight: 500,
                        }}
                      >
                        {hasChange24h
                          ? `${profit ? '+' : ''}${change24h.toFixed(2)}%`
                          : 'N/A'}
                      </TableCell>

                      <TableCell align="center" sx={{ color: 'white' }}>
                        {Number.isFinite(marketCap)
                          ? `${symbol} ${numberWithCommas((marketCap / 1e6).toFixed(0))}M`
                          : '--'}
                      </TableCell>

                      <TableCell align="center" sx={{ color: 'white' }}>
                        {Number.isFinite(totalVolume)
                          ? `${symbol} ${numberWithCommas((totalVolume / 1e6).toFixed(0))}M`
                          : '--'}
                      </TableCell>

                      <TableCell align="center" sx={{ color: 'white' }}>
                        {Number.isFinite(circulatingSupply)
                          ? numberWithCommas(circulatingSupply.toFixed(0))
                          : '--'}
                      </TableCell>
                    </CoinRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </TableContainer>

        {!loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <Pagination
              count={totalPages}
              page={page}
              onChange={(_, value) => setPage(value)}
              shape="rounded"
              sx={{
                '& .MuiPaginationItem-root': {
                  color: 'white',
                  borderColor: GREEN,
                  '&.Mui-selected': {
                    backgroundColor: GREEN,
                    color: 'black',
                  },
                  '&:hover': {
                    backgroundColor: 'rgba(110, 231, 85, 0.2)',
                  },
                },
              }}
            />
          </Box>
        )}
      </Container>
    </ThemeProvider>
  );
}

export default Coinstable;



export const handleSearch = (coins, query) => {
  return coins.filter(
    (coin) =>
      coin.name.toLowerCase().includes(query.toLowerCase()) ||
      coin.symbol.toLowerCase().includes(query.toLowerCase())
  );
};
