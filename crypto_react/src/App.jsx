import { BrowserRouter, Route, Routes } from 'react-router-dom';
import './App.css';
import Header from './components/Header';
import Homepage from './pages/homePage';
import Coinpage from './pages/coinPage';
import { styled } from '@mui/material/styles';
import React from 'react';

const AppContainer = styled('div')({
  backgroundColor: 'black',
  color: 'white',
  minHeight: '100vh',
});

function App() {
  return (
    <BrowserRouter>
      <AppContainer>
        <Header />
        <Routes>
          <Route path='/' element={<Homepage />} />
          <Route path='/coins/:id' element={<Coinpage />} />
        </Routes>
      </AppContainer>
    </BrowserRouter>
  );
}

export default App;