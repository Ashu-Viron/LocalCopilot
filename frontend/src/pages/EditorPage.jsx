import React, { useState, useCallback, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import ChatPanel from '../components/ChatPanel'
import FileExplorer from '../components/FileExplorer'
import CodeEditor from '../components/CodeEditor'
import TerminalView from '../components/TerminalView'
import DiffViewer from '../components/DiffViewer'
import ToolLogs from '../components/ToolLogs'
import api from '../services/api'

export default function EditorPage() {
  const [searchParams] = useSearchParams()
  const conversationIdFromUrl = searchParams.get('conversation')
  
  const fileExplorerRef = useRef(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [openFiles, setOpenFiles] = useState([])
  const [activeTab, setActiveTab] = useState('terminal')
  const [conversationId, setConversationId] = useState(conversationIdFromUrl)
  const [editorContent, setEditorContent] = useState('')
  const [originalContent, setOriginalContent] = useState('')
  const [unsavedFiles, setUnsavedFiles] = useState(new Set())
  const [diffData, setDiffData] = useState(null)
  const [logs, setLogs] = useState([])
  const [terminalOutput, setTerminalOutput] = useState([])
  const [showBottomPanel, setShowBottomPanel] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  // Chat panel resize state
  const [chatWidth, setChatWidth] = useState(320)
  const [isResizing, setIsResizing] = useState(false)
  const resizeRef = useRef(null)
  const startXRef = useRef(0)
  const startWidthRef = useRef(320)
  
  // Explorer panel resize state
  const [explorerWidth, setExplorerWidth] = useState(240)
  const [isResizingExplorer, setIsResizingExplorer] = useState(false)
  const resizeExplorerRef = useRef(null)
  const startExplorerXRef = useRef(0)
  const startExplorerWidthRef = useRef(240)
  const [saveStatus, setSaveStatus] = useState('')
  const [showNewFileModal, setShowNewFileModal] = useState(false)
  const [newFileName, setNewFileName] = useState('')

  // Helper to refresh file explorer
  const refreshFileExplorer = useCallback(() => {
    if (fileExplorerRef.current) {
      fileExplorerRef.current.refresh()
    }
  }, [])

  // Handler for terminal command completion
  const handleTerminalCommandComplete = useCallback((cmd) => {
    // Refresh file explorer after filesystem-modifying commands
    console.log('Terminal command completed:', cmd)
    refreshFileExplorer()
  }, [refreshFileExplorer])

  // Load file content from backend when file is selected
  const loadFileContent = useCallback(async (file) => {
    if (!file || !file.is_file) return
    
    setIsLoading(true)
    try {
      const response = await api.readFile(file.path)
      const content = response.content || ''
      setEditorContent(content)
      setOriginalContent(content)
      setLogs(prev => [...prev, { type: 'info', message: `Loaded: ${file.path}` }])
    } catch (err) {
      console.error('Error loading file:', err)
      setEditorContent('')
      setOriginalContent('')
      setLogs(prev => [...prev, { type: 'error', message: `Failed to load: ${file.path}` }])
    } finally {
      setIsLoading(false)
    }
  }, [])

  const handleFileSelect = useCallback(async (file) => {
    // Check if file is already open
    const existingFile = openFiles.find(f => f.path === file.path)
    
    if (existingFile) {
      setSelectedFile(existingFile)
    } else {
      setOpenFiles(prev => [...prev, file])
      setSelectedFile(file)
    }
    
    // Load content from backend
    await loadFileContent(file)
  }, [openFiles, loadFileContent])

  const handleTabClose = (path) => {
    const newOpenFiles = openFiles.filter(f => f.path !== path)
    setOpenFiles(newOpenFiles)
    setUnsavedFiles(prev => {
      const next = new Set(prev)
      next.delete(path)
      return next
    })
    
    if (selectedFile?.path === path) {
      if (newOpenFiles.length > 0) {
        const newSelected = newOpenFiles[newOpenFiles.length - 1]
        setSelectedFile(newSelected)
        loadFileContent(newSelected)
      } else {
        setSelectedFile(null)
        setEditorContent('')
        setOriginalContent('')
      }
    }
  }

  const handleEditorChange = (content) => {
    setEditorContent(content)
    if (selectedFile && content !== originalContent) {
      setUnsavedFiles(prev => new Set([...prev, selectedFile.path]))
    } else if (selectedFile && content === originalContent) {
      setUnsavedFiles(prev => {
        const next = new Set(prev)
        next.delete(selectedFile.path)
        return next
      })
    }
  }

  // Save file to backend
  const handleSaveFile = useCallback(async () => {
    if (!selectedFile) return
    
    setIsLoading(true)
    setSaveStatus('Saving...')
    
    try {
      await api.writeFile(selectedFile.path, editorContent, true)
      setOriginalContent(editorContent)
      setUnsavedFiles(prev => {
        const next = new Set(prev)
        next.delete(selectedFile.path)
        return next
      })
      setSaveStatus('Saved!')
      setLogs(prev => [...prev, { type: 'success', message: `Saved: ${selectedFile.path}` }])
      // Refresh file explorer in case file was newly created
      refreshFileExplorer()
      setTimeout(() => setSaveStatus(''), 2000)
    } catch (err) {
      console.error('Error saving file:', err)
      setSaveStatus('Save failed')
      setLogs(prev => [...prev, { type: 'error', message: `Failed to save: ${selectedFile.path}` }])
      setTimeout(() => setSaveStatus(''), 3000)
    } finally {
      setIsLoading(false)
    }
  }, [selectedFile, editorContent])

  // Chat panel resize handlers
  const handleResizeMouseDown = useCallback((e) => {
    e.preventDefault()
    setIsResizing(true)
    startXRef.current = e.clientX
    startWidthRef.current = chatWidth
  }, [chatWidth])

  useEffect(() => {
    if (!isResizing) return

    const handleMouseMove = (e) => {
      const delta = startXRef.current - e.clientX
      const newWidth = Math.min(800, Math.max(280, startWidthRef.current + delta))
      setChatWidth(newWidth)
    }

    const handleMouseUp = () => {
      setIsResizing(false)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [isResizing])

  // Explorer panel resize handlers
  const handleExplorerResizeMouseDown = useCallback((e) => {
    e.preventDefault()
    setIsResizingExplorer(true)
    startExplorerXRef.current = e.clientX
    startExplorerWidthRef.current = explorerWidth
  }, [explorerWidth])

  useEffect(() => {
    if (!isResizingExplorer) return

    const handleMouseMove = (e) => {
      const delta = e.clientX - startExplorerXRef.current
      const newWidth = Math.min(600, Math.max(160, startExplorerWidthRef.current + delta))
      setExplorerWidth(newWidth)
    }

    const handleMouseUp = () => {
      setIsResizingExplorer(false)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [isResizingExplorer])

  // Keyboard shortcut for save (Ctrl+S)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault()
        handleSaveFile()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleSaveFile])

  // Create new file
  const handleCreateFile = async () => {
    if (!newFileName.trim()) return
    
    setIsLoading(true)
    try {
      await api.createFile(newFileName, '')
      setLogs(prev => [...prev, { type: 'success', message: `Created: ${newFileName}` }])
      setShowNewFileModal(false)
      setNewFileName('')
      // Refresh file explorer to show new file
      refreshFileExplorer()
    } catch (err) {
      console.error('Error creating file:', err)
      setLogs(prev => [...prev, { type: 'error', message: `Failed to create: ${newFileName}` }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-full bg-[#0d1117]">
      {/* File Explorer */}
      <div className="bg-[#010409] border-r border-[#21262d] flex flex-col shrink-0 relative" style={{ width: explorerWidth }}>
        <div className="h-10 px-4 flex items-center justify-between border-b border-[#21262d]">
          <span className="text-xs font-medium text-[#8b949e] uppercase tracking-wide">Explorer</span>
          <button 
            onClick={() => setShowNewFileModal(true)}
            className="w-5 h-5 flex items-center justify-center text-[#8b949e] hover:text-[#c9d1d9] hover:bg-[#21262d] rounded"
            title="New File"
          >
            +
          </button>
        </div>
        <div className="flex-1 overflow-auto">
          <FileExplorer ref={fileExplorerRef} onFileSelect={handleFileSelect} />
        </div>

        {/* Resize Handle */}
        <div
          ref={resizeExplorerRef}
          onMouseDown={handleExplorerResizeMouseDown}
          className={`absolute right-[-3px] top-0 bottom-0 w-[6px] flex items-center justify-center cursor-col-resize group transition-colors hover:bg-[#388bfd]/30 z-10 ${
            isResizingExplorer ? 'bg-[#388bfd]/40' : 'bg-transparent'
          }`}
          title="Drag to resize explorer"
        >
          <div className={`flex flex-col gap-[2px] transition-opacity ${
            isResizingExplorer ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
          }`}>
            <svg width="6" height="14" viewBox="0 0 6 14" className="text-[#8b949e]">
              <path d="M2 1L0 3.5L2 6" stroke="currentColor" strokeWidth="1.2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M4 8L6 10.5L4 13" stroke="currentColor" strokeWidth="1.2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
        </div>
      </div>

      {/* Main Editor Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Editor Tabs */}
        <div className="h-10 bg-[#010409] border-b border-[#21262d] flex items-center justify-between px-2">
          <div className="flex items-center gap-1 overflow-x-auto flex-1">
            {openFiles.length === 0 ? (
              <span className="text-xs text-[#484f58] px-2">Select a file to edit</span>
            ) : (
              openFiles.map((file) => (
                <div
                  key={file.path}
                  onClick={() => {
                    setSelectedFile(file)
                    loadFileContent(file)
                  }}
                  className={`group flex items-center gap-2 px-3 h-7 rounded text-xs cursor-pointer shrink-0 ${
                    selectedFile?.path === file.path
                      ? 'bg-[#161b22] text-[#c9d1d9]'
                      : 'text-[#8b949e] hover:bg-[#161b22]'
                  }`}
                >
                  <span className="truncate max-w-32">{file.name}</span>
                  {unsavedFiles.has(file.path) && <span className="w-1.5 h-1.5 bg-[#f0883e] rounded-full" />}
                  <button
                    onClick={(e) => { e.stopPropagation(); handleTabClose(file.path) }}
                    className="w-4 h-4 flex items-center justify-center rounded hover:bg-[#21262d] opacity-0 group-hover:opacity-100 text-[#8b949e]"
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>
          
          {/* Save Button & Status */}
          <div className="flex items-center gap-2 shrink-0 ml-2">
            {saveStatus && (
              <span className={`text-xs ${saveStatus === 'Saved!' ? 'text-[#238636]' : saveStatus.includes('failed') ? 'text-[#f85149]' : 'text-[#8b949e]'}`}>
                {saveStatus}
              </span>
            )}
            {selectedFile && unsavedFiles.has(selectedFile.path) && (
              <button
                onClick={handleSaveFile}
                disabled={isLoading}
                className="px-2 py-1 bg-[#238636] hover:bg-[#2ea043] disabled:bg-[#21262d] text-white text-xs rounded font-medium"
              >
                Save
              </button>
            )}
          </div>
        </div>

        {/* Editor Content */}
        <div className="flex-1 overflow-hidden relative">
          {isLoading && (
            <div className="absolute inset-0 bg-[#010409]/80 flex items-center justify-center z-10">
              <div className="text-[#8b949e] text-sm flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-[#8b949e] border-t-transparent rounded-full animate-spin" />
                Loading...
              </div>
            </div>
          )}
          {selectedFile ? (
            <CodeEditor file={selectedFile} value={editorContent} onChange={handleEditorChange} />
          ) : (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-12 h-12 mx-auto mb-3 bg-[#21262d] rounded-lg flex items-center justify-center">
                  <span className="text-[#484f58] text-xl">📄</span>
                </div>
                <p className="text-[#8b949e] text-sm">Select a file from the explorer to view and edit</p>
                <p className="text-[#484f58] text-xs mt-1">Files are loaded from backend workspace</p>
              </div>
            </div>
          )}
        </div>

        {/* Bottom Panel Toggle */}
        <div className="h-8 bg-[#010409] border-t border-[#21262d] flex items-center px-3 gap-4">
          {['Terminal', 'Diff', 'Logs'].map((tab) => (
            <button
              key={tab}
              onClick={() => {
                setActiveTab(tab.toLowerCase())
                setShowBottomPanel(activeTab === tab.toLowerCase() ? !showBottomPanel : true)
              }}
              className={`text-xs transition-colors ${
                showBottomPanel && activeTab === tab.toLowerCase()
                  ? 'text-[#c9d1d9]'
                  : 'text-[#484f58] hover:text-[#8b949e]'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Bottom Panel */}
        {showBottomPanel && (
          <div className="h-48 bg-[#010409] border-t border-[#21262d] overflow-auto">
            {activeTab === 'terminal' && <TerminalView output={terminalOutput} onCommandComplete={handleTerminalCommandComplete} />}
            {activeTab === 'diff' && <DiffViewer data={diffData} />}
            {activeTab === 'logs' && <ToolLogs logs={logs} />}
          </div>
        )}
      </div>

      {/* Chat Panel with Resize Handle */}
      <div className="flex shrink-0" style={{ width: chatWidth }}>
        {/* Resize Handle */}
        <div
          ref={resizeRef}
          onMouseDown={handleResizeMouseDown}
          className={`w-[6px] flex items-center justify-center cursor-col-resize group transition-colors hover:bg-[#388bfd]/30 ${
            isResizing ? 'bg-[#388bfd]/40' : 'bg-[#21262d]/50'
          }`}
          title="Drag to resize chat"
        >
          <div className={`flex flex-col gap-[2px] transition-opacity ${
            isResizing ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
          }`}>
            <svg width="6" height="14" viewBox="0 0 6 14" className="text-[#8b949e]">
              <path d="M2 1L0 3.5L2 6" stroke="currentColor" strokeWidth="1.2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M4 8L6 10.5L4 13" stroke="currentColor" strokeWidth="1.2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
        </div>

        {/* Chat Content */}
        <div className="flex-1 bg-[#010409] border-l border-[#21262d] flex flex-col min-w-0">
          <ChatPanel 
            conversationId={conversationId} 
            onFilesChanged={() => {
              refreshFileExplorer()
              // Auto-reload the active file if it was changed by the AI
              // Only do this if the user hasn't made unsaved changes
              if (selectedFile && !unsavedFiles.has(selectedFile.path)) {
                loadFileContent(selectedFile)
              }
            }}
            onLog={(type, msg) => setLogs(prev => [...prev, { type, message: msg }])}
          />
        </div>
      </div>

      {/* New File Modal */}
      {showNewFileModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#161b22] border border-[#21262d] rounded-lg p-4 w-80">
            <h3 className="text-[#c9d1d9] text-sm font-medium mb-3">Create New File</h3>
            <input
              type="text"
              value={newFileName}
              onChange={(e) => setNewFileName(e.target.value)}
              placeholder="filename.js or path/to/file.js"
              className="w-full px-3 py-2 bg-[#0d1117] border border-[#21262d] rounded text-sm text-[#c9d1d9] placeholder-[#484f58] focus:outline-none focus:border-[#388bfd] mb-3"
              autoFocus
              onKeyDown={(e) => e.key === 'Enter' && handleCreateFile()}
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => { setShowNewFileModal(false); setNewFileName('') }}
                className="px-3 py-1.5 text-[#8b949e] hover:text-[#c9d1d9] text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateFile}
                disabled={!newFileName.trim() || isLoading}
                className="px-3 py-1.5 bg-[#238636] hover:bg-[#2ea043] disabled:bg-[#21262d] disabled:text-[#484f58] text-white text-sm rounded font-medium"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
