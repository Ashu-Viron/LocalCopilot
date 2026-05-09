import React, { useState, useEffect, useRef } from 'react'

export default function ToolLogs({ logs = [] }) {
  const [filteredLogs, setFilteredLogs] = useState(logs)
  const [filterLevel, setFilterLevel] = useState('all')
  const [expandedLogs, setExpandedLogs] = useState(new Set())
  const logsEndRef = useRef(null)

  useEffect(() => {
    const filtered = filterLevel === 'all'
      ? logs
      : logs.filter(log => (log.level || log.type)?.toLowerCase() === filterLevel.toLowerCase())
    setFilteredLogs(filtered)
  }, [logs, filterLevel])

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [filteredLogs])

  useEffect(() => {
    // Listen for new logs from parent
    const handleNewLog = (e) => {
      // Logs will be updated through props
    }

    window.addEventListener('newToolLog', handleNewLog)
    return () => window.removeEventListener('newToolLog', handleNewLog)
  }, [])

  const toggleLog = (logIdx) => {
    const newExpanded = new Set(expandedLogs)
    if (newExpanded.has(logIdx)) {
      newExpanded.delete(logIdx)
    } else {
      newExpanded.add(logIdx)
    }
    setExpandedLogs(newExpanded)
  }

  const getLogColor = (level) => {
    const colors = {
      'error': 'text-[#f85149]',
      'warning': 'text-[#d29922]',
      'info': 'text-[#58a6ff]',
      'debug': 'text-[#8b949e]',
      'success': 'text-[#3fb950]',
    }
    return colors[level?.toLowerCase()] || colors.info
  }

  const getLogIcon = (level) => {
    const icons = {
      'error': '✕',
      'warning': '!',
      'info': 'i',
      'debug': '·',
      'success': '✓',
    }
    return icons[level?.toLowerCase()] || 'i'
  }

  const getLogBgColor = (level) => {
    const colors = {
      'error': 'bg-[#3d1e20]',
      'warning': 'bg-[#3b2e1a]',
      'info': 'bg-[#1a2433]',
      'debug': 'bg-[#161b22]',
      'success': 'bg-[#1a3329]',
    }
    return colors[level?.toLowerCase()] || colors.info
  }

  const clearLogs = () => {
    window.dispatchEvent(new CustomEvent('clearToolLogs'))
  }

  return (
    <div className="flex flex-col h-full bg-[#010409]">
      {/* Header */}
      <div className="px-4 py-2 border-b border-[#21262d] bg-[#0d1117] flex items-center justify-between">
        <h3 className="text-xs font-medium text-[#8b949e]">Logs</h3>
        <div className="flex items-center gap-2">
          <select
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value)}
            className="text-xs px-2 py-1 bg-[#161b22] border border-[#21262d] text-[#8b949e] rounded focus:outline-none focus:border-[#388bfd]"
          >
            <option value="all">All</option>
            <option value="error">Errors</option>
            <option value="warning">Warnings</option>
            <option value="info">Info</option>
            <option value="success">Success</option>
          </select>
          <button
            onClick={clearLogs}
            className="text-xs px-2 py-1 bg-[#21262d] hover:bg-[#30363d] rounded text-[#8b949e]"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Logs Container */}
      <div className="flex-1 overflow-y-auto">
        {filteredLogs.length === 0 ? (
          <div className="flex items-center justify-center h-full text-[#484f58]">
            <p className="text-sm">No logs yet</p>
          </div>
        ) : (
          <div className="divide-y divide-[#21262d]">
            {filteredLogs.map((log, idx) => {
              const logLevel = log.level || log.type || 'info'
              return (
                <div
                  key={idx}
                  className={`px-4 py-2 hover:bg-[#161b22] cursor-pointer ${getLogBgColor(logLevel)}`}
                  onClick={() => toggleLog(idx)}
                >
                  {/* Log Header */}
                  <div className="flex items-start gap-2">
                    <span className={`w-4 h-4 flex items-center justify-center text-xs font-bold rounded ${getLogColor(logLevel)}`}>
                      {getLogIcon(logLevel)}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-medium ${getLogColor(logLevel)}`}>
                          {logLevel.toUpperCase()}
                        </span>
                        {log.tool && (
                          <span className="text-xs text-[#8b949e] bg-[#21262d] px-1.5 py-0.5 rounded">
                            {log.tool}
                          </span>
                        )}
                        <span className="text-xs text-[#484f58] ml-auto">
                          {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-sm text-[#c9d1d9] mt-1">{log.message}</p>
                    </div>
                    {log.details && (
                      <span className={`text-xs text-[#484f58] ${expandedLogs.has(idx) ? 'rotate-90' : ''}`}>
                        ▶
                      </span>
                    )}
                  </div>

                  {/* Log Details */}
                  {log.details && expandedLogs.has(idx) && (
                    <div className="mt-2 ml-6 p-2 bg-[#0d1117] rounded font-mono text-xs text-[#8b949e] max-h-40 overflow-y-auto border border-[#21262d]">
                      <pre className="whitespace-pre-wrap break-words">
                        {JSON.stringify(log.details, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
        <div ref={logsEndRef} />
      </div>

      {/* Footer */}
      {filteredLogs.length > 0 && (
        <div className="px-4 py-1 border-t border-[#21262d] bg-[#0d1117] text-xs text-[#484f58]">
          {filteredLogs.length} log(s)
        </div>
      )}
    </div>
  )
}
