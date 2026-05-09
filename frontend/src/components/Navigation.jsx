import React, { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

export default function Navigation() {
  const navigate = useNavigate()
  const location = useLocation()
  const [isExpanded, setIsExpanded] = useState(true)

  const navItems = [
    { id: 'home', label: 'Home', path: '/' },
    { id: 'editor', label: 'Editor', path: '/editor' },
    { id: 'chat', label: 'Chat', path: '/chat' },
    { id: 'settings', label: 'Settings', path: '/settings' },
  ]

  const isActive = (path) => location.pathname === path

  return (
    <div className={`${isExpanded ? 'w-56' : 'w-16'} transition-all duration-200 bg-[#0d1117] border-r border-[#21262d] h-screen flex flex-col shrink-0`}>
      {/* Header */}
      <div className="h-14 px-4 border-b border-[#21262d] flex items-center justify-between">
        {isExpanded ? (
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-[#238636] rounded flex items-center justify-center font-semibold text-white text-xs">
              LC
            </div>
            <span className="text-sm font-semibold text-[#c9d1d9]">LocalCopilot</span>
          </div>
        ) : (
          <div className="w-7 h-7 bg-[#238636] rounded flex items-center justify-center font-semibold text-white text-xs mx-auto">
            LC
          </div>
        )}
        {isExpanded && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-6 h-6 flex items-center justify-center hover:bg-[#21262d] rounded text-[#8b949e] text-xs"
          >
            ‹
          </button>
        )}
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 py-3 px-2">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => navigate(item.path)}
            className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors mb-0.5 ${
              isActive(item.path)
                ? 'bg-[#21262d] text-white font-medium'
                : 'text-[#8b949e] hover:text-[#c9d1d9] hover:bg-[#161b22]'
            }`}
          >
            <span className={`w-5 h-5 flex items-center justify-center rounded text-xs ${
              isActive(item.path) ? 'bg-[#238636] text-white' : 'bg-[#21262d] text-[#8b949e]'
            }`}>
              {item.label.charAt(0)}
            </span>
            {isExpanded && <span>{item.label}</span>}
          </button>
        ))}
      </nav>

      {/* Expand button when collapsed */}
      {!isExpanded && (
        <div className="p-2 border-t border-[#21262d]">
          <button
            onClick={() => setIsExpanded(true)}
            className="w-full h-8 flex items-center justify-center hover:bg-[#21262d] rounded text-[#8b949e] text-xs"
          >
            ›
          </button>
        </div>
      )}
    </div>
  )
}
