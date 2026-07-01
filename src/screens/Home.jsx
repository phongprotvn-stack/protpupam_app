import { Eye, ThumbsUp, Video as VideoIcon, Music, BrainCircuit } from 'lucide-react'
import { useApp } from '../contexts/AppContext'
import StatCard from '../components/StatCard'
import PieChartWidget from '../components/PieChartWidget'
import BarChartWidget from '../components/BarChartWidget'

export default function Home() {
  const { stats, loading, error } = useApp()

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 animate-fade-in">
        <div className="w-10 h-10 border-3 border-[#E6002D] border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-[14px] text-[#6B7280]">Đang tải dữ liệu...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 px-6 animate-fade-in">
        <BrainCircuit size={48} className="text-[#9CA3AF] mb-4" />
        <p className="text-[15px] font-semibold text-[#101010] mb-2">Chưa kết nối Firebase</p>
        <p className="text-[13px] text-[#6B7280] text-center leading-relaxed">
          {error}
        </p>
        <div className="mt-6 p-4 bg-yellow-50 rounded-2xl text-[12px] text-yellow-800 leading-relaxed">
          <strong>Hướng dẫn:</strong><br />
          1. Vào <a href="https://console.firebase.google.com" target="_blank" rel="noopener noreferrer" className="underline">Firebase Console</a> → Tạo project<br />
          2. Thêm Web App → Copy config<br />
          3. Tạo file <code>.env</code> trong project root với các biến VITE_FIREBASE_*<br />
          4. Hoặc sửa trực tiếp <code>src/firebase/firebase.js</code>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Header */}
      <div className="card-hero">
        <h1 className="text-[22px] font-bold">Bò Bụ Bẫm 📊</h1>
        <p className="text-[14px] opacity-80 mt-1">Phân tích video TikTok</p>
        <div className="flex items-center gap-2 mt-3">
          <span className="bg-white/20 text-white text-[13px] font-semibold px-3 py-1 rounded-full">
            {stats.total} video
          </span>
          <span className="bg-white/20 text-white text-[13px] font-semibold px-3 py-1 rounded-full">
            📈 {stats.totalLikes?.toLocaleString('vi-VN')} likes
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard icon={VideoIcon} label="Tổng video" value={stats.total} color="#E6002D" />
        <StatCard icon={Eye} label="Lượt xem" value={stats.totalViews?.toLocaleString('vi-VN')} sub={`TB ${stats.avgViews?.toLocaleString('vi-VN')}/video`} color="#3B82F6" />
        <StatCard icon={ThumbsUp} label="Lượt thích" value={stats.totalLikes?.toLocaleString('vi-VN')} sub={`TB ${stats.avgLikes?.toLocaleString('vi-VN')}/video`} color="#10B981" />
        <StatCard icon={Music} label="Bài hát" value={stats.musicMoods?.length || 0} sub="tâm trạng khác nhau" color="#8B5CF6" />
      </div>

      {/* Charts */}
      {stats.total > 0 && (
        <>
          <PieChartWidget
            data={stats.shirtColors}
            title="👕 Màu áo"
            emptyMessage="Chưa phân tích màu áo"
          />
          <BarChartWidget
            data={stats.hairStyles}
            title="💇 Kiểu tóc"
            emptyMessage="Chưa phân tích kiểu tóc"
          />
          <PieChartWidget
            data={stats.scenes}
            title="📍 Bối cảnh"
            emptyMessage="Chưa phân tích bối cảnh"
          />
          <PieChartWidget
            data={stats.musicMoods}
            title="🎵 Tâm trạng nhạc"
            emptyMessage="Chưa phân tích nhạc"
          />
        </>
      )}
    </div>
  )
}
