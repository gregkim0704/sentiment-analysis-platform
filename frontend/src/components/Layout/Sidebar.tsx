import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Divider,
  Chip,
} from '@mui/material';
import {
  Dashboard,
  Business,
  TrendingUp,
  People,
  CloudDownload,
  Analytics,
  Person,
  Settings,
  Assessment,
} from '@mui/icons-material';

import { useAuth } from '../../contexts/AuthContext';
import authService from '../../services/authService';

interface SidebarProps {
  onItemClick?: () => void;
}

interface MenuItem {
  text: string;
  icon: React.ReactElement;
  path: string;
  requiredRole?: 'admin' | 'analyst' | 'viewer';
  badge?: string;
}

const menuItems: MenuItem[] = [
  {
    text: '대시보드',
    icon: <Dashboard />,
    path: '/dashboard',
  },
  {
    text: '회사 관리',
    icon: <Business />,
    path: '/companies',
  },
  {
    text: '센티멘트 분석',
    icon: <TrendingUp />,
    path: '/sentiment',
  },
  {
    text: '스테이크홀더',
    icon: <People />,
    path: '/stakeholders',
  },
  {
    text: '크롤링 관리',
    icon: <CloudDownload />,
    path: '/crawling',
    requiredRole: 'analyst',
    badge: 'NEW',
  },
  {
    text: '분석 관리',
    icon: <Analytics />,
    path: '/analysis',
    requiredRole: 'analyst',
  },
  {
    text: '사용자 관리',
    icon: <Person />,
    path: '/users',
    requiredRole: 'admin',
  },
];

const Sidebar: React.FC<SidebarProps> = ({ onItemClick }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();

  const handleItemClick = (path: string) => {
    navigate(path);
    onItemClick?.();
  };

  const isSelected = (path: string) => {
    return location.pathname === path;
  };

  const canAccess = (requiredRole?: string) => {
    if (!requiredRole) return true;
    return authService.hasRole(requiredRole as 'admin' | 'analyst' | 'viewer');
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 로고 영역 */}
      <Toolbar
        sx={{
          px: 3,
          py: 2,
          backgroundColor: 'primary.main',
          color: 'primary.contrastText',
        }}
      >
        <Assessment sx={{ mr: 2 }} />
        <Typography variant="h6" noWrap component="div">
          센티멘트 분석
        </Typography>
      </Toolbar>

      <Divider />

      {/* 사용자 정보 */}
      <Box sx={{ p: 2, backgroundColor: 'grey.50' }}>
        <Typography variant="body2" color="text.secondary">
          안녕하세요,
        </Typography>
        <Typography variant="subtitle2" fontWeight="bold">
          {user?.full_name}
        </Typography>
        <Chip
          label={
            user?.role === 'admin' ? '관리자' :
            user?.role === 'analyst' ? '분석가' : '뷰어'
          }
          size="small"
          color={
            user?.role === 'admin' ? 'error' :
            user?.role === 'analyst' ? 'primary' : 'default'
          }
          sx={{ mt: 1 }}
        />
      </Box>

      <Divider />

      {/* 메뉴 목록 */}
      <List sx={{ flexGrow: 1, py: 1 }}>
        {menuItems.map((item) => {
          if (!canAccess(item.requiredRole)) {
            return null;
          }

          return (
            <ListItem key={item.path} disablePadding>
              <ListItemButton
                selected={isSelected(item.path)}
                onClick={() => handleItemClick(item.path)}
                sx={{
                  mx: 1,
                  borderRadius: 1,
                  '&.Mui-selected': {
                    backgroundColor: 'primary.main',
                    color: 'primary.contrastText',
                    '&:hover': {
                      backgroundColor: 'primary.dark',
                    },
                    '& .MuiListItemIcon-root': {
                      color: 'primary.contrastText',
                    },
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 40,
                    color: isSelected(item.path) ? 'inherit' : 'text.secondary',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.text}
                  primaryTypographyProps={{
                    fontSize: '0.9rem',
                    fontWeight: isSelected(item.path) ? 600 : 400,
                  }}
                />
                {item.badge && (
                  <Chip
                    label={item.badge}
                    size="small"
                    color="secondary"
                    sx={{ ml: 1, height: 20, fontSize: '0.7rem' }}
                  />
                )}
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      <Divider />

      {/* 설정 메뉴 */}
      <List>
        <ListItem disablePadding>
          <ListItemButton
            selected={isSelected('/settings')}
            onClick={() => handleItemClick('/settings')}
            sx={{
              mx: 1,
              borderRadius: 1,
              '&.Mui-selected': {
                backgroundColor: 'primary.main',
                color: 'primary.contrastText',
                '& .MuiListItemIcon-root': {
                  color: 'primary.contrastText',
                },
              },
            }}
          >
            <ListItemIcon
              sx={{
                minWidth: 40,
                color: isSelected('/settings') ? 'inherit' : 'text.secondary',
              }}
            >
              <Settings />
            </ListItemIcon>
            <ListItemText 
              primary="설정"
              primaryTypographyProps={{
                fontSize: '0.9rem',
                fontWeight: isSelected('/settings') ? 600 : 400,
              }}
            />
          </ListItemButton>
        </ListItem>
      </List>

      {/* 버전 정보 */}
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography variant="caption" color="text.secondary">
          v1.0.0
        </Typography>
      </Box>
    </Box>
  );
};

export default Sidebar;