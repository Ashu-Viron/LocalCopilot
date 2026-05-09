import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

export default function ChatPage() {
  const navigate = useNavigate()
  const [conversations, setConversations] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadConversations()
  }, [])

  const loadConversations = async () => {
    try {
      setLoading(true)
      const data = await api.listConversations()
      setConversations(data || [])
    } catch (err) {
      console.error('Failed to load conversations:', err)
    } finally {
      setLoading(false)
    }
  }

  const deleteConversation = async (id) => {
    try {
      await api.deleteConversation(id)
      setConversations(conversations.filter(c => c.id !== id))
    } catch (err) {
      console.error('Failed to delete conversation:', err)
    }
  }

  const filteredConversations = conversations.filter(conv =>
    conv.title?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="h-full overflow-auto bg-[#0d1117]">
      <div className="max-w-3xl mx-auto px-8 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-[#c9d1d9] mb-1">Conversations</h1>
          <p className="text-sm text-[#8b949e]">View and manage your chat history</p>
        </div>

        {/* Search */}
        <div className="mb-6">
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 bg-[#0d1117] border border-[#21262d] rounded-md text-sm text-[#c9d1d9] placeholder-[#484f58] focus:outline-none focus:border-[#388bfd]"
          />
        </div>

        {/* Conversations List */}
        {loading ? (
          <div className="text-center py-12 text-[#484f58] text-sm">Loading...</div>
        ) : filteredConversations.length > 0 ? (
          <div className="space-y-2">
            {filteredConversations.map((conv) => (
              <div
                key={conv.id}
                className="group flex items-center justify-between p-3 bg-[#161b22] border border-[#21262d] rounded-lg hover:border-[#30363d] transition-colors"
              >
                <button
                  onClick={() => navigate(`/editor?conversation=${conv.id}`)}
                  className="flex-1 text-left"
                >
                  <div className="text-sm text-[#c9d1d9] group-hover:text-[#388bfd] transition-colors">
                    {conv.title || 'Untitled conversation'}
                  </div>
                  <div className="text-xs text-[#484f58] mt-0.5">
                    {conv.created_at ? new Date(conv.created_at).toLocaleDateString('en-US', {
                      month: 'short', day: 'numeric', year: 'numeric'
                    }) : 'No date'}
                  </div>
                </button>
                <button
                  onClick={() => deleteConversation(conv.id)}
                  className="px-2 py-1 text-xs text-[#484f58] hover:text-[#f85149] opacity-0 group-hover:opacity-100 transition-all"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-[#8b949e] text-sm mb-4">No conversations found</p>
            <button
              onClick={() => navigate('/editor')}
              className="px-4 py-2 bg-[#238636] hover:bg-[#2ea043] text-white rounded-md text-sm font-medium transition-colors"
            >
              Start a new conversation
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
