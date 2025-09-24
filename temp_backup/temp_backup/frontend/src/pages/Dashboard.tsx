import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  CircularProgress
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  People,
  Business,
  Assessment,
  Notifications
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

import SentimentChart from '@/components/Charts/SentimentChart';
import StakeholderChart from '@/components/Charts/StakeholderChart';
import TrendChart from '@/components/Charts/TrendChart';
import RecentNews from '@/components/Dashboard/RecentNews';
import AlertPanel from '@/components/Dashboard/AlertPanel';
import { dashboardService } from '@/services/dashboardService';
import { Company, StakeholderType } from '@/types';

const Dashboard: React.FC = () => {
  const [selectedCompany, setSelectedCompany] = useState<number | ''>('');
  const [selectedStakeholder, setSelectedStakeholder] = useState<StakeholderType | 'all'>('all');
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');

  // 회사 목록 조회
  const { data: companies = [] } = useQuery<Company[]>(
    'companies',
    dashboardService.getCompanies
  );

  // 대시보드 데이터 조회
  const { data: dashboardData, isLoading } = useQuery(
    ['dashboard', selectedCompany, selectedStakeholder, timeRange],
    () => dashboardService.getDashboardData({
      companyId: selectedCompany || undefined,
      stakeholderType: selectedStakeholder === 'all' ? undefined : selectedStakeholder,
      timeRange
    }),
    {
      enabled: !!selectedCompany,
      refetchInterval: 30000 // 30초마다 자동 새로고침
    }
  );

  // 첫 번째 회사를 기본 선택
  useEffect(() => {
    if (companies.length > 0 && !selectedCompany) {
      setSelectedCompany(companies[0].id);
    }
  }, [companies, selectedCompany]);

  const stakeholderTypes = [
    { value: 'all', label: '전체' },
    { value: 'customer', label: '고객' },
    { value: 'investor', label: '투자자' },
    { value: 'employee', label: '직원' },
    { value: 'government', label: '정부' },
    { value: 'media', label: '언론' },
    { value: 'partner', label: '파트너' },
    { value: 'competitor', label: '경쟁사' },
    { value: 'community', label: '지역사회' }
  ];

  const getSentimentColor = (score: number) => {
    if (score >= 0.5) return '#4caf50';
    if (score >= 0) return '#ff9800';
    return '#f44336';
  };

  const getSentimentIcon = (score: number) => {
    return score >= 0 ? <TrendingUp /> : <TrendingDown />;
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* 헤더 */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          센티멘트 분석 대시보드
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          {format(new Date(), 'yyyy년 MM월 dd일 EEEE', { locale: ko })} 업데이트
        </Typography>
      </Box>

      {/* 필터 */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth>
              <InputLabel>회사 선택</InputLabel>
              <Select
                value={selectedCompany}
                onChange={(e) => setSelectedCompany(e.target.value as number)}
                label="회사 선택"
              >
                {companies.map((company) => (
                  <MenuItem key={company.id} value={company.id}>
                    {company.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth>
              <InputLabel>스테이크홀더</InputLabel>
              <Select
                value={selectedStakeholder}
                onChange={(e) => setSelectedStakeholder(e.target.value as StakeholderType | 'all')}
                label="스테이크홀더"
              >
                {stakeholderTypes.map((type) => (
                  <MenuItem key={type.value} value={type.value}>
                    {type.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth>
              <InputLabel>기간</InputLabel>
              <Select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value as '7d' | '30d' | '90d')}
                label="기간"
              >
                <MenuItem value="7d">최근 7일</MenuItem>
                <MenuItem value="30d">최근 30일</MenuItem>
                <MenuItem value="90d">최근 90일</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {dashboardData && (
        <>
          {/* 주요 지표 카드 */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box>
                      <Typography color="text.secondary" gutterBottom>
                        전체 센티멘트
                      </Typography>
                      <Typography variant="h4">
                        {dashboardData.overallSentiment.toFixed(2)}
                      </Typography>
                      <Chip
                        icon={getSentimentIcon(dashboardData.overallSentiment)}
                        label={dashboardData.overallSentiment >= 0 ? '긍정적' : '부정적'}
                        color={dashboardData.overallSentiment >= 0 ? 'success' : 'error'}
                        size="small"
                      />
                    </Box>
                    <Assessment sx={{ fontSize: 40, color: getSentimentColor(dashboardData.overallSentiment) }} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box>
                      <Typography color="text.secondary" gutterBottom>
                        분석된 기사
                      </Typography>
                      <Typography variant="h4">
                        {dashboardData.totalArticles.toLocaleString()}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        오늘 +{dashboardData.todayArticles}
                      </Typography>
                    </Box>
                    <Business sx={{ fontSize: 40, color: 'primary.main' }} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box>
                      <Typography color="text.secondary" gutterBottom>
                        활성 스테이크홀더
                      </Typography>
                      <Typography variant="h4">
                        {dashboardData.activeStakeholders}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        8개 그룹 중
                      </Typography>
                    </Box>
                    <People sx={{ fontSize: 40, color: 'secondary.main' }} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box>
                      <Typography color="text.secondary" gutterBottom>
                        활성 알림
                      </Typography>
                      <Typography variant="h4">
                        {dashboardData.activeAlerts}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        확인 필요
                      </Typography>
                    </Box>
                    <Notifications sx={{ fontSize: 40, color: 'warning.main' }} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* 차트 섹션 */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} lg={8}>
              <Paper sx={{ p: 2, height: 400 }}>
                <Typography variant="h6" gutterBottom>
                  센티멘트 트렌드
                </Typography>
                <TrendChart data={dashboardData.trendData} />
              </Paper>
            </Grid>
            <Grid item xs={12} lg={4}>
              <Paper sx={{ p: 2, height: 400 }}>
                <Typography variant="h6" gutterBottom>
                  스테이크홀더별 분포
                </Typography>
                <StakeholderChart data={dashboardData.stakeholderData} />
              </Paper>
            </Grid>
          </Grid>

          <Grid container spacing={3}>
            <Grid item xs={12} lg={6}>
              <Paper sx={{ p: 2, height: 400 }}>
                <Typography variant="h6" gutterBottom>
                  센티멘트 분포
                </Typography>
                <SentimentChart data={dashboardData.sentimentDistribution} />
              </Paper>
            </Grid>
            <Grid item xs={12} lg={6}>
              <RecentNews companyId={selectedCompany as number} />
            </Grid>
          </Grid>

          {/* 알림 패널 */}
          <Box sx={{ mt: 3 }}>
            <AlertPanel companyId={selectedCompany as number} />
          </Box>
        </>
      )}
    </Box>
  );
};

export default Dashboard;