import React, { useState, useEffect, forwardRef, useImperativeHandle } from 'react'
import { useFiles } from '../hooks/useChat'
import api from '../services/api'

const FileExplorer = forwardRef(function FileExplorer({ onFileSelect }, ref) {
  const { files, isLoading, error, listFiles } = useFiles()
  const [expandedFolders, setExpandedFolders] = useState(new Set())
  const [selectedFile, setSelectedFile] = useState(null)
  const [folderStructure, setFolderStructure] = useState({})

  // Expose refresh method to parent components
  useImperativeHandle(ref, () => ({
    refresh: () => {
      refreshFiles()
    }
  }))

  useEffect(() => {
    loadInitialFiles()
  }, [])

  const loadInitialFiles = async () => {
    try {
      await listFiles('.')
    } catch (err) {
      console.error('Error loading files:', err)
    }
  }

  const refreshFiles = async () => {
    // Reload root files
    await loadInitialFiles()
    // Reload all currently expanded folders
    for (const folderPath of expandedFolders) {
      try {
        const response = await api.listFiles(folderPath)
        setFolderStructure(prev => ({
          ...prev,
          [folderPath]: response.files
        }))
      } catch (err) {
        console.error('Error refreshing folder:', folderPath, err)
      }
    }
  }

  const toggleFolder = (path) => {
    const newExpanded = new Set(expandedFolders)
    if (newExpanded.has(path)) {
      newExpanded.delete(path)
    } else {
      newExpanded.add(path)
      loadFolder(path)
    }
    setExpandedFolders(newExpanded)
  }

  const loadFolder = async (path) => {
    try {
      const response = await api.listFiles(path)
      setFolderStructure(prev => ({
        ...prev,
        [path]: response.files
      }))
    } catch (err) {
      console.error('Error loading folder:', err)
    }
  }

  const handleFileClick = (file) => {
    setSelectedFile(file)
    if (file.is_file && onFileSelect) {
      onFileSelect(file)
    }
  }

  const getFileIcon = (filename, isFolder) => {
    if (isFolder) return '▸'
    const ext = filename.split('.').pop()?.toLowerCase()
    const colors = {
      'js': 'text-yellow-400',
      'jsx': 'text-[#61dafb]',
      'ts': 'text-blue-400',
      'tsx': 'text-[#61dafb]',
      'py': 'text-[#3776ab]',
      'json': 'text-yellow-300',
      'md': 'text-[#8b949e]',
      'css': 'text-[#563d7c]',
      'html': 'text-orange-400',
    }
    return <span className={colors[ext] || 'text-[#8b949e]'}>◆</span>
  }

  const renderFileTree = (items, depth = 0) => {
    if (!items) return null
    
    return (
      <div style={{ paddingLeft: depth > 0 ? '12px' : '0' }}>
        {items.map((item) => {
          const isFolder = !item.is_file
          const isExpanded = expandedFolders.has(item.path)
          const isSelected = selectedFile?.path === item.path

          return (
            <div key={item.path}>
              <button
                onClick={() => isFolder ? toggleFolder(item.path) : handleFileClick(item)}
                className={`w-full flex items-center gap-1.5 px-2 py-1 text-left text-xs rounded transition-colors ${
                  isSelected
                    ? 'bg-[#1f6feb]/20 text-[#c9d1d9]'
                    : 'text-[#8b949e] hover:bg-[#161b22] hover:text-[#c9d1d9]'
                }`}
              >
                {isFolder && (
                  <span className={`text-[10px] text-[#484f58] transition-transform ${isExpanded ? 'rotate-90' : ''}`}>
                    ▶
                  </span>
                )}
                {!isFolder && <span className="w-2.5" />}
                {!isFolder && getFileIcon(item.name, false)}
                <span className="truncate">{item.name}</span>
              </button>

              {isFolder && isExpanded && folderStructure[item.path] && (
                renderFileTree(folderStructure[item.path], depth + 1)
              )}
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className="h-full overflow-auto py-2 px-1">
      {isLoading && files.length === 0 ? (
        <div className="px-3 py-4 text-[#484f58] text-xs text-center">Loading...</div>
      ) : error ? (
        <div className="px-3 py-4 text-[#f85149] text-xs text-center">{error}</div>
      ) : files.length === 0 ? (
        <div className="px-3 py-4 text-[#484f58] text-xs text-center">No files</div>
      ) : (
        renderFileTree(files)
      )}
    </div>
  )
})

export default FileExplorer
