import React from 'react';
import { Box, Typography } from '@mui/material';

const CrawlingPage: React.FC = () => {
  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        크롤링 관리
      </Typography>
      <Typography variant="body1">
        크롤링 관리 페이지입니다.
      </Typography>
    </Box>
  );
};

export default CrawlingPage;