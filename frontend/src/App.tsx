import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';

import { useAuth } from './contexts/AuthContext';
import Layout from './components/Layout/Layout';
import ProtectedRoute from './components/Auth/ProtectedRoute';

// 페이지 컴포넌트들 (Lazy Loading)
const LoginPage = React.lazy(() => import('./pages/Auth/LoginPage'));
const DashboardPage = React.lazy(() => import('./pages/Dashboard/DashboardPage'));
const CompaniesPage = React.lazy(() => import('./pages/Companies/CompaniesPage'));
const SentimentPage = React.lazy(() => import('./pages/Sentiment/SentimentPage'));
const StakeholdersPage = React.lazy(() => import('./pages/Stakeholders/StakeholdersPage'));
const CrawlingPage = React.lazy(() => import('./pages/Crawling/CrawlingPage'));
const AnalysisPage = React.lazy(() => import('./pages/Analysis/AnalysisPage'));
const UsersPage = React.lazy(() => import('./pages/Users/UsersPage'));
const SettingsPage = React.lazy(() => import('./pages/Settings/SettingsPage'));
const NotFoundPage = React.lazy(() => import('./pages/NotFound/NotFoundPage'));

// 로딩 컴포넌트
const LoadingFallback: React.FC = () => (
  <Box
    display="flex"
    justifyContent="center"
    alignItems="center"
    minHeight="200px"
  >
    <CircularProgress />
  </Box>
);

const App: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  // 초기 로딩 중
  if (isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <React.Suspense fallback={<LoadingFallback />}>
        <Routes>
          {/* 로그인 페이지 */}
          <Route
            path="/login"
            element={
              isAuthenticated ? (
                <Navigate to="/dashboard" replace />
              ) : (
                <LoginPage />
              )
            }
          />

          {/* 보호된 라우트들 */}
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <Layout>
                  <Routes>
                    {/* 대시보드 */}
                    <Route path="/dashboard" element={<DashboardPage />} />
                    
                    {/* 회사 관리 */}
                    <Route path="/companies" element={<CompaniesPage />} />
                    
                    {/* 센티멘트 분석 */}
                    <Route path="/sentiment" element={<SentimentPage />} />
                    
                    {/* 스테이크홀더 분석 */}
                    <Route path="/stakeholders" element={<StakeholdersPage />} />
                    
                    {/* 크롤링 관리 */}
                    <Route 
                      path="/crawling" 
                      element={
                        <ProtectedRoute requiredRole="analyst">
                          <CrawlingPage />
                        </ProtectedRoute>
                      } 
                    />
                    
                    {/* 분석 관리 */}
                    <Route 
                      path="/analysis" 
                      element={
                        <ProtectedRoute requiredRole="analyst">
                          <AnalysisPage />
                        </ProtectedRoute>
                      } 
                    />
                    
                    {/* 사용자 관리 (관리자만) */}
                    <Route 
                      path="/users" 
                      element={
                        <ProtectedRoute requiredRole="admin">
                          <UsersPage />
                        </ProtectedRoute>
                      } 
                    />
                    
                    {/* 설정 */}
                    <Route path="/settings" element={<SettingsPage />} />
                    
                    {/* 기본 리다이렉트 */}
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    
                    {/* 404 페이지 */}
                    <Route path="*" element={<NotFoundPage />} />
                  </Routes>
                </Layout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </React.Suspense>
  );
};

export default App;