import { Routes, Route, Navigate } from 'react-router-dom'
import { AppProvider } from './contexts/AppContext'
import BottomNav from './components/BottomNav'
import Home from './screens/Home'
import Videos from './screens/Videos'
import Stats from './screens/Stats'

export default function App() {
  return (
    <AppProvider>
      <div className="min-h-screen bg-[#F8F8FA] pb-20">
        <div className="max-w-lg mx-auto px-4 pt-4">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/videos" element={<Videos />} />
            <Route path="/stats" element={<Stats />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
        <BottomNav />
      </div>
    </AppProvider>
  )
}
