import React, { useState, useEffect } from 'react'
import api from '../services/api'

export default function SettingsPage() {
  const [config, setConfig] = useState({})
  const [loading, setLoading] = useState(true)
  const [saved, setSaved] = useState(false)
  const [availableModels, setAvailableModels] = useState({})
  const [modelsLoading, setModelsLoading] = useState(true)

  useEffect(() => {
    loadConfig()
    loadAvailableModels()
  }, [])

  const loadConfig = async () => {
    try {
      const data = await api.getConfig()
      setConfig(data || {})
    } catch (err) {
      console.error('Failed to load config:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadAvailableModels = async () => {
    try {
      const models = await api.getAvailableModels()
      setAvailableModels(models || {})
    } catch (err) {
      console.error('Failed to load models:', err)
      // Fallback to some default models
      setAvailableModels({
        'gemini-2.5-flash-lite': 'google/gemini-2.5-flash-lite',
        'gpt-4': 'openai/gpt-4',
        'gpt-3.5-turbo': 'openai/gpt-3.5-turbo'
      })
    } finally {
      setModelsLoading(false)
    }
  }

  const handleChange = (key, value) => {
    setConfig({ ...config, [key]: value })
    setSaved(false)
  }

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  if (loading) {
    return (
      <div className="h-full bg-[#0d1117] flex items-center justify-center">
        <span className="text-[#484f58] text-sm">Loading...</span>
      </div>
    )
  }

  return (
    <div className="h-full overflow-auto bg-[#0d1117]">
      <div className="max-w-2xl mx-auto px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-[#c9d1d9] mb-1">Settings</h1>
          <p className="text-sm text-[#8b949e]">Configure your LocalCopilot preferences</p>
        </div>

        {/* AI Settings */}
        <section className="mb-8">
          <h2 className="text-xs font-medium text-[#8b949e] uppercase tracking-wide mb-3">AI Model</h2>
          <div className="bg-[#161b22] border border-[#21262d] rounded-lg divide-y divide-[#21262d]">
            <div className="p-4 flex items-center justify-between">
              <div>
                <div className="text-sm text-[#c9d1d9]">Model</div>
                <div className="text-xs text-[#484f58] mt-0.5">Select the AI model to use</div>
              </div>
              <select
                value={config.llm_model || ''}
                onChange={(e) => handleChange('llm_model', e.target.value)}
                className="px-3 py-1.5 bg-[#0d1117] border border-[#21262d] rounded-md text-sm text-[#c9d1d9] focus:outline-none focus:border-[#388bfd] min-w-[180px]"
                disabled={modelsLoading}
              >
                {modelsLoading ? (
                  <option value="">Loading models...</option>
                ) : Object.keys(availableModels).length === 0 ? (
                  <option value="">No models available</option>
                ) : (
                  Object.entries(availableModels).map(([modelId, modelPath]) => (
                    <option key={modelId} value={modelId}>
                      {modelId}
                    </option>
                  ))
                )}
              </select>
            </div>
            <div className="p-4 flex items-center justify-between">
              <div>
                <div className="text-sm text-[#c9d1d9]">Temperature</div>
                <div className="text-xs text-[#484f58] mt-0.5">Lower values are more deterministic</div>
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={config.temperature || 0.7}
                  onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
                  className="w-24"
                />
                <span className="text-xs text-[#8b949e] w-8">{(config.temperature || 0.7).toFixed(1)}</span>
              </div>
            </div>
          </div>
        </section>

        {/* Editor Settings */}
        <section className="mb-8">
          <h2 className="text-xs font-medium text-[#8b949e] uppercase tracking-wide mb-3">Editor</h2>
          <div className="bg-[#161b22] border border-[#21262d] rounded-lg divide-y divide-[#21262d]">
            <div className="p-4 flex items-center justify-between">
              <div>
                <div className="text-sm text-[#c9d1d9]">Font Size</div>
                <div className="text-xs text-[#484f58] mt-0.5">Code editor font size</div>
              </div>
              <input
                type="number"
                min="10"
                max="24"
                value={config.font_size || 14}
                onChange={(e) => handleChange('font_size', parseInt(e.target.value))}
                className="w-20 px-3 py-1.5 bg-[#0d1117] border border-[#21262d] rounded-md text-sm text-[#c9d1d9] focus:outline-none focus:border-[#388bfd]"
              />
            </div>
            <div className="p-4 flex items-center justify-between">
              <div>
                <div className="text-sm text-[#c9d1d9]">Auto Save</div>
                <div className="text-xs text-[#484f58] mt-0.5">Automatically save files</div>
              </div>
              <button
                onClick={() => handleChange('auto_save', !config.auto_save)}
                className={`w-10 h-5 rounded-full transition-colors ${
                  config.auto_save ? 'bg-[#238636]' : 'bg-[#21262d]'
                }`}
              >
                <div className={`w-4 h-4 bg-white rounded-full transition-transform mx-0.5 ${
                  config.auto_save ? 'translate-x-5' : ''
                }`} />
              </button>
            </div>
          </div>
        </section>

        {/* Workspace Info */}
        <section className="mb-8">
          <h2 className="text-xs font-medium text-[#8b949e] uppercase tracking-wide mb-3">Workspace</h2>
          <div className="bg-[#161b22] border border-[#21262d] rounded-lg p-4">
            <div className="text-sm text-[#c9d1d9] mb-1">Directory</div>
            <div className="text-xs text-[#484f58] font-mono">{config.workspace_dir || './workspace'}</div>
          </div>
        </section>

        {/* Save Button */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-[#238636] hover:bg-[#2ea043] text-white rounded-md text-sm font-medium transition-colors"
          >
            Save changes
          </button>
          {saved && <span className="text-xs text-[#238636]">Saved</span>}
        </div>
      </div>
    </div>
  )
}
