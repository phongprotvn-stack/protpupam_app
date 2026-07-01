import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell } from 'recharts'

const COLORS = ['#E6002D', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316']

export default function BarChartWidget({ data, title, emptyMessage, dataKey = 'value' }) {
  if (!data || data.length === 0) {
    return (
      <div className="card">
        <h3 className="section-title">{title}</h3>
        <p className="text-[13px] text-[#9CA3AF] text-center py-8">{emptyMessage || 'Chưa có dữ liệu'}</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h3 className="section-title">{title}</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 5, right: 5, left: -10, bottom: 5 }}>
          <XAxis
            dataKey="name"
            tick={{ fontSize: 10, fill: '#6B7280' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 10, fill: '#9CA3AF' }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <Tooltip
            formatter={(value) => [`${value} video`, 'Số lượng']}
            contentStyle={{ borderRadius: 16, border: 'none', boxShadow: '0 8px 24px rgba(0,0,0,0.1)' }}
          />
          <Bar dataKey={dataKey} radius={[8, 8, 0, 0]} maxBarSize={36}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
