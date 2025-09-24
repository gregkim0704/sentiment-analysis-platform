import React from 'react';
import {
  Paper,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Box,
  Button,
  CircularProgress,
  Alert,
  IconButton
} from '@mui/material';
import {
  Warning,
  Error,
  Info,
  CheckCircle,
  Close,
  Refresh
} from '@mui/icons-material';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { dashboardService } from '@/services/dashboardService';

interface AlertPanelProps {
  companyId: number;
}

const AlertPanel: React.FC<AlertPanelProps> = ({ companyId }) => {
  const queryClient = useQueryClient();

  const { data: alerts = [], isLoading, refetch } = useQuery(
    ['alerts', companyId],
    () => dashboardService.getAlerts(companyId),
    {
      enabled: !!companyId,
      refetchInterval: 30000 // 30초마다 새로고침
    }
  );

  const dismissAlertMutation = useMutation(
    (alertId: number) => dashboardService.dismissAlert(alertId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['alerts', companyId]);
      }
    }
  );

  const getAlertIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <Error color="error" />;
      case 'warning': return <Warning color="warning" />;
      case 'info': return <Info color="info" />;
      default: return <Info />;
    }
  };

  const getAlertColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'warning': return 'warning';
      case 'info': return 'info';
      default: return 'default';
    }
  };

  const getSeverityLabel = (severity: string) => {
    switch (severity) {
      case 'critical': return '긴급';
      case 'warning': return '경고';
      case 'info': return '정보';
      default: return severity;
    }
  };

  const handleDismiss = (alertId: number) => {
    dismissAlertMutation.mutate(alertId);
  };

  if (isLoading) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          알림
        </Typography>
        <Box display="flex" justifyContent="center" alignItems="center" height="200px">
          <CircularProgress />
        </Box>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h6">
          알림 ({alerts.length}개)
        </Typography>
        <Button
          startIcon={<Refresh />}
          onClick={() => refetch()}
          size="small"
        >
          새로고침
        </Button>
      </Box>

      {alerts.length === 0 ? (
        <Alert severity="success" icon={<CheckCircle />}>
          현재 활성화된 알림이 없습니다.
        </Alert>
      ) : (
        <List>
          {alerts.map((alert) => (
            <ListItem
              key={alert.id}
              sx={{
                border: 1,
                borderColor: `${getAlertColor(alert.severity)}.main`,
                borderRadius: 1,
                mb: 1,
                backgroundColor: `${getAlertColor(alert.severity)}.light`,
                '&:last-child': { mb: 0 }
              }}
            >
              <ListItemIcon>
                {getAlertIcon(alert.severity)}
              </ListItemIcon>
              <ListItemText
                primary={
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="body1" sx={{ fontWeight: 500 }}>
                      {alert.title}
                    </Typography>
                    <Chip
                      label={getSeverityLabel(alert.severity)}
                      color={getAlertColor(alert.severity) as any}
                      size="small"
                    />
                  </Box>
                }
                secondary={
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      {alert.message}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                      {format(new Date(alert.createdAt), 'yyyy/MM/dd HH:mm', { locale: ko })}
                    </Typography>
                    {alert.metadata && (
                      <Box sx={{ mt: 1 }}>
                        {alert.metadata.stakeholderType && (
                          <Chip
                            label={`스테이크홀더: ${alert.metadata.stakeholderType}`}
                            size="small"
                            variant="outlined"
                            sx={{ mr: 0.5 }}
                          />
                        )}
                        {alert.metadata.sentimentScore && (
                          <Chip
                            label={`센티멘트: ${alert.metadata.sentimentScore.toFixed(2)}`}
                            size="small"
                            variant="outlined"
                            sx={{ mr: 0.5 }}
                          />
                        )}
                        {alert.metadata.articleCount && (
                          <Chip
                            label={`기사 수: ${alert.metadata.articleCount}`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    )}
                  </Box>
                }
              />
              <IconButton
                edge="end"
                onClick={() => handleDismiss(alert.id)}
                disabled={dismissAlertMutation.isLoading}
                size="small"
              >
                <Close />
              </IconButton>
            </ListItem>
          ))}
        </List>
      )}
    </Paper>
  );
};

export default AlertPanel;