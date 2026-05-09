/**
 * API Service for backend communication
 */

// Automatically use relative URLs (/api) when deployed to AWS/production
// so it seamlessly routes through the Nginx proxy without manual configuration.
const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE_URL = import.meta.env.VITE_API_URL || (isLocalhost ? 'http://localhost:8000/api' : '/api');

class APIClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
      },
    }

    const config = { ...defaultOptions, ...options }
    
    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error(`API Request Failed: ${endpoint}`, error)
      throw error
    }
  }

  // Chat endpoints
  async sendMessage(message, conversationId = null) {
    const endpoint = conversationId 
      ? `/chat/conversation/${conversationId}/message`
      : '/chat/message'
    
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        include_logs: true,
      }),
    })
  }

  /**
   * Send message with streaming response
   * @param {string} message - User message
   * @param {string|null} conversationId - Optional conversation ID
   * @param {object} callbacks - Callback functions for streaming events
   * @param {function} callbacks.onChunk - Called with each text chunk
   * @param {function} callbacks.onStatus - Called with status updates (thinking, etc)
   * @param {function} callbacks.onToolLog - Called with tool execution logs
   * @param {function} callbacks.onFileChange - Called when files are modified
   * @param {function} callbacks.onConversationId - Called with conversation ID
   * @param {function} callbacks.onDone - Called when streaming completes
   * @param {function} callbacks.onError - Called on error
   */
  async sendMessageStream(message, conversationId = null, callbacks = {}) {
    const url = `${this.baseURL}/chat/message/stream`
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          conversation_id: conversationId,
          include_logs: true,
        }),
      })

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        
        // Keep the last incomplete line in buffer
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              switch (data.type) {
                case 'status':
                  callbacks.onStatus?.(data.content)
                  break
                case 'chunk':
                  callbacks.onChunk?.(data.content)
                  break
                case 'conversation_id':
                  callbacks.onConversationId?.(data.content)
                  break
                case 'tool_log':
                  callbacks.onToolLog?.(data.content)
                  break
                case 'file_change':
                  callbacks.onFileChange?.(data.content)
                  break
                case 'done':
                  callbacks.onDone?.(data)
                  break
                case 'error':
                  callbacks.onError?.(data.content)
                  break
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', line)
            }
          }
        }
      }
    } catch (error) {
      console.error('Streaming request failed:', error)
      callbacks.onError?.(error.message)
      throw error
    }
  }

  async createConversation() {
    return this.request('/chat/conversation', {
      method: 'POST',
    })
  }

  async listConversations() {
    return this.request('/chat/conversations')
  }

  async getConversation(conversationId) {
    return this.request(`/chat/conversation/${conversationId}`)
  }

  async deleteConversation(conversationId) {
    return this.request(`/chat/conversation/${conversationId}`, {
      method: 'DELETE',
    })
  }

  // File endpoints
  async listFiles(path = '.') {
    return this.request(`/files/list?path=${encodeURIComponent(path)}`)
  }

  async readFile(path) {
    return this.request(`/files/read?path=${encodeURIComponent(path)}`)
  }

  async writeFile(path, content, backup = true) {
    return this.request('/files/write', {
      method: 'POST',
      body: JSON.stringify({
        path,
        content,
        backup,
      }),
    })
  }

  async createFile(path, content = '') {
    return this.request('/files/create', {
      method: 'POST',
      body: JSON.stringify({
        path,
        content,
      }),
    })
  }

  async deleteFile(path, backup = true) {
    return this.request('/files/delete', {
      method: 'DELETE',
      body: JSON.stringify({
        path,
        backup,
      }),
    })
  }

  async searchFiles(pattern, path = null, isRegex = false, caseSensitive = false) {
    return this.request('/files/search', {
      method: 'POST',
      body: JSON.stringify({
        pattern,
        path,
        is_regex: isRegex,
        case_sensitive: caseSensitive,
      }),
    })
  }

  // Tool endpoints
  async executeTool(tool, parameters, timeout = 30) {
    return this.request('/tools/execute', {
      method: 'POST',
      body: JSON.stringify({
        tool,
        parameters,
        timeout,
      }),
    })
  }

  async getExecutionLogs(limit = null) {
    const query = limit ? `?limit=${limit}` : ''
    return this.request(`/tools/logs${query}`)
  }

  async clearExecutionLogs() {
    return this.request('/tools/logs/clear', {
      method: 'POST',
    })
  }

  async listAvailableTools() {
    return this.request('/tools/available')
  }

  // System endpoints
  async getSystemStatus() {
    return this.request('/system/status')
  }

  async getSystemConfig() {
    return this.request('/system/config')
  }

  async getWorkspaceInfo() {
    return this.request('/system/workspace')
  }

  async healthCheck() {
    return this.request('/system/health')
  }

  async getSystemHealth() {
    return this.healthCheck()
  }

  // Terminal endpoints
  async executeCommand(command, cwd = null, timeout = 30) {
    return this.request('/terminal/execute', {
      method: 'POST',
      body: JSON.stringify({
        command,
        cwd,
        timeout,
      }),
    })
  }

  // Model endpoints
  async getAvailableModels() {
    return this.request('/models/available')
  }

  async getCurrentModel() {
    return this.request('/models/current')
  }

  async getModelStatus() {
    return this.request('/models/status')
  }

  async getConfig() {
    try {
      return await this.request('/system/config')
    } catch {
      return {}
    }
  }
}

export default new APIClient()
