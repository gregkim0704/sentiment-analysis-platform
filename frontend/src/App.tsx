import React from 'react';
import { Box, Typography, Container } from '@mui/material';

const App: React.FC = () => {
  return (
    <Container maxWidth="lg">
      <Box
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
        textAlign="center"
      >
        <Typography variant="h2" component="h1" gutterBottom color="primary">
          🎉 센티멘트 분석 플랫폼
        </Typography>
        
        <Typography variant="h5" component="h2" gutterBottom color="text.secondary">
          멀티 스테이크홀더 센티멘트 분석 시스템
        </Typography>
        
        <Box mt={4}>
          <Typography variant="body1" paragraph>
            ✅ 프론트엔드: React + TypeScript + Material-UI
          </Typography>
          <Typography variant="body1" paragraph>
            ✅ 백엔드: FastAPI + Python
          </Typography>
          <Typography variant="body1" paragraph>
            ✅ 배포: Railway 클라우드 플랫폼
          </Typography>
        </Box>
        
        <Box mt={4} p={3} bgcolor="background.paper" borderRadius={2} boxShadow={1}>
          <Typography variant="h6" gutterBottom>
            🚀 배포 성공!
          </Typography>
          <Typography variant="body2" color="text.secondary">
            풀스택 애플리케이션이 성공적으로 배포되었습니다.
          </Typography>
        </Box>
      </Box>
    </Container>
  );
};

export default App;