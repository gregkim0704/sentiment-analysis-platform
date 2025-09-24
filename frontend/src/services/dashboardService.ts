import { api } from './api';
import { Company, StakeholderType } from '@/types';

export interface DashboardData {
  overallSentiment: number;
  totalArticles: number;
  todayArticles: number;
  activeStakeholders: number;
  activeAlerts: number;
  trendData: TrendData[];
  stakeholderData: StakeholderData[];
  sentimentDistribution: SentimentDistribution[];
}

export interface TrendData {
  date: string;
  overall: number;
  customer: number;
  investor: number;
  employee: number;
  media: number;
}

export interface StakeholderData {
  name: string;
  value: number;
  sentiment: number;
}

export interface SentimentDistribution {
  sentiment: string;
  count: number;
  percentage: number;
}

export interface NewsArticle {
  id: number;
  title: string;
  url: string;
  source: string;
  publishedAt: string;
  sentiment: string;
  sentimentScore: number;
  stakeholderType: string;
}

export interface AlertItem {
  id: number;
  title: string;
  message: string;
  severity: 'critical' | 'warning' | 'info';
  createdAt: string;
  metadata?: {
    stakeholderType?: string;
    sentimentScore?: number;
    articleCount?: number;
  };
}

export interface DashboardParams {
  companyId?: number;
  stakeholderType?: StakeholderType;
  timeRange: '7d' | '30d' | '90d';
}

class DashboardService {
  async getCompanies(): Promise<Company[]> {
    const response = await api.get('/companies');
    return response.data;
  }

  async getDashboardData(params: DashboardParams): Promise<DashboardData> {
    const response = await api.get('/dashboard', { params });
    return response.data;
  }

  async getRecentNews(companyId: number, limit: number = 10): Promise<NewsArticle[]> {
    const response = await api.get(`/companies/${companyId}/news/recent`, {
      params: { limit }
    });
    return response.data;
  }

  async getAlerts(companyId: number): Promise<AlertItem[]> {
    const response = await api.get(`/companies/${companyId}/alerts`);
    return response.data;
  }

  async dismissAlert(alertId: number): Promise<void> {
    await api.patch(`/alerts/${alertId}/dismiss`);
  }

  async getSentimentTrend(
    companyId: number,
    stakeholderType?: StakeholderType,
    timeRange: '7d' | '30d' | '90d' = '30d'
  ): Promise<TrendData[]> {
    const response = await api.get(`/companies/${companyId}/sentiment/trend`, {
      params: { stakeholderType, timeRange }
    });
    return response.data;
  }

  async getStakeholderAnalysis(
    companyId: number,
    timeRange: '7d' | '30d' | '90d' = '30d'
  ): Promise<StakeholderData[]> {
    const response = await api.get(`/companies/${companyId}/stakeholders/analysis`, {
      params: { timeRange }
    });
    return response.data;
  }

  async getSentimentDistribution(
    companyId: number,
    stakeholderType?: StakeholderType,
    timeRange: '7d' | '30d' | '90d' = '30d'
  ): Promise<SentimentDistribution[]> {
    const response = await api.get(`/companies/${companyId}/sentiment/distribution`, {
      params: { stakeholderType, timeRange }
    });
    return response.data;
  }
}

export const dashboardService = new DashboardService();