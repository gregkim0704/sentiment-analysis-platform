import React from 'react';
import { Box, Typography } from '@mui/material';

const UsersPage: React.FC = () => {
  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        사용자 관리
      </Typography>
      <Typography variant="body1">
        사용자 관리 페이지입니다.
      </Typography>
    </Box>
  );
};

export default UsersPage;