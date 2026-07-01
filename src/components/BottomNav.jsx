import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Video, BarChart3 } from 'lucide-react'
import { useApp } from '../contexts/AppContext'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Tổng quan' },
  { to: '/videos', icon: Video, label: 'Video' },
  { to: '/stats', icon: BarChart3, label: 'Thống kê' },
]

export default function BottomNav() {
  const { unviewedCount } = useApp()

  return (
    <nav className="bottom-nav">
      {navItems.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          className={({ isActive }) =>
            `nav-item ${isActive ? 'active' : ''}`
          }
        >
          <div className="relative">
            <Icon size={22} strokeWidth={1.8} />
            {label === 'Video' && unviewedCount > 0 && (
              <span className="absolute -top-1 -right-1.5 bg-[#E6002D] text-white text-[9px] font-bold w-4 h-4 flex items-center justify-center rounded-full">
                {unviewedCount > 9 ? '9+' : unviewedCount}
              </span>
            )}
          </div>
          <span className="nav-label">{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
