import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

export default function HomePage() {
  const navigate = useNavigate()
  const [recentConversations, setRecentConversations] = useState([])

  useEffect(() => {
    loadRecentConversations()
  }, [])

  const loadRecentConversations = async () => {
    try {
      const conversations = await api.listConversations()
      setRecentConversations(conversations?.slice(0, 4) || [])
    } catch (err) {
      console.error('Failed to load conversations:', err)
    }
  }

  return (
    <div className="h-full overflow-auto bg-[#0d1117]">
      <div className="max-w-4xl mx-auto px-8 py-12">
        {/* Welcome Section */}
        <div className="mb-12">
          <h1 className="text-3xl font-semibold text-[#c9d1d9] mb-3">
            Welcome back
          </h1>
          <p className="text-[#8b949e] text-base leading-relaxed">
            Your AI coding assistant is ready. Start a new conversation or continue where you left off.
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 gap-4 mb-12">
          <button
            onClick={() => navigate('/editor')}
            className="group p-5 bg-[#161b22] border border-[#21262d] rounded-lg text-left hover:border-[#388bfd] transition-colors"
          >
            <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-8 bg-[#238636] rounded flex items-center justify-center text-white text-sm">
                +
              </div>
              <span className="text-[#c9d1d9] font-medium">New Session</span>
            </div>
            <p className="text-[#8b949e] text-sm">Open the editor and start coding with AI assistance</p>
          </button>

          <button
            onClick={() => navigate('/chat')}
            className="group p-5 bg-[#161b22] border border-[#21262d] rounded-lg text-left hover:border-[#388bfd] transition-colors"
          >
            <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-8 bg-[#1f6feb] rounded flex items-center justify-center text-white text-sm">
                ↗
              </div>
              <span className="text-[#c9d1d9] font-medium">Browse History</span>
            </div>
            <p className="text-[#8b949e] text-sm">View and manage your past conversations</p>
          </button>
        </div>

        {/* Recent Conversations */}
        {recentConversations.length > 0 && (
          <div className="mb-12">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-medium text-[#8b949e] uppercase tracking-wide">Recent</h2>
              <button 
                onClick={() => navigate('/chat')}
                className="text-xs text-[#388bfd] hover:underline"
              >
                View all
              </button>
            </div>
            <div className="space-y-2">
              {recentConversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => navigate(`/editor?conversation=${conv.id}`)}
                  className="w-full flex items-center gap-3 p-3 bg-[#161b22] border border-[#21262d] rounded-lg text-left hover:border-[#30363d] transition-colors"
                >
                  <div className="w-8 h-8 bg-[#21262d] rounded flex items-center justify-center text-[#8b949e] text-xs">
                    #
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-[#c9d1d9] truncate">
                      {conv.title || 'Untitled conversation'}
                    </div>
                    <div className="text-xs text-[#484f58]">
                      {conv.created_at ? new Date(conv.created_at).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric'
                      }) : 'No date'}
                    </div>
                  </div>
                  <span className="text-[#484f58] text-sm">→</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Info Section */}
        <div className="bg-[#161b22] border border-[#21262d] rounded-lg p-5">
          <h3 className="text-sm font-medium text-[#c9d1d9] mb-3">Getting Started</h3>
          <ul className="space-y-2 text-sm text-[#8b949e]">
            <li className="flex items-start gap-2">
              <span className="text-[#484f58] mt-0.5">•</span>
              <span>Use the <strong className="text-[#c9d1d9]">Editor</strong> to write code with AI suggestions</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#484f58] mt-0.5">•</span>
              <span>Ask questions in the chat panel on the right</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#484f58] mt-0.5">•</span>
              <span>Configure your preferred AI model in <strong className="text-[#c9d1d9]">Settings</strong></span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
