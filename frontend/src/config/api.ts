// API 설정
export const API_CONFIG = {
  // 환경 변수에서 API URL을 가져오거나 기본값 사용
  BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  
  // API 엔드포인트들
  ENDPOINTS: {
    // 인증
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    
    // 센티멘트 분석
    SENTIMENT: '/api/sentiment',
    SENTIMENT_BATCH: '/api/sentiment/batch',
    
    // 스테이크홀더
    STAKEHOLDERS: '/api/stakeholders',
    
    // 크롤링
    CRAWL: '/api/crawl',
    
    // 대시보드
    DASHBOARD: '/api/dashboard',
  },
  
  // 요청 설정
  TIMEOUT: 30000, // 30초
  
  // 헤더 설정
  HEADERS: {
    'Content-Type': 'application/json',
  },
};

// API URL 생성 헬퍼 함수
export const createApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};

// 환경별 설정
export const isDevelopment = process.env.NODE_ENV === 'development';
export const isProduction = process.env.NODE_ENV === 'production';

console.log('API Base URL:', API_CONFIG.BASE_URL);
console.log('Environment:', process.env.NODE_ENV);