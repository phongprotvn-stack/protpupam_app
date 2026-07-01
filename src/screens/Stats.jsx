import { useApp } from '../contexts/AppContext'
import PieChartWidget from '../components/PieChartWidget'
import BarChartWidget from '../components/BarChartWidget'
import { BarChart3 } from 'lucide-react'

export default function Stats() {
  const { stats, loading } = useApp()

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 animate-fade-in">
        <div className="w-10 h-10 border-3 border-[#E6002D] border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-[14px] text-[#6B7280]">Đang tải...</p>
      </div>
    )
  }

  if (stats.total === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-32 animate-fade-in">
        <BarChart3 size={48} className="text-[#D1D5DB] mb-4" />
        <p className="text-[15px] font-semibold text-[#101010] mb-1">Chưa có thống kê</p>
        <p className="text-[13px] text-[#6B7280]">Cần phân tích video trước đã</p>
      </div>
    )
  }

  return (
    <div className="space-y-4 animate-fade-in">
      <h1 className="text-[20px] font-bold text-[#101010]">📊 Thống kê chi tiết</h1>

      {/* Overview numbers */}
      <div className="card">
        <h3 className="section-title">Tổng quan tương tác</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            <p className="text-[28px] font-bold text-[#E6002D]">{stats.total}</p>
            <p className="text-[12px] text-[#6B7280]">Tổng video</p>
          </div>
          <div className="text-center">
            <p className="text-[28px] font-bold text-[#3B82F6]">{stats.avgLikes?.toLocaleString('vi-VN')}</p>
            <p className="text-[12px] text-[#6B7280]">Like trung bình</p>
          </div>
          <div className="text-center">
            <p className="text-[28px] font-bold text-[#10B981]">{stats.avgViews?.toLocaleString('vi-VN')}</p>
            <p className="text-[12px] text-[#6B7280]">View trung bình</p>
          </div>
          <div className="text-center">
            <p className="text-[28px] font-bold text-[#F59E0B]">
              {stats.avgViews > 0 ? ((stats.avgLikes / stats.avgViews) * 100).toFixed(1) : 0}%
            </p>
            <p className="text-[12px] text-[#6B7280]">Tỷ lệ tương tác</p>
          </div>
        </div>
      </div>

      {/* Appearance */}
      <PieChartWidget
        data={stats.shirtColors}
        title="👕 Màu áo"
        emptyMessage="Chưa phân tích"
      />
      <BarChartWidget
        data={stats.hairStyles}
        title="💇 Kiểu tóc"
        emptyMessage="Chưa phân tích"
      />

      {/* Scene & Mood */}
      <PieChartWidget
        data={stats.scenes}
        title="📍 Bối cảnh (trong nhà / ngoài trời)"
        emptyMessage="Chưa phân tích"
      />
      <PieChartWidget
        data={stats.musicMoods}
        title="🎵 Tâm trạng nhạc nền"
        emptyMessage="Chưa phân tích"
      />

      {/* Emotions */}
      <PieChartWidget
        data={stats.emotions}
        title="😊 Cảm xúc"
        emptyMessage="Chưa phân tích"
      />
    </div>
  )
}
