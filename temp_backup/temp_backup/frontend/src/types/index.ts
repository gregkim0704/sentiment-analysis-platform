// 기본 응답 타입
export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
  error?: string;
}

// 페이지네이션 타입
export interface Pagination {
  page: number;
  size: number;
  total?: number;
  pages?: number;
}

// 사용자 관련 타입
export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'admin' | 'analyst' | 'viewer';
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  last_login?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// 회사 관련 타입
export interface Company {
  id: number;
  name: string;
  stock_code?: string;
  industry: string;
  description?: string;
  website_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

// 센티멘트 관련 타입
export type SentimentScore = 'very_negative' | 'negative' | 'neutral' | 'positive' | 'very_positive';

export type StakeholderType = 
  | 'customer' 
  | 'investor' 
  | 'employee' 
  | 'government' 
  | 'media' 
  | 'partner' 
  | 'competitor' 
  | 'community';

export type NewsSource = 'naver' | 'daum' | 'google' | 'company_website' | 'social_media' | 'press_release';

// 뉴스 기사 타입
export interface NewsArticle {
  id: number;
  company_id: number;
  title: string;
  content: string;
  url: string;
  source: NewsSource;
  author?: string;
  published_date: string;
  collected_date: string;
  sentiment_score?: SentimentScore;
  sentiment_confidence?: number;
  stakeholder_type?: StakeholderType;
  keywords?: string[];
  summary?: string;
}

// 센티멘트 트렌드 타입
export interface SentimentTrend {
  date: string;
  company_id: number;
  company_name: string;
  stakeholder_type: StakeholderType;
  total_articles: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  avg_sentiment_score: number;
  sentiment_volatility: number;
  top_keywords: string[];
}

// 스테이크홀더 인사이트 타입
export interface StakeholderInsight {
  stakeholder_type: StakeholderType;
  sentiment_score: SentimentScore;
  confidence: number;
  impact_level: 'very_low' | 'low' | 'medium' | 'high' | 'very_high';
  urgency_level: 'low' | 'medium' | 'high' | 'critical';
  key_concerns: string[];
  positive_factors: string[];
  negative_factors: string[];
  action_items: string[];
  analysis_date: string;
  article_count: number;
  keywords: string[];
  reasoning?: string;
}

// 스테이크홀더 비교 분석 타입
export interface StakeholderComparison {
  most_positive: [string, number] | null;
  most_negative: [string, number] | null;
  highest_impact: [string, string] | null;
  most_urgent: [string, string] | null;
  most_active: [string, number] | null;
  summary: {
    total_stakeholders: number;
    avg_sentiment: number;
    total_articles: number;
    stakeholders_with_data: number;
  };
}

// 대시보드 데이터 타입
export interface DashboardData {
  company_overview: {
    total_companies: number;
    active_companies: number;
    total_articles: number;
    analyzed_articles: number;
  };
  recent_trends: SentimentTrend[];
  stakeholder_summary: Record<StakeholderType, {
    article_count: number;
    avg_sentiment: number;
    has_analyzer: boolean;
  }>;
  urgent_insights: StakeholderInsight[];
}

// 크롤링 작업 타입
export interface CrawlingJob {
  task_id: string;
  status: 'pending' | 'progress' | 'success' | 'failure';
  message: string;
  meta?: any;
  result?: any;
  error?: string;
}

// 분석 통계 타입
export interface AnalysisStatistics {
  period_days: number;
  total_articles: number;
  analyzed_articles: number;
  recent_analyzed: number;
  completion_rate: number;
  sentiment_distribution: Record<SentimentScore, number>;
  stakeholder_distribution: Record<StakeholderType, number>;
  analyzer_info: {
    model_name: string;
    is_loaded: boolean;
    confidence_threshold: number;
    supported_languages: string[];
    model_type: string;
  };
}

// 차트 데이터 타입
export interface ChartDataPoint {
  date: string;
  value: number;
  label?: string;
  color?: string;
}

export interface SentimentChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
  }[];
}

// 필터 옵션 타입
export interface FilterOptions {
  company_id?: number;
  stakeholder_type?: StakeholderType;
  sentiment_score?: SentimentScore;
  date_from?: string;
  date_to?: string;
  days?: number;
}

// 에러 타입
export interface ApiError {
  code: number;
  message: string;
  details?: any;
  timestamp: string;
  request_id?: string;
}