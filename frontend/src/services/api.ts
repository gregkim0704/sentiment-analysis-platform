import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import { ApiResponse, ApiError } from '../types';

// API 기본 설정
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api/v1';

// Axios 인스턴스 생성
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 토큰 관리
const getToken = (): string | null => {
  return localStorage.getItem('access_token');
};

const setToken = (token: string): void => {
  localStorage.setItem('access_token', token);
};

const removeToken = (): void => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

// 요청 인터셉터 (토큰 자동 추가)
apiClient.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터 (에러 처리)
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    // 401 에러 (토큰 만료) 처리
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token } = response.data;
          setToken(access_token);

          // 원래 요청 재시도
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // 리프레시 토큰도 만료된 경우 로그아웃
        removeToken();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// API 응답 래퍼 함수
const handleApiResponse = <T>(response: AxiosResponse<ApiResponse<T>>): T => {
  if (response.data.success) {
    return response.data.data as T;
  } else {
    throw new Error(response.data.message || '알 수 없는 오류가 발생했습니다.');
  }
};

// API 에러 처리 함수
const handleApiError = (error: AxiosError): never => {
  if (error.response?.data) {
    const apiError = error.response.data as ApiError;
    throw new Error(apiError.message || '서버 오류가 발생했습니다.');
  } else if (error.request) {
    throw new Error('네트워크 연결을 확인해주세요.');
  } else {
    throw new Error('요청 처리 중 오류가 발생했습니다.');
  }
};

// 기본 API 함수들
export const api = {
  // GET 요청
  get: async <T>(url: string, params?: any): Promise<T> => {
    try {
      const response = await apiClient.get<ApiResponse<T>>(url, { params });
      return handleApiResponse(response);
    } catch (error) {
      return handleApiError(error as AxiosError);
    }
  },

  // POST 요청
  post: async <T>(url: string, data?: any): Promise<T> => {
    try {
      const response = await apiClient.post<ApiResponse<T>>(url, data);
      return handleApiResponse(response);
    } catch (error) {
      return handleApiError(error as AxiosError);
    }
  },

  // PUT 요청
  put: async <T>(url: string, data?: any): Promise<T> => {
    try {
      const response = await apiClient.put<ApiResponse<T>>(url, data);
      return handleApiResponse(response);
    } catch (error) {
      return handleApiError(error as AxiosError);
    }
  },

  // DELETE 요청
  delete: async <T>(url: string): Promise<T> => {
    try {
      const response = await apiClient.delete<ApiResponse<T>>(url);
      return handleApiResponse(response);
    } catch (error) {
      return handleApiError(error as AxiosError);
    }
  },
};

// 토큰 관리 함수들 내보내기
export { getToken, setToken, removeToken };

export default apiClient;