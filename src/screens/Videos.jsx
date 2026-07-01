import { useApp } from '../contexts/AppContext'
import VideoCard from '../components/VideoCard'
import { ListVideo } from 'lucide-react'

export default function Videos() {
  const { videos, loading, markViewed } = useApp()

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 animate-fade-in">
        <div className="w-10 h-10 border-3 border-[#E6002D] border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-[14px] text-[#6B7280]">Đang tải video...</p>
      </div>
    )
  }

  if (videos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-32 animate-fade-in">
        <ListVideo size={48} className="text-[#D1D5DB] mb-4" />
        <p className="text-[15px] font-semibold text-[#101010] mb-1">Chưa có video</p>
        <p className="text-[13px] text-[#6B7280]">Đợi GitHub Actions crawl video đầu tiên nhé!</p>
      </div>
    )
  }

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-[20px] font-bold text-[#101010]">📹 Video</h1>
        <span className="text-[13px] text-[#6B7280]">{videos.length} video</span>
      </div>

      {videos.map((v) => (
        <VideoCard key={v.id} video={v} onView={markViewed} />
      ))}
    </div>
  )
}
