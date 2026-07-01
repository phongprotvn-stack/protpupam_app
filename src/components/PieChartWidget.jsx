import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

const COLORS = ['#E6002D', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316']

const RADIAN = Math.PI / 180
function renderLabel({ cx, cy, midAngle, innerRadius, outerRadius, percent }) {
  if (percent < 0.05) return null
  const radius = outerRadius + 20
  const x = cx + radius * Math.cos(-midAngle * RADIAN)
  const y = cy + radius * Math.sin(-midAngle * RADIAN)
  return (
    <text x={x} y={y} fill="#6B7280" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" fontSize={11}>
      {(percent * 100).toFixed(0)}%
    </text>
  )
}

export default function PieChartWidget({ data, title, emptyMessage }) {
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
      <div className="flex flex-col items-center">
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={80}
              dataKey="value"
              labelLine
              label={renderLabel}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value, name) => [`${value} video`, name]}
              contentStyle={{ borderRadius: 16, border: 'none', boxShadow: '0 8px 24px rgba(0,0,0,0.1)' }}
            />
          </PieChart>
        </ResponsiveContainer>

        {/* Legend */}
        <div className="flex flex-wrap gap-x-4 gap-y-1.5 mt-2 justify-center">
          {data.map((d, i) => (
            <div key={d.name} className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
              <span className="text-[11px] text-[#6B7280] capitalize">{d.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
