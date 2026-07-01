import { createContext, useContext, useEffect, useState, useMemo } from 'react'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [videos, setVideos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let unsubscribe = null
    let cancelled = false

    async function init() {
      try {
        const { db } = await import('../firebase/firebase.js')
        if (!db) {
          setError('Firebase chưa được cấu hình. Vào Firebase Console tạo project và cập nhật firebase.js')
          setLoading(false)
          return
        }
        const { collection, query, orderBy, onSnapshot } = await import('firebase/firestore')

        const q = query(collection(db, 'videos'), orderBy('createdAt', 'desc'))
        unsubscribe = onSnapshot(q, (snapshot) => {
          if (cancelled) return
          const list = []
          snapshot.forEach((doc) => {
            list.push({ id: doc.id, ...doc.data() })
          })
          setVideos(list)
          setLoading(false)
        }, (err) => {
          console.error('Firestore error:', err)
          if (!cancelled) {
            setError('Lỗi kết nối Firestore: ' + err.message)
            setLoading(false)
          }
        })
      } catch (e) {
        if (!cancelled) {
          setError('Lỗi khởi tạo: ' + e.message)
          setLoading(false)
        }
      }
    }

    init()

    return () => {
      cancelled = true
      if (unsubscribe) unsubscribe()
    }
  }, [])

  // ===== Computed stats =====
  const stats = useMemo(() => {
    const total = videos.length
    if (total === 0) return { total: 0 }

    // Shirt color frequency
    const shirtColors = {}
    // Hair style frequency
    const hairStyles = {}
    // Scene (indoor/outdoor)
    const scenes = {}
    // Mood
    const moods = {}
    // Music mood
    const musicMoods = {}
    // Emotions
    const emotions = {}
    // Total views, likes, comments
    let totalViews = 0
    let totalLikes = 0
    let totalComments = 0
    let totalShares = 0

    videos.forEach((v) => {
      const analysis = v.analysis || {}

      // Shirt
      const sc = analysis.shirtColor || analysis.shirt_color || 'unknown'
      shirtColors[sc] = (shirtColors[sc] || 0) + 1

      // Hair
      const hs = analysis.hairStyle || analysis.hair_style || 'unknown'
      hairStyles[hs] = (hairStyles[hs] || 0) + 1

      // Scene
      const scn = analysis.scene || analysis.location || 'unknown'
      scenes[scn] = (scenes[scn] || 0) + 1

      // Emotion
      const emo = analysis.emotion || 'unknown'
      emotions[emo] = (emotions[emo] || 0) + 1

      // Music mood
      const mm = analysis.musicMood || analysis.music_mood || 'unknown'
      musicMoods[mm] = (musicMoods[mm] || 0) + 1

      // Interaction stats
      totalViews += v.viewCount || v.views || 0
      totalLikes += v.likeCount || v.likes || 0
      totalComments += v.commentCount || v.comments || 0
      totalShares += v.shareCount || v.shares || 0
    })

    // Convert to chart-friendly format
    const toChart = (obj) =>
      Object.entries(obj)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value)

    return {
      total,
      shirtColors: toChart(shirtColors),
      hairStyles: toChart(hairStyles),
      scenes: toChart(scenes),
      emotions: toChart(emotions),
      musicMoods: toChart(musicMoods),
      totalViews,
      totalLikes,
      totalComments,
      totalShares,
      avgViews: total > 0 ? Math.round(totalViews / total) : 0,
      avgLikes: total > 0 ? Math.round(totalLikes / total) : 0,
    }
  }, [videos])

  const [unviewedCount, setUnviewedCount] = useState(0)

  useEffect(() => {
    const unviewed = videos.filter((v) => !v.viewed).length
    setUnviewedCount(unviewed)
  }, [videos])

  // Mark video as viewed
  async function markViewed(videoId) {
    try {
      const { db } = await import('../firebase/firebase.js')
      if (!db) return
      const { doc, updateDoc } = await import('firebase/firestore')
      await updateDoc(doc(db, 'videos', videoId), { viewed: true })
    } catch (e) {
      console.error('Error marking viewed:', e)
    }
  }

  // Update video analysis manually
  async function updateAnalysis(videoId, analysis) {
    try {
      const { db } = await import('../firebase/firebase.js')
      if (!db) return
      const { doc, updateDoc } = await import('firebase/firestore')
      await updateDoc(doc(db, 'videos', videoId), { analysis, analyzedAt: new Date().toISOString() })
    } catch (e) {
      console.error('Error updating analysis:', e)
    }
  }

  return (
    <AppContext.Provider
      value={{
        videos,
        stats,
        loading,
        error,
        unviewedCount,
        markViewed,
        updateAnalysis,
      }}
    >
      {children}
    </AppContext.Provider>
  )
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used within AppProvider')
  return ctx
}
