import React from 'react';
import { Box, Typography } from '@mui/material';

const LoginPage: React.FC = () => {
  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight="100vh"
    >
      <Typography variant="h4">로그인 페이지</Typography>
    </Box>
  );
};

export default LoginPage;