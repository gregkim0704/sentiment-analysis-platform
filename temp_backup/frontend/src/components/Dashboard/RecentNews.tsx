import React from 'react';
import {
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
  Box,
  Link,
  CircularProgress,
  Divider
} from '@mui/material';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import { useQuery } from 'react-query';
import { dashboardService } from '@/services/dashboardService';

interface RecentNewsProps {
  companyId: number;
}

const RecentNews: React.FC<RecentNewsProps> = ({ companyId }) => {
  const { data: news = [], isLoading } = useQuery(
    ['recentNews', companyId],
    () => dashboardService.getRecentNews(companyId),
    {
      enabled: !!companyId,
      refetchInterval: 60000 // 1분마다 새로고침
    }
  );

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'very_positive': return 'success';
      case 'positive': return 'success';
      case 'neutral': return 'default';
      case 'negative': return 'warning';
      case 'very_negative': return 'error';
      default: return 'default';
    }
  };

  const getSentimentLabel = (sentiment: string) => {
    switch (sentiment) {
      case 'very_positive': return '매우 긍정적';
      case 'positive': return '긍정적';
      case 'neutral': return '중립';
      case 'negative': return '부정적';
      case 'very_negative': return '매우 부정적';
      default: return '알 수 없음';
    }
  };

  const getStakeholderLabel = (stakeholder: string) => {
    switch (stakeholder) {
      case 'customer': return '고객';
      case 'investor': return '투자자';
      case 'employee': return '직원';
      case 'government': return '정부';
      case 'media': return '언론';
      case 'partner': return '파트너';
      case 'competitor': return '경쟁사';
      case 'community': return '지역사회';
      default: return stakeholder;
    }
  };

  if (isLoading) {
    return (
      <Paper sx={{ p: 2, height: 400 }}>
        <Typography variant="h6" gutterBottom>
          최근 뉴스
        </Typography>
        <Box display="flex" justifyContent="center" alignItems="center" height="300px">
          <CircularProgress />
        </Box>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 2, height: 400, overflow: 'hidden' }}>
      <Typography variant="h6" gutterBottom>
        최근 뉴스 ({news.length}개)
      </Typography>
      
      <Box sx={{ height: 340, overflow: 'auto' }}>
        <List dense>
          {news.map((article, index) => (
            <React.Fragment key={article.id}>
              <ListItem alignItems="flex-start" sx={{ px: 0 }}>
                <ListItemText
                  primary={
                    <Link
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      sx={{
                        textDecoration: 'none',
                        color: 'text.primary',
                        '&:hover': {
                          textDecoration: 'underline'
                        }
                      }}
                    >
                      <Typography variant="body2" sx={{ fontWeight: 500, lineHeight: 1.3 }}>
                        {article.title}
                      </Typography>
                    </Link>
                  }
                  secondary={
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" color="text.secondary" display="block">
                        {article.source} • {format(new Date(article.publishedAt), 'MM/dd HH:mm', { locale: ko })}
                      </Typography>
                      <Box sx={{ mt: 0.5, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                        <Chip
                          label={getSentimentLabel(article.sentiment)}
                          color={getSentimentColor(article.sentiment) as any}
                          size="small"
                          variant="outlined"
                        />
                        <Chip
                          label={getStakeholderLabel(article.stakeholderType)}
                          size="small"
                          variant="outlined"
                        />
                        <Chip
                          label={`${article.sentimentScore.toFixed(2)}`}
                          size="small"
                          variant="filled"
                          sx={{
                            backgroundColor: article.sentimentScore >= 0 ? '#e8f5e8' : '#ffebee',
                            color: article.sentimentScore >= 0 ? '#2e7d32' : '#c62828'
                          }}
                        />
                      </Box>
                    </Box>
                  }
                />
              </ListItem>
              {index < news.length - 1 && <Divider />}
            </React.Fragment>
          ))}
          
          {news.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography color="text.secondary">
                최근 뉴스가 없습니다.
              </Typography>
            </Box>
          )}
        </List>
      </Box>
    </Paper>
  );
};

export default RecentNews;