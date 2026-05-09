import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

// Map common language aliases
const languageMap = {
  'js': 'javascript',
  'ts': 'typescript',
  'py': 'python',
  'rb': 'ruby',
  'sh': 'bash',
  'shell': 'bash',
  'yml': 'yaml',
  'dockerfile': 'docker',
  'plaintext': 'text',
  '': 'text'
}

// Detect file name from content or preceding text
const extractFileName = (content, language) => {
  // Check for common file patterns at the start
  const filePatterns = [
    /^\/\/\s*(.+\.\w+)\s*$/m,           // // filename.ext
    /^#\s*(.+\.\w+)\s*$/m,              // # filename.ext
    /^\/\*\s*(.+\.\w+)\s*\*\/\s*$/m,    // /* filename.ext */
    /^<!--\s*(.+\.\w+)\s*-->\s*$/m,     // <!-- filename.ext -->
  ]
  
  for (const pattern of filePatterns) {
    const match = content.match(pattern)
    if (match) {
      return match[1]
    }
  }
  
  return null
}

// Code block with copy button and optional file header
const CodeBlock = ({ language, children, fileName }) => {
  const [copied, setCopied] = useState(false)
  const code = String(children).replace(/\n$/, '')
  const normalizedLang = languageMap[language?.toLowerCase()] || language || 'text'
  
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }
  
  return (
    <div className="code-block-container my-3 rounded-lg overflow-hidden border border-gray-700">
      {/* Header with language/filename and copy button */}
      <div className="code-header flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center gap-2">
          {fileName && (
            <span className="text-blue-400 text-sm font-medium flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              {fileName}
            </span>
          )}
          <span className="text-gray-400 text-xs uppercase">{normalizedLang}</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 px-2 py-1 text-xs text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
        >
          {copied ? (
            <>
              <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-green-400">Copied!</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Copy
            </>
          )}
        </button>
      </div>
      
      {/* Code content */}
      <SyntaxHighlighter
        language={normalizedLang}
        style={oneDark}
        customStyle={{
          margin: 0,
          padding: '1rem',
          background: '#1e1e1e',
          fontSize: '0.875rem',
          lineHeight: '1.5',
        }}
        showLineNumbers={code.split('\n').length > 3}
        wrapLongLines={true}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  )
}

// Inline code styling
const InlineCode = ({ children }) => {
  return (
    <code className="inline-code px-1.5 py-0.5 mx-0.5 bg-gray-700 text-pink-400 rounded text-sm font-mono">
      {children}
    </code>
  )
}

// Pre-process content to detect file names before code blocks
const preprocessContent = (content) => {
  if (!content) return ''
  
  // Pattern to detect "filename.ext:" or "filename.ext" followed by code block
  const fileHeaderPattern = /(?:^|\n)([a-zA-Z0-9_\-\/]+\.[a-zA-Z0-9]+):?\s*\n(```[\s\S]*?```)/g
  
  // Replace with a special marker that we'll handle in rendering
  return content.replace(fileHeaderPattern, (match, fileName, codeBlock) => {
    // Add the filename as a data attribute in the code fence
    return `\n\`\`\`{filename="${fileName}"}${codeBlock.slice(3)}`
  })
}

const MarkdownRenderer = ({ content, className = '' }) => {
  if (!content) return null
  
  // Track file context for code blocks
  let lastMentionedFile = null
  
  // Check if text before code block mentions a file
  const findFileContext = (text) => {
    if (!text) return null
    
    // Look for file mentions in patterns like "cat add.c", "file add.c", "in add.c", etc.
    const filePatterns = [
      /(?:cat|show|view|open|read|file|in)\s+([a-zA-Z0-9_\-\/]+\.[a-zA-Z0-9]+)/i,
      /`([a-zA-Z0-9_\-\/]+\.[a-zA-Z0-9]+)`/,
      /([a-zA-Z0-9_\-\/]+\.[a-zA-Z0-9]+):/,
    ]
    
    for (const pattern of filePatterns) {
      const match = text.match(pattern)
      if (match) {
        return match[1]
      }
    }
    return null
  }
  
  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Code blocks
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '')
            const language = match ? match[1] : ''
            
            if (!inline && (match || String(children).includes('\n'))) {
              // Extract filename from code content or use context
              const codeContent = String(children)
              const extractedFile = extractFileName(codeContent, language)
              const fileName = extractedFile || lastMentionedFile
              
              // Clear file context after using it
              if (lastMentionedFile) {
                lastMentionedFile = null
              }
              
              return (
                <CodeBlock language={language} fileName={fileName}>
                  {children}
                </CodeBlock>
              )
            }
            
            return <InlineCode {...props}>{children}</InlineCode>
          },
          
          // Paragraphs - check for file mentions
          p({ children, ...props }) {
            // Convert children to string to check for file mentions
            const text = React.Children.toArray(children)
              .map(child => typeof child === 'string' ? child : '')
              .join('')
            
            const foundFile = findFileContext(text)
            if (foundFile) {
              lastMentionedFile = foundFile
            }
            
            return (
              <p className="my-2 leading-relaxed" {...props}>
                {children}
              </p>
            )
          },
          
          // Headers
          h1: ({ children }) => <h1 className="text-2xl font-bold mt-4 mb-2 text-white">{children}</h1>,
          h2: ({ children }) => <h2 className="text-xl font-bold mt-3 mb-2 text-white">{children}</h2>,
          h3: ({ children }) => <h3 className="text-lg font-semibold mt-3 mb-1 text-white">{children}</h3>,
          h4: ({ children }) => <h4 className="text-base font-semibold mt-2 mb-1 text-gray-200">{children}</h4>,
          
          // Lists
          ul: ({ children }) => <ul className="list-disc list-inside my-2 ml-4 space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal list-inside my-2 ml-4 space-y-1">{children}</ol>,
          li: ({ children }) => <li className="text-gray-300">{children}</li>,
          
          // Blockquotes
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-blue-500 pl-4 my-3 italic text-gray-400 bg-gray-800/50 py-2 rounded-r">
              {children}
            </blockquote>
          ),
          
          // Links
          a: ({ href, children }) => (
            <a 
              href={href} 
              className="text-blue-400 hover:text-blue-300 underline" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              {children}
            </a>
          ),
          
          // Tables
          table: ({ children }) => (
            <div className="overflow-x-auto my-3">
              <table className="min-w-full border border-gray-700 rounded">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-gray-800">{children}</thead>,
          tbody: ({ children }) => <tbody className="divide-y divide-gray-700">{children}</tbody>,
          tr: ({ children }) => <tr className="hover:bg-gray-800/50">{children}</tr>,
          th: ({ children }) => <th className="px-4 py-2 text-left text-sm font-semibold text-gray-300">{children}</th>,
          td: ({ children }) => <td className="px-4 py-2 text-sm text-gray-400">{children}</td>,
          
          // Horizontal rule
          hr: () => <hr className="my-4 border-gray-700" />,
          
          // Strong/Bold
          strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
          
          // Emphasis/Italic
          em: ({ children }) => <em className="italic text-gray-300">{children}</em>,
          
          // Strikethrough
          del: ({ children }) => <del className="line-through text-gray-500">{children}</del>,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

export default MarkdownRenderer
