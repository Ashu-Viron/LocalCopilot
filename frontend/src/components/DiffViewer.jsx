import React, { useState, useEffect } from 'react'

export default function DiffViewer({ diff = null }) {
  const [expandedFiles, setExpandedFiles] = useState(new Set())

  const toggleFile = (filePath) => {
    const newExpanded = new Set(expandedFiles)
    if (newExpanded.has(filePath)) {
      newExpanded.delete(filePath)
    } else {
      newExpanded.add(filePath)
    }
    setExpandedFiles(newExpanded)
  }

  if (!diff) {
    return (
      <div className="flex flex-col h-full bg-[#010409]">
        <div className="px-4 py-2 border-b border-[#21262d] bg-[#0d1117]">
          <h3 className="text-xs font-medium text-[#8b949e]">Diff</h3>
        </div>
        <div className="flex-1 flex items-center justify-center text-[#484f58]">
          <p className="text-sm">No changes to review</p>
        </div>
      </div>
    )
  }

  const fileDiffs = Array.isArray(diff) ? diff : [diff]

  return (
    <div className="flex flex-col h-full bg-[#010409]">
      {/* Header */}
      <div className="px-4 py-2 border-b border-[#21262d] bg-[#0d1117]">
        <h3 className="text-xs font-medium text-[#8b949e]">
          Diff — {fileDiffs.length} file(s) changed
        </h3>
      </div>

      {/* Diff Content */}
      <div className="flex-1 overflow-y-auto">
        {fileDiffs.map((fileDiff, fileIdx) => (
          <div key={fileIdx} className="border-b border-[#21262d]">
            {/* File Header */}
            <div
              onClick={() => toggleFile(fileDiff.file_path)}
              className="px-4 py-2 bg-[#161b22] cursor-pointer hover:bg-[#21262d] flex items-center justify-between"
            >
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <span className={`text-[#484f58] text-xs transition-transform ${expandedFiles.has(fileDiff.file_path) ? 'rotate-90' : ''}`}>
                  ▶
                </span>
                <span className="text-sm font-mono text-[#c9d1d9] truncate">{fileDiff.file_path}</span>
              </div>
              <div className="flex gap-3 ml-4 text-xs font-mono">
                <span className="text-[#3fb950]">+{fileDiff.additions || 0}</span>
                <span className="text-[#f85149]">-{fileDiff.deletions || 0}</span>
              </div>
            </div>

            {/* Diff Changes */}
            {expandedFiles.has(fileDiff.file_path) && (
              <div className="bg-[#0d1117]">
                {fileDiff.changes && fileDiff.changes.length > 0 ? (
                  <div className="divide-y divide-[#21262d]">
                    {fileDiff.changes.map((change, changeIdx) => (
                      <div key={changeIdx} className="px-4 py-0.5 font-mono text-xs">
                        {change.type === 'add' && (
                          <div className="text-[#3fb950] bg-[#1a3329]">
                            + {change.new_content}
                          </div>
                        )}
                        {change.type === 'remove' && (
                          <div className="text-[#f85149] bg-[#3d1e20]">
                            - {change.old_content}
                          </div>
                        )}
                        {change.type === 'modify' && (
                          <>
                            <div className="text-[#f85149] bg-[#3d1e20]">
                              - {change.old_content}
                            </div>
                            <div className="text-[#3fb950] bg-[#1a3329]">
                              + {change.new_content}
                            </div>
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="px-4 py-2 text-[#484f58] text-sm">No changes</div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer Stats */}
      <div className="px-4 py-1 border-t border-[#21262d] bg-[#0d1117] text-xs text-[#8b949e] flex gap-4">
        <div className="flex items-center gap-1">
          <span className="text-[#3fb950]">●</span>
          <span>+{fileDiffs.reduce((sum, f) => sum + (f.additions || 0), 0)}</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-[#f85149]">●</span>
          <span>-{fileDiffs.reduce((sum, f) => sum + (f.deletions || 0), 0)}</span>
        </div>
      </div>
    </div>
  )
}
