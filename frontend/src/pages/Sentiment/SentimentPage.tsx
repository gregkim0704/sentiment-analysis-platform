import React from 'react';
import { Box, Typography } from '@mui/material';

const SentimentPage: React.FC = () => {
  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        센티멘트 분석
      </Typography>
      <Typography variant="body1">
        센티멘트 분석 페이지입니다.
      </Typography>
    </Box>
  );
};

export default SentimentPage;