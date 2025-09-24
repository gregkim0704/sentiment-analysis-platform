import React, { useState, ReactNode } from 'react';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Menu as MenuIcon,
  ChevronLeft as ChevronLeftIcon,
} from '@mui/icons-material';

import Sidebar from './Sidebar';
import Header from './Header';

interface LayoutProps {
  children: ReactNode;
}

const DRAWER_WIDTH = 280;

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const [desktopOpen, setDesktopOpen] = useState(true);

  const handleDrawerToggle = () => {
    if (isMobile) {
      setMobileOpen(!mobileOpen);
    } else {
      setDesktopOpen(!desktopOpen);
    }
  };

  const handleMobileDrawerClose = () => {
    setMobileOpen(false);
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* 헤더 */}
      <Header 
        drawerWidth={DRAWER_WIDTH}
        isDrawerOpen={isMobile ? mobileOpen : desktopOpen}
        onDrawerToggle={handleDrawerToggle}
      />

      {/* 사이드바 - 모바일 */}
      {isMobile && (
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleMobileDrawerClose}
          ModalProps={{
            keepMounted: true, // 모바일 성능 향상
          }}
          sx={{
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: DRAWER_WIDTH,
            },
          }}
        >
          <Sidebar onItemClick={handleMobileDrawerClose} />
        </Drawer>
      )}

      {/* 사이드바 - 데스크톱 */}
      {!isMobile && (
        <Drawer
          variant="persistent"
          open={desktopOpen}
          sx={{
            width: desktopOpen ? DRAWER_WIDTH : 0,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: DRAWER_WIDTH,
              boxSizing: 'border-box',
              transition: theme.transitions.create('width', {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.enteringScreen,
              }),
            },
          }}
        >
          <Sidebar />
        </Drawer>
      )}

      {/* 메인 콘텐츠 */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: {
            md: `calc(100% - ${desktopOpen ? DRAWER_WIDTH : 0}px)`,
          },
          transition: theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
          }),
        }}
      >
        {/* 헤더 높이만큼 여백 */}
        <Toolbar />
        
        {/* 페이지 콘텐츠 */}
        <Box
          sx={{
            p: 3,
            minHeight: 'calc(100vh - 64px)',
            backgroundColor: theme.palette.background.default,
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;