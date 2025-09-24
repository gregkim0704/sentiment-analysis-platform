import React from 'react';
import { Box, Typography } from '@mui/material';

const StakeholdersPage: React.FC = () => {
  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        스테이크홀더 분석
      </Typography>
      <Typography variant="body1">
        스테이크홀더 분석 페이지입니다.
      </Typography>
    </Box>
  );
};

export default StakeholdersPage;