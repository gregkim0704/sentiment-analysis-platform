import { api, setToken, removeToken } from './api';
import { LoginRequest, LoginResponse, User } from '../types';

export const authService = {
  // 로그인
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await api.post<LoginResponse>('/auth/login', credentials);
    
    // 토큰 저장
    setToken(response.access_token);
    localStorage.setItem('refresh_token', response.refresh_token);
    localStorage.setItem('user', JSON.stringify(response.user));
    
    return response;
  },

  // 로그아웃
  logout: async (): Promise<void> => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      // 로그아웃 API 실패해도 로컬 토큰은 제거
      console.warn('로그아웃 API 호출 실패:', error);
    } finally {
      removeToken();
      localStorage.removeItem('user');
    }
  },

  // 현재 사용자 정보 조회
  getCurrentUser: async (): Promise<User> => {
    return await api.get<User>('/auth/me');
  },

  // 회원가입
  register: async (userData: {
    email: string;
    password: string;
    full_name: string;
  }): Promise<{ user: User; message: string }> => {
    return await api.post('/auth/register', userData);
  },

  // 비밀번호 변경
  changePassword: async (passwordData: {
    current_password: string;
    new_password: string;
  }): Promise<{ message: string }> => {
    return await api.post('/auth/change-password', passwordData);
  },

  // 토큰 갱신
  refreshToken: async (refreshToken: string): Promise<{
    access_token: string;
    token_type: string;
    expires_in: number;
  }> => {
    return await api.post('/auth/refresh', { refresh_token: refreshToken });
  },

  // 토큰 유효성 검증
  validateToken: async (token: string): Promise<{
    valid: boolean;
    user?: User;
    expires_at?: number;
  }> => {
    return await api.post('/auth/validate-token', { token });
  },

  // 로컬 스토리지에서 사용자 정보 가져오기
  getStoredUser: (): User | null => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch (error) {
        console.error('사용자 정보 파싱 오류:', error);
        return null;
      }
    }
    return null;
  },

  // 로그인 상태 확인
  isAuthenticated: (): boolean => {
    const token = localStorage.getItem('access_token');
    const user = authService.getStoredUser();
    return !!(token && user);
  },

  // 권한 확인
  hasRole: (requiredRole: 'admin' | 'analyst' | 'viewer'): boolean => {
    const user = authService.getStoredUser();
    if (!user) return false;

    const roleHierarchy = {
      admin: 3,
      analyst: 2,
      viewer: 1,
    };

    return roleHierarchy[user.role] >= roleHierarchy[requiredRole];
  },
};

export default authService;