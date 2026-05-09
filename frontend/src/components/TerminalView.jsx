import React, { useState, useEffect, useRef } from 'react'
import api from '../services/api'

export default function TerminalView({ onCommandComplete }) {
  const [output, setOutput] = useState([
    { type: 'info', text: '$ Terminal ready - connected to backend workspace' }
  ])
  const [command, setCommand] = useState('')
  const [currentDir, setCurrentDir] = useState('')
  const [isExecuting, setIsExecuting] = useState(false)
  const [commandHistory, setCommandHistory] = useState([])
  const [historyIndex, setHistoryIndex] = useState(-1)
  const outputEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    scrollToBottom()
  }, [output])

  useEffect(() => {
    // Listen for terminal output from parent
    const handleTerminalOutput = (e) => {
      addOutput(e.detail.type, e.detail.text)
    }

    window.addEventListener('terminalOutput', handleTerminalOutput)
    return () => window.removeEventListener('terminalOutput', handleTerminalOutput)
  }, [])

  const scrollToBottom = () => {
    outputEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const addOutput = (type, text) => {
    setOutput(prev => [...prev, { type, text }])
  }

  const handleExecuteCommand = async (e) => {
    e.preventDefault()
    if (!command.trim() || isExecuting) return

    const cmd = command.trim()
    setCommand('')
    setIsExecuting(true)
    
    // Add to history
    setCommandHistory(prev => [...prev, cmd])
    setHistoryIndex(-1)

    // Add command to output
    addOutput('command', `${currentDir ? `${currentDir} ` : ''}$ ${cmd}`)

    // Intercept cd command to maintain state
    if (cmd.startsWith('cd ') || cmd === 'cd') {
      const target = cmd.substring(3).trim()
      if (!target || target === '~' || target === '/' || target === '\\') {
        setCurrentDir('')
      } else if (target === '..') {
        const parts = currentDir.split(/[\/\\]/)
        parts.pop()
        setCurrentDir(parts.join('/'))
      } else {
        setCurrentDir(currentDir ? `${currentDir}/${target}` : target)
      }
      setIsExecuting(false)
      inputRef.current?.focus()
      return
    }

    try {
      // Call real backend terminal API
      const result = await api.executeCommand(cmd, currentDir || undefined)
      
      // Show stdout
      if (result.stdout && result.stdout.trim()) {
        result.stdout.trim().split('\n').forEach(line => {
          addOutput('success', line)
        })
      }
      
      // Show stderr
      if (result.stderr && result.stderr.trim()) {
        result.stderr.trim().split('\n').forEach(line => {
          addOutput('error', line)
        })
      }
      
      // If no output at all
      if (!result.stdout?.trim() && !result.stderr?.trim()) {
        if (result.success) {
          addOutput('info', '(command completed with no output)')
        } else {
          addOutput('error', `Command failed with exit code ${result.return_code}`)
        }
      }
      
      // Notify parent that command completed (for file explorer refresh)
      if (onCommandComplete) {
        // Check if command might have modified files
        const fsCommands = ['touch', 'mkdir', 'rm', 'rmdir', 'cp', 'mv', 'echo', 'cat', 'del', 'copy', 'move', 'new-item', 'remove-item']
        const lowerCmd = cmd.toLowerCase()
        if (fsCommands.some(c => lowerCmd.includes(c)) || lowerCmd.includes('>')) {
          onCommandComplete(cmd)
        }
      }
      
    } catch (err) {
      addOutput('error', `Error: ${err.message}`)
    } finally {
      setIsExecuting(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e) => {
    // Navigate command history with up/down arrows
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (commandHistory.length > 0) {
        const newIndex = historyIndex < commandHistory.length - 1 ? historyIndex + 1 : historyIndex
        setHistoryIndex(newIndex)
        setCommand(commandHistory[commandHistory.length - 1 - newIndex] || '')
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1
        setHistoryIndex(newIndex)
        setCommand(commandHistory[commandHistory.length - 1 - newIndex] || '')
      } else {
        setHistoryIndex(-1)
        setCommand('')
      }
    }
  }

  const getOutputColor = (type) => {
    const colors = {
      command: 'text-[#58a6ff]',
      success: 'text-[#3fb950]',
      error: 'text-[#f85149]',
      warning: 'text-[#d29922]',
      info: 'text-[#8b949e]',
    }
    return colors[type] || colors.info
  }

  const clearTerminal = () => {
    setOutput([{ type: 'info', text: '$ Terminal cleared' }])
  }

  return (
    <div className="flex flex-col h-full bg-[#010409]">
      {/* Header */}
      <div className="px-4 py-2 border-b border-[#21262d] bg-[#0d1117] flex items-center justify-between">
        <h3 className="text-xs font-medium text-[#8b949e]">Terminal</h3>
        <button
          onClick={clearTerminal}
          className="text-xs px-2 py-1 bg-[#21262d] hover:bg-[#30363d] rounded text-[#8b949e]"
        >
          Clear
        </button>
      </div>

      {/* Output Area */}
      <div className="flex-1 overflow-y-auto p-3 font-mono text-sm space-y-0.5">
        {output.map((line, idx) => (
          <div key={idx} className={`${getOutputColor(line.type)}`}>
            {line.text}
          </div>
        ))}
        <div ref={outputEndRef} />
      </div>

      {/* Input Area */}
      <form
        onSubmit={handleExecuteCommand}
        className="p-3 border-t border-[#21262d] bg-[#0d1117] flex gap-2 items-center"
      >
        <span className="text-[#58a6ff] font-mono text-sm shrink-0 whitespace-nowrap">
          {currentDir ? `${currentDir} $` : '$'}
        </span>
        <input
          ref={inputRef}
          type="text"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type command... (↑↓ for history)"
          disabled={isExecuting}
          className="flex-1 bg-transparent focus:outline-none text-[#c9d1d9] text-sm font-mono placeholder-[#484f58]"
        />
        <button
          type="submit"
          disabled={isExecuting || !command.trim()}
          className="px-2 py-1 text-xs bg-[#238636] hover:bg-[#2ea043] disabled:bg-[#21262d] disabled:text-[#484f58] text-white rounded"
        >
          {isExecuting ? '...' : 'Run'}
        </button>
      </form>
    </div>
  )
}
