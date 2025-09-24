import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend
} from 'recharts';

interface StakeholderData {
  name: string;
  value: number;
  sentiment: number;
}

interface StakeholderChartProps {
  data: StakeholderData[];
}

const StakeholderChart: React.FC<StakeholderChartProps> = ({ data }) => {
  const COLORS = {
    customer: '#4caf50',
    investor: '#ff9800',
    employee: '#9c27b0',
    government: '#2196f3',
    media: '#f44336',
    partner: '#00bcd4',
    competitor: '#795548',
    community: '#607d8b'
  };

  const getColor = (name: string) => {
    const key = name.toLowerCase() as keyof typeof COLORS;
    return COLORS[key] || '#9e9e9e';
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-300 rounded shadow-lg">
          <p className="font-semibold">{data.name}</p>
          <p>기사 수: {data.value}개</p>
          <p>평균 센티멘트: {data.sentiment.toFixed(2)}</p>
        </div>
      );
    }
    return null;
  };

  const CustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
    if (percent < 0.05) return null; // 5% 미만은 라벨 숨김
    
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        fontSize={12}
        fontWeight="bold"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={CustomLabel}
          outerRadius={120}
          fill="#8884d8"
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={getColor(entry.name)} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend 
          verticalAlign="bottom" 
          height={36}
          formatter={(value, entry) => (
            <span style={{ color: entry.color }}>
              {value} ({entry.payload?.sentiment?.toFixed(2) || 0})
            </span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
};

export default StakeholderChart;