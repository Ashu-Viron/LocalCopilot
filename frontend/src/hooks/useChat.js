/**
 * Custom hooks for chat functionality
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import api from '../services/api'

export function useChat(initialConversationId = null) {
  const [conversationId, setConversationId] = useState(initialConversationId)
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [isThinking, setIsThinking] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [error, setError] = useState(null)
  
  // Use refs to track state across async operations without causing re-renders
  const streamingContentRef = useRef('')
  const isStreamingRef = useRef(false)
  const currentConversationIdRef = useRef(initialConversationId)

  // Keep ref in sync with state
  useEffect(() => {
    currentConversationIdRef.current = conversationId
  }, [conversationId])

  // Automatically load conversation when initialConversationId is provided
  useEffect(() => {
    if (initialConversationId && !isStreamingRef.current) {
      loadConversationMessages(initialConversationId)
    }
  }, [initialConversationId])

  const loadConversationMessages = async (convId) => {
    // Don't load if currently streaming
    if (isStreamingRef.current) {
      console.log('Skipping load - streaming in progress')
      return
    }
    
    setIsLoading(true)
    setError(null)
    try {
      const response = await api.getConversation(convId)
      setConversationId(convId)
      currentConversationIdRef.current = convId
      // Map messages to the correct format
      const formattedMessages = (response.messages || []).map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp || msg.created_at,
      }))
      setMessages(formattedMessages)
      return response
    } catch (err) {
      console.error('Error loading conversation:', err)
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  // Send message - accepts optional convId to avoid closure issues
  const sendMessage = useCallback(async (message, onFilesChanged, onLog, targetConversationId = null) => {
    // Use provided conversationId or current ref value
    const convIdToUse = targetConversationId || currentConversationIdRef.current
    
    setIsLoading(true)
    setIsThinking(true)
    setError(null)
    setStreamingContent('')
    streamingContentRef.current = ''
    isStreamingRef.current = true

    // Add user message immediately - use functional update to preserve existing messages
    const userMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    }
    
    setMessages(prevMessages => [...prevMessages, userMessage])

    let finalConvId = convIdToUse
    let hasFileChanges = false

    try {
      await api.sendMessageStream(message, convIdToUse, {
        onStatus: (status) => {
          if (status === 'thinking') {
            setIsThinking(true)
          }
        },
        onConversationId: (id) => {
          finalConvId = id
          if (!convIdToUse) {
            setConversationId(id)
            currentConversationIdRef.current = id
          }
        },
        onChunk: (chunk) => {
          setIsThinking(false)
          streamingContentRef.current += chunk
          setStreamingContent(streamingContentRef.current)
        },
        onToolLog: (log) => {
          console.log('Tool log:', log)
          if (onLog) onLog('info', log)
        },
        onFileChange: (change) => {
          console.log('File change:', change)
          hasFileChanges = true
          if (onLog) onLog('success', change)
        },
        onDone: (data) => {
          // Finalize the assistant message - use functional update to preserve all messages
          const assistantMessage = {
            role: 'assistant',
            content: streamingContentRef.current,
            timestamp: new Date().toISOString(),
          }
          
          setMessages(prevMessages => [...prevMessages, assistantMessage])
          setStreamingContent('')
          streamingContentRef.current = ''
          isStreamingRef.current = false
          setIsLoading(false)
          setIsThinking(false)
          
          // Trigger file explorer refresh if needed
          if ((data.has_file_changes || hasFileChanges) && onFilesChanged) {
            onFilesChanged()
          }
        },
        onError: (errorMsg) => {
          setError(errorMsg)
          isStreamingRef.current = false
          setIsLoading(false)
          setIsThinking(false)
        }
      })
    } catch (err) {
      setError(err.message)
      isStreamingRef.current = false
      setIsLoading(false)
      setIsThinking(false)
      console.error('Error sending message:', err)
    }

    return { conversation_id: finalConvId, has_file_changes: hasFileChanges }
  }, []) // No dependencies - uses refs for current values

  const createNewConversation = useCallback(async () => {
    try {
      const response = await api.createConversation()
      const newId = response.conversation_id
      setConversationId(newId)
      currentConversationIdRef.current = newId
      // Don't clear messages here - let the caller decide
      return newId
    } catch (err) {
      setError(err.message)
      console.error('Error creating conversation:', err)
      return null
    }
  }, [])

  const loadConversation = useCallback(async (convId) => {
    // Don't load if currently streaming
    if (isStreamingRef.current) {
      console.log('Skipping load - streaming in progress')
      return null
    }
    
    try {
      const response = await api.getConversation(convId)
      setConversationId(convId)
      currentConversationIdRef.current = convId
      // Map messages to the correct format
      const formattedMessages = (response.messages || []).map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp || msg.created_at,
      }))
      setMessages(formattedMessages)
      return response
    } catch (err) {
      setError(err.message)
      console.error('Error loading conversation:', err)
      return null
    }
  }, [])

  const clearMessages = useCallback(() => {
    if (isStreamingRef.current) {
      console.log('Cannot clear - streaming in progress')
      return
    }
    setMessages([])
    setStreamingContent('')
    streamingContentRef.current = ''
    setError(null)
  }, [])

  const startNewChat = useCallback(async () => {
    // Clear current state and create new conversation
    if (isStreamingRef.current) {
      console.log('Cannot start new chat - streaming in progress')
      return null
    }
    
    setMessages([])
    setStreamingContent('')
    streamingContentRef.current = ''
    setError(null)
    
    return await createNewConversation()
  }, [createNewConversation])

  return {
    conversationId,
    messages,
    isLoading,
    isThinking,
    streamingContent,
    error,
    sendMessage,
    createNewConversation,
    loadConversation,
    clearMessages,
    startNewChat,
  }
}

/**
 * Custom hooks for file operations
 */

export function useFiles() {
  const [files, setFiles] = useState([])
  const [currentPath, setCurrentPath] = useState('.')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const listFiles = useCallback(async (path = '.') => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await api.listFiles(path)
      setFiles(response.files)
      setCurrentPath(path)
      return response
    } catch (err) {
      setError(err.message)
      console.error('Error listing files:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const readFile = useCallback(async (path) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await api.readFile(path)
      return response
    } catch (err) {
      setError(err.message)
      console.error('Error reading file:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const writeFile = useCallback(async (path, content, backup = true) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await api.writeFile(path, content, backup)
      return response
    } catch (err) {
      setError(err.message)
      console.error('Error writing file:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const searchFiles = useCallback(async (pattern, path = null, isRegex = false) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await api.searchFiles(pattern, path, isRegex)
      return response
    } catch (err) {
      setError(err.message)
      console.error('Error searching files:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  return {
    files,
    currentPath,
    isLoading,
    error,
    listFiles,
    readFile,
    writeFile,
    searchFiles,
  }
}
