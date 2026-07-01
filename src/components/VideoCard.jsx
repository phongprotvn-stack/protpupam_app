export default function VideoCard({ video, onView }) {
  const a = video.analysis || {}
  const thumb = video.thumbnail || video.thumb || ''

  const shirtColor = a.shirtColor || a.shirt_color || '—'
  const hairStyle = a.hairStyle || a.hair_style || '—'
  const scene = a.scene || a.location || '—'

  return (
    <div className={`card animate-fade-in ${!video.viewed ? 'ring-2 ring-[#E6002D]/20' : ''}`}>
      <div className="flex gap-3">
        {/* Thumbnail */}
        <div className="w-20 h-20 rounded-2xl overflow-hidden bg-gray-100 shrink-0">
          {thumb ? (
            <img src={thumb} alt="" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-300 text-xs">
              No img
            </div>
          )}
        </div>

        {/* Info */}
        <div className="min-w-0 flex-1">
          <a
            href={video.url || `https://www.tiktok.com/@bobubammm/video/${video.id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[15px] font-semibold text-[#101010] line-clamp-1 hover:text-[#E6002D] transition-colors"
          >
            {video.caption || video.title || `Video #${video.id?.slice(0, 8)}`}
          </a>

          <div className="flex flex-wrap gap-1.5 mt-1.5">
            {shirtColor !== '—' && <span className="badge badge-red">👕 {shirtColor}</span>}
            {hairStyle !== '—' && <span className="badge badge-blue">💇 {hairStyle}</span>}
            {scene !== '—' && <span className="badge badge-green">📍 {scene}</span>}
          </div>

          <p className="text-[11px] text-[#9CA3AF] mt-1.5">
            {video.createdAt
              ? new Date(video.createdAt).toLocaleDateString('vi-VN', {
                  day: '2-digit',
                  month: '2-digit',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })
              : ''}
          </p>
        </div>
      </div>

      {/* Interactions row */}
      <div className="flex gap-4 mt-3 pt-3 border-t border-gray-50">
        <span className="text-[12px] text-[#6B7280]">❤️ {(video.likeCount || video.likes || 0).toLocaleString('vi-VN')}</span>
        <span className="text-[12px] text-[#6B7280]">💬 {(video.commentCount || video.comments || 0).toLocaleString('vi-VN')}</span>
        <span className="text-[12px] text-[#6B7280]">👁️ {(video.viewCount || video.views || 0).toLocaleString('vi-VN')}</span>
      </div>

      {/* Mark viewed button */}
      {!video.viewed && onView && (
        <button
          onClick={() => onView(video.id)}
          className="mt-2 text-[12px] font-medium text-[#E6002D] hover:opacity-70 transition-opacity"
        >
          Đã xem ✓
        </button>
      )}
    </div>
  )
}
