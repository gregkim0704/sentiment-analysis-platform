import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

interface TrendData {
  date: string;
  overall: number;
  customer: number;
  investor: number;
  employee: number;
  media: number;
}

interface TrendChartProps {
  data: TrendData[];
}

const TrendChart: React.FC<TrendChartProps> = ({ data }) => {
  const formatDate = (dateStr: string) => {
    return format(new Date(dateStr), 'MM/dd', { locale: ko });
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-300 rounded shadow-lg">
          <p className="font-semibold">{format(new Date(label), 'yyyy년 MM월 dd일', { locale: ko })}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {entry.value.toFixed(2)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="date" 
          tickFormatter={formatDate}
          tick={{ fontSize: 12 }}
        />
        <YAxis 
          domain={[-2, 2]}
          tick={{ fontSize: 12 }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Line
          type="monotone"
          dataKey="overall"
          stroke="#2196f3"
          strokeWidth={3}
          name="전체"
          dot={{ r: 4 }}
        />
        <Line
          type="monotone"
          dataKey="customer"
          stroke="#4caf50"
          strokeWidth={2}
          name="고객"
          dot={{ r: 3 }}
        />
        <Line
          type="monotone"
          dataKey="investor"
          stroke="#ff9800"
          strokeWidth={2}
          name="투자자"
          dot={{ r: 3 }}
        />
        <Line
          type="monotone"
          dataKey="employee"
          stroke="#9c27b0"
          strokeWidth={2}
          name="직원"
          dot={{ r: 3 }}
        />
        <Line
          type="monotone"
          dataKey="media"
          stroke="#f44336"
          strokeWidth={2}
          name="언론"
          dot={{ r: 3 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default TrendChart;