import React, { useState, useRef, useEffect, forwardRef, useImperativeHandle } from 'react'
import { useChat } from '../hooks/useChat'
import MarkdownRenderer from './MarkdownRenderer'

const ChatPanel = forwardRef(function ChatPanel({ conversationId, onFilesChanged, onLog }, ref) {
  const { 
    conversationId: currentConversationId,
    messages, 
    isLoading, 
    isThinking, 
    streamingContent, 
    error, 
    sendMessage, 
    createNewConversation,
    startNewChat 
  } = useChat(conversationId)
  
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef(null)
  const messagesContainerRef = useRef(null)

  // Expose startNewChat to parent via ref
  useImperativeHandle(ref, () => ({
    startNewChat: handleNewChat
  }), [])

  // Auto-scroll to bottom when new content arrives
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, streamingContent, isThinking])

  const handleSendMessage = async (e) => {
    e.preventDefault()
    if (!inputValue.trim() || isLoading) return

    const message = inputValue.trim()
    setInputValue('')
    
    try {
      // If no conversation exists, create one first then send with that ID
      let targetConvId = currentConversationId
      if (!targetConvId) {
        targetConvId = await createNewConversation()
      }
      // Pass the conversationId explicitly to avoid closure issues
      await sendMessage(message, onFilesChanged, onLog, targetConvId)
    } catch (err) {
      console.error('Error sending message:', err)
    }
  }

  const handleNewChat = async () => {
    if (isLoading) return
    await startNewChat()
  }

  return (
    <div className="flex flex-col h-full bg-[#010409]">
      {/* Header with New Chat button */}
      <div className="h-10 px-4 flex items-center justify-between border-b border-[#21262d] shrink-0">
        <span className="text-xs font-medium text-[#8b949e] uppercase tracking-wide">Chat</span>
        <button 
          onClick={handleNewChat}
          disabled={isLoading}
          className="w-6 h-6 bg-[#238636] rounded text-white text-xs font-medium hover:bg-[#2ea043] disabled:bg-[#21262d] disabled:cursor-not-allowed flex items-center justify-center"
          title="New Chat"
        >
          +
        </button>
      </div>

      {/* Messages Area - Always visible */}
      <div 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4"
      >
        {messages.length === 0 && !streamingContent && !isThinking ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <p className="text-[#c9d1d9] text-sm mb-1">No messages yet</p>
              <p className="text-[#484f58] text-xs">Ask a question to get started</p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {/* Render all existing messages */}
            {messages.map((message, idx) => (
              <div key={`msg-${idx}-${message.timestamp || idx}`} className={message.role === 'user' ? 'flex justify-end' : ''}>
                <div
                  className={`max-w-[85%] px-3 py-2 rounded-lg text-sm ${
                    message.role === 'user'
                      ? 'bg-[#1f6feb] text-white'
                      : 'bg-[#161b22] text-[#c9d1d9] border border-[#21262d]'
                  }`}
                >
                  {message.role === 'user' ? (
                    <pre className="whitespace-pre-wrap break-words leading-relaxed font-sans m-0">{message.content}</pre>
                  ) : (
                    <MarkdownRenderer content={message.content} />
                  )}
                </div>
              </div>
            ))}

            {/* Thinking indicator - shows while waiting for first chunk */}
            {isThinking && !streamingContent && (
              <div className="flex items-center gap-2 px-3 py-2 bg-[#161b22] border border-[#21262d] rounded-lg max-w-[85%]">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-[#58a6ff] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-[#58a6ff] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-[#58a6ff] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="text-[#8b949e] text-sm">Thinking...</span>
              </div>
            )}

            {/* Streaming response - shows as chunks arrive */}
            {streamingContent && (
              <div className="max-w-[85%] px-3 py-2 rounded-lg text-sm bg-[#161b22] text-[#c9d1d9] border border-[#21262d]">
                <MarkdownRenderer content={streamingContent} />
                <span className="inline-block w-2 h-4 bg-[#58a6ff] ml-1 animate-pulse" />
              </div>
            )}

            {/* Error display */}
            {error && (
              <div className="px-3 py-2 bg-[#3d1e20] border border-[#6e3630] rounded-lg text-[#f85149] text-sm">
                Error: {error}
              </div>
            )}
            
            {/* Scroll anchor */}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <form onSubmit={handleSendMessage} className="p-3 border-t border-[#21262d]">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={isLoading ? "Waiting for response..." : "Ask something..."}
            disabled={isLoading}
            className="flex-1 px-3 py-2 bg-[#0d1117] border border-[#21262d] rounded-md text-sm text-[#c9d1d9] placeholder-[#484f58] focus:outline-none focus:border-[#388bfd] disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="px-4 py-2 bg-[#238636] hover:bg-[#2ea043] disabled:bg-[#21262d] disabled:text-[#484f58] text-white rounded-md text-sm font-medium transition-colors"
          >
            {isLoading ? (
              <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
            ) : 'Send'}
          </button>
        </div>
      </form>
    </div>
  )
})

export default ChatPanel