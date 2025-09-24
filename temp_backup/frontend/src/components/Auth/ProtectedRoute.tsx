import React, { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, Alert, AlertTitle } from '@mui/material';

import { useAuth } from '../../contexts/AuthContext';
import authService from '../../services/authService';

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: 'admin' | 'analyst' | 'viewer';
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRole = 'viewer' 
}) => {
  const { isAuthenticated, user } = useAuth();
  const location = useLocation();

  // 인증되지 않은 경우 로그인 페이지로 리다이렉트
  if (!isAuthenticated) {
    return (
      <Navigate 
        to="/login" 
        state={{ from: location }} 
        replace 
      />
    );
  }

  // 권한 확인
  if (!authService.hasRole(requiredRole)) {
    return (
      <Box p={3}>
        <Alert severity="error">
          <AlertTitle>접근 권한 없음</AlertTitle>
          이 페이지에 접근할 권한이 없습니다. 
          {requiredRole === 'admin' && '관리자 권한이 필요합니다.'}
          {requiredRole === 'analyst' && '분석가 이상의 권한이 필요합니다.'}
          <br />
          현재 권한: {user?.role}
        </Alert>
      </Box>
    );
  }

  return <>{children}</>;
};

export default ProtectedRoute;