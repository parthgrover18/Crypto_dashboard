import { React, useState,useEffect } from 'react'
import { Typography, Box } from '@mui/material';

function Banner() {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
      const timer = setTimeout(() => setIsVisible(true), 100);
      return () => clearTimeout(timer);
    }, []);
  return (
    <div>
            <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', md: 'row' },
          alignItems: 'center',
          justifyContent: 'space-between',
          marginTop: '20vh',
          marginBottom: '30vh',
          px: { xs: 4, md: '10vw' },
          py: { xs: 8, md: 0 },
          backgroundColor: '#000',
          color: '#fff',
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? 'translateY(0)' : 'translateY(40px)',
          transition: 'opacity 0.8s ease, transform 0.8s ease',
        }}
      >
        <Box sx={{ flex: 1, textAlign: { xs: 'center', md: 'left' }, mb: { xs: 6, md: 0 } }}>
          <Typography
            variant="h2"
            sx={{
              fontWeight: 700,
              fontSize: { xs: '10vw', sm: '8vw', md: '4vw' },
              lineHeight: 1.2,
              color: '#fff',
              mb: 3,
            }}
          >
            Smart Crypto<br/> <span style={{color:'#6ee755'}}>Trading & Analytics</span>
          </Typography>
          <Typography
            variant="body1"
            sx={{
              fontSize: { xs: '4.5vw', sm: '2vw', md: '1.25vw' },
              color: '#aaa',
              maxWidth: '480px',
              mx: { xs: 'auto', md: 0 },
            }}
          >
            Real-time insights. Seamless execution. All in one sleek dashboard.
          </Typography>
        </Box>

        <Box sx={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
          <video
            playsInline
            muted
            autoPlay
            loop
            preload="auto"
            style={{
              width: '100%',
              maxWidth: '600px',
              height: 'auto',
              objectFit: 'cover',
            }}
          >
            <source
              src="https://videos.ctfassets.net/ilblxxee70tt/50or9ply0PUQSi2S4O0VYg/3101e0825fbbcda9f757b8aec48b2b8b/metal_candlesticks_desktop.mp4"
              type="video/mp4"
            />
          </video>
        </Box>
      </Box>
    </div>
  )
}

export default Banner
