import React, { useEffect, useRef, useState } from 'react'

export default function CodeEditor({ file = null, value = '', onChange }) {
  const editorRef = useRef(null)
  const [content, setContent] = useState(value)

  useEffect(() => {
    setContent(value)
  }, [value, file])

  const getLanguage = (filename) => {
    if (!filename) return 'text'
    const ext = filename.split('.').pop()?.toLowerCase()
    const langs = { js: 'JavaScript', jsx: 'JSX', ts: 'TypeScript', tsx: 'TSX', py: 'Python', json: 'JSON', md: 'Markdown', css: 'CSS', html: 'HTML' }
    return langs[ext] || 'Text'
  }

  const handleChange = (e) => {
    const newContent = e.target.value
    setContent(newContent)
    if (onChange) onChange(newContent)
  }

  if (!file) {
    return null
  }

  return (
    <div className="flex flex-col h-full bg-[#0d1117]">
      <textarea
        ref={editorRef}
        value={content}
        onChange={handleChange}
        className="flex-1 w-full bg-[#0d1117] text-[#c9d1d9] p-4 font-mono text-sm resize-none focus:outline-none leading-relaxed"
        spellCheck="false"
        placeholder="Start typing..."
      />
      <div className="h-6 px-3 border-t border-[#21262d] bg-[#010409] flex items-center justify-between text-[11px] text-[#484f58]">
        <span>{getLanguage(file?.name)}</span>
        <span>Ln {content.split('\n').length}, Col 1</span>
      </div>
    </div>
  )
}
