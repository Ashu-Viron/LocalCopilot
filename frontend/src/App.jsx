import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navigation from './components/Navigation'
import HomePage from './pages/HomePage'
import EditorPage from './pages/EditorPage'
import ChatPage from './pages/ChatPage'
import SettingsPage from './pages/SettingsPage'


export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-[#010409]">
        <Navigation />
        <main className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/editor" element={<EditorPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
