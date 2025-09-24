import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';

interface SentimentDistribution {
  sentiment: string;
  count: number;
  percentage: number;
}

interface SentimentChartProps {
  data: SentimentDistribution[];
}

const SentimentChart: React.FC<SentimentChartProps> = ({ data }) => {
  const SENTIMENT_COLORS = {
    'very_negative': '#d32f2f',
    'negative': '#f57c00',
    'neutral': '#616161',
    'positive': '#388e3c',
    'very_positive': '#1976d2'
  };

  const SENTIMENT_LABELS = {
    'very_negative': '매우 부정적',
    'negative': '부정적',
    'neutral': '중립',
    'positive': '긍정적',
    'very_positive': '매우 긍정적'
  };

  const getColor = (sentiment: string) => {
    return SENTIMENT_COLORS[sentiment as keyof typeof SENTIMENT_COLORS] || '#9e9e9e';
  };

  const getLabel = (sentiment: string) => {
    return SENTIMENT_LABELS[sentiment as keyof typeof SENTIMENT_LABELS] || sentiment;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-300 rounded shadow-lg">
          <p className="font-semibold">{getLabel(label)}</p>
          <p>기사 수: {data.count}개</p>
          <p>비율: {data.percentage.toFixed(1)}%</p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={data}
        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="sentiment"
          tickFormatter={getLabel}
          tick={{ fontSize: 12 }}
          angle={-45}
          textAnchor="end"
          height={80}
        />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={getColor(entry.sentiment)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};

export default SentimentChart;