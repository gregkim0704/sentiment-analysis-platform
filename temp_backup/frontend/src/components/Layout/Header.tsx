import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Menu as MenuIcon,
  AccountCircle,
  Settings,
  Logout,
  Notifications,
  Badge,
} from '@mui/icons-material';

import { useAuth } from '../../contexts/AuthContext';

interface HeaderProps {
  drawerWidth: number;
  isDrawerOpen: boolean;
  onDrawerToggle: () => void;
}

const Header: React.FC<HeaderProps> = ({
  drawerWidth,
  isDrawerOpen,
  onDrawerToggle,
}) => {
  const { user, logout } = useAuth();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    handleMenuClose();
    await logout();
  };

  const getRoleDisplayName = (role: string) => {
    const roleNames = {
      admin: '관리자',
      analyst: '분석가',
      viewer: '뷰어',
    };
    return roleNames[role as keyof typeof roleNames] || role;
  };

  return (
    <AppBar
      position="fixed"
      sx={{
        width: { md: `calc(100% - ${isDrawerOpen ? drawerWidth : 0}px)` },
        ml: { md: `${isDrawerOpen ? drawerWidth : 0}px` },
        transition: (theme) =>
          theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
          }),
      }}
    >
      <Toolbar>
        {/* 메뉴 버튼 */}
        <IconButton
          color="inherit"
          aria-label="메뉴 열기"
          edge="start"
          onClick={onDrawerToggle}
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>

        {/* 제목 */}
        <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
          센티멘트 분석 플랫폼
        </Typography>

        {/* 알림 버튼 */}
        <IconButton color="inherit" sx={{ mr: 1 }}>
          <Badge badgeContent={0} color="error">
            <Notifications />
          </Badge>
        </IconButton>

        {/* 사용자 메뉴 */}
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <IconButton
            size="large"
            aria-label="사용자 메뉴"
            aria-controls="user-menu"
            aria-haspopup="true"
            onClick={handleMenuOpen}
            color="inherit"
          >
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}>
              {user?.full_name?.charAt(0) || 'U'}
            </Avatar>
          </IconButton>

          <Menu
            id="user-menu"
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            onClick={handleMenuClose}
            PaperProps={{
              elevation: 0,
              sx: {
                overflow: 'visible',
                filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
                mt: 1.5,
                minWidth: 200,
                '& .MuiAvatar-root': {
                  width: 32,
                  height: 32,
                  ml: -0.5,
                  mr: 1,
                },
                '&:before': {
                  content: '""',
                  display: 'block',
                  position: 'absolute',
                  top: 0,
                  right: 14,
                  width: 10,
                  height: 10,
                  bgcolor: 'background.paper',
                  transform: 'translateY(-50%) rotate(45deg)',
                  zIndex: 0,
                },
              },
            }}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            {/* 사용자 정보 */}
            <Box sx={{ px: 2, py: 1 }}>
              <Typography variant="subtitle2" noWrap>
                {user?.full_name}
              </Typography>
              <Typography variant="body2" color="text.secondary" noWrap>
                {user?.email}
              </Typography>
              <Typography variant="caption" color="primary">
                {getRoleDisplayName(user?.role || '')}
              </Typography>
            </Box>

            <Divider />

            {/* 메뉴 항목들 */}
            <MenuItem onClick={handleMenuClose}>
              <ListItemIcon>
                <AccountCircle fontSize="small" />
              </ListItemIcon>
              <ListItemText>내 프로필</ListItemText>
            </MenuItem>

            <MenuItem onClick={handleMenuClose}>
              <ListItemIcon>
                <Settings fontSize="small" />
              </ListItemIcon>
              <ListItemText>설정</ListItemText>
            </MenuItem>

            <Divider />

            <MenuItem onClick={handleLogout}>
              <ListItemIcon>
                <Logout fontSize="small" />
              </ListItemIcon>
              <ListItemText>로그아웃</ListItemText>
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;