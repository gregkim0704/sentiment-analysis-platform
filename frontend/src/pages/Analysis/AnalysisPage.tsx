import React from 'react';
import { Box, Typography } from '@mui/material';

const AnalysisPage: React.FC = () => {
  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        분석 관리
      </Typography>
      <Typography variant="body1">
        분석 관리 페이지입니다.
      </Typography>
    </Box>
  );
};

export default AnalysisPage;