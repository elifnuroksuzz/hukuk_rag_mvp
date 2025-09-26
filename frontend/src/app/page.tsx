'use client'

import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Send, 
  Upload, 
  FileText, 
  MessageSquare, 
  Settings,
  Trash2,
  Download,
  CheckCircle,
  AlertCircle,
  Loader2,
  Scale,
  BookOpen,
  Search,
  Clock,
  Users,
  BarChart3
} from 'lucide-react'
import toast, { Toaster } from 'react-hot-toast'

const API_BASE_URL = 'http://localhost:8000'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  confidence?: number
  timestamp: string
}

interface Source {
  filename: string
  similarity: string
  preview: string
  chunk_index?: number
}

interface SystemStats {
  total_documents: number
  llm_model: string
  uptime: string
  collection_name: string
  embedding_model: string
}

interface DocumentInfo {
  filename: string
  chunks: number
}

export default function HukukRAGApp() {
  // State Management
  const [messages, setMessages] = useState<Message[]>([])
  const [inputText, setInputText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null)
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [activeTab, setActiveTab] = useState<'chat' | 'upload' | 'stats'>('chat')
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Fetch system stats on load
  useEffect(() => {
    fetchSystemStats()
    fetchDocuments()
    
    // Health check on mount
    checkHealth()
  }, [])

  const checkHealth = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`)
      if (response.data.status === 'healthy') {
        toast.success('Sistem bağlantısı başarılı')
      } else {
        toast.error('Sistem sağlık kontrolü başarısız')
      }
    } catch (error) {
      toast.error('API bağlantısı kurulamadı')
    }
  }

  const fetchSystemStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/stats`)
      setSystemStats(response.data)
    } catch (error) {
      console.error('Stats fetch error:', error)
    }
  }

  const fetchDocuments = async () => {
    try {
      // Bu endpoint'in backend'de olması gerekiyor
      const response = await axios.get(`${API_BASE_URL}/documents`)
      setDocuments(response.data.documents || [])
    } catch (error) {
      // Demo verisi
      setDocuments([
        { filename: 'tck.pdf', chunks: 247 },
        { filename: 'tmk.pdf', chunks: 490 },
        { filename: 'icra_iflas_kanunu.pdf', chunks: 158 },
        { filename: 'borçlar_kanunu.pdf', chunks: 322 }
      ])
    }
  }

  const sendMessage = async () => {
    if (!inputText.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputText.trim(),
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputText('')
    setIsLoading(true)

    try {
      // Prepare chat history for API
      const chatHistory = messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }))

      const response = await axios.post(`${API_BASE_URL}/query`, {
        question: userMessage.content,
        chat_history: chatHistory,
        max_sources: 5
      })

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
        confidence: response.data.confidence,
        timestamp: response.data.timestamp
      }

      setMessages(prev => [...prev, assistantMessage])
      
      // Update stats after successful query
      fetchSystemStats()
      
    } catch (error: any) {
      toast.error('Sorgu işlenirken hata oluştu')
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Üzgünüm, sorunuzu işlerken bir hata oluştu. Lütfen tekrar deneyin.',
        timestamp: new Date().toISOString()
      }
      
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return

    setIsUploading(true)
    
    const formData = new FormData()
    Array.from(files).forEach(file => {
      formData.append('files', file)
    })

    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      const { processed_files, failed_files, total_chunks } = response.data

      if (processed_files.length > 0) {
        toast.success(`${processed_files.length} dosya başarıyla yüklendi (${total_chunks} parça)`)
        fetchSystemStats() // Refresh stats
        fetchDocuments() // Refresh document list
      }

      if (failed_files.length > 0) {
        toast.error(`${failed_files.length} dosya yüklenemedi`)
      }

    } catch (error: any) {
      toast.error('Dosya yükleme başarısız')
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const clearChat = () => {
    setMessages([])
    toast.success('Sohbet temizlendi')
  }

  const clearDatabase = async () => {
    if (!confirm('Tüm belgeler silinecek. Emin misiniz?')) return

    try {
      await axios.delete(`${API_BASE_URL}/documents`)
      toast.success('Veritabanı temizlendi')
      fetchSystemStats()
      fetchDocuments()
    } catch (error) {
      toast.error('Veritabanı temizlenemedi')
    }
  }

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return 'text-gray-500'
    if (confidence >= 0.7) return 'text-green-600'
    if (confidence >= 0.5) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getConfidenceText = (confidence?: number) => {
    if (!confidence) return 'Bilinmiyor'
    if (confidence >= 0.7) return 'Yüksek'
    if (confidence >= 0.5) return 'Orta'
    return 'Düşük'
  }

  // Quick questions
  const quickQuestions = [
    "Türk Ceza Kanunu'nun amacı nedir?",
    "Hakim kanunda hüküm bulamazsa ne yapar?",
    "İcra takibi nasıl başlar?",
    "Ödeme emrine itiraz edilebilir mi?",
    "Medeni Kanun ne zaman yürürlüğe girdi?"
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800">
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-md border-b border-white/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <Scale className="h-8 w-8 text-blue-400" />
              <div>
                <h1 className="text-xl font-bold text-white">Hukuk RAG Asistanı</h1>
                <p className="text-xs text-blue-300">Türk Hukuk Belgeleri AI Analizi</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {systemStats && (
                <div className="hidden md:flex items-center space-x-4 text-sm text-blue-200">
                  <div className="flex items-center space-x-1">
                    <FileText className="h-4 w-4" />
                    <span>{systemStats.total_documents.toLocaleString()} belge</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Clock className="h-4 w-4" />
                    <span>{systemStats.uptime}</span>
                  </div>
                </div>
              )}
              
              <div className="flex space-x-2">
                <button
                  onClick={() => setActiveTab('chat')}
                  className={`p-2 rounded-lg transition-colors ${
                    activeTab === 'chat' 
                      ? 'bg-blue-500 text-white' 
                      : 'text-blue-300 hover:bg-white/10'
                  }`}
                >
                  <MessageSquare className="h-5 w-5" />
                </button>
                <button
                  onClick={() => setActiveTab('upload')}
                  className={`p-2 rounded-lg transition-colors ${
                    activeTab === 'upload' 
                      ? 'bg-blue-500 text-white' 
                      : 'text-blue-300 hover:bg-white/10'
                  }`}
                >
                  <Upload className="h-5 w-5" />
                </button>
                <button
                  onClick={() => setActiveTab('stats')}
                  className={`p-2 rounded-lg transition-colors ${
                    activeTab === 'stats' 
                      ? 'bg-blue-500 text-white' 
                      : 'text-blue-300 hover:bg-white/10'
                  }`}
                >
                  <BarChart3 className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-140px)]">
          
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6 h-full overflow-y-auto">
              
              {activeTab === 'chat' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4">Hızlı Sorular</h3>
                    <div className="space-y-2">
                      {quickQuestions.map((question, index) => (
                        <button
                          key={index}
                          onClick={() => setInputText(question)}
                          className="w-full text-left text-sm text-blue-200 hover:text-white p-3 rounded-lg hover:bg-white/10 transition-colors"
                        >
                          {question}
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  <div className="pt-4 border-t border-white/20">
                    <button
                      onClick={clearChat}
                      className="w-full flex items-center justify-center space-x-2 p-3 bg-red-500/20 text-red-200 hover:bg-red-500/30 rounded-lg transition-colors"
                    >
                      <Trash2 className="h-4 w-4" />
                      <span>Sohbeti Temizle</span>
                    </button>
                  </div>
                </div>
              )}

              {activeTab === 'upload' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4">Belge Yükleme</h3>
                    
                    <div className="space-y-4">
                      <div
                        className="border-2 border-dashed border-blue-400/50 rounded-lg p-6 text-center hover:border-blue-400 transition-colors cursor-pointer"
                        onClick={() => fileInputRef.current?.click()}
                      >
                        <Upload className="h-8 w-8 text-blue-400 mx-auto mb-2" />
                        <p className="text-blue-200 text-sm">
                          PDF, DOCX veya TXT dosyalarını yükleyin
                        </p>
                        <p className="text-blue-300 text-xs mt-1">
                          Tıklayın veya dosyaları sürükleyin
                        </p>
                      </div>
                      
                      <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        accept=".pdf,.docx,.txt"
                        onChange={(e) => handleFileUpload(e.target.files)}
                        className="hidden"
                      />
                      
                      {isUploading && (
                        <div className="flex items-center justify-center space-x-2 text-blue-300">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span>Yükleniyor...</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="pt-4 border-t border-white/20">
                    <button
                      onClick={clearDatabase}
                      className="w-full flex items-center justify-center space-x-2 p-3 bg-red-500/20 text-red-200 hover:bg-red-500/30 rounded-lg transition-colors"
                    >
                      <Trash2 className="h-4 w-4" />
                      <span>Veritabanını Temizle</span>
                    </button>
                  </div>
                </div>
              )}

              {activeTab === 'stats' && systemStats && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4">Sistem Durumu</h3>
                    
                    <div className="space-y-4">
                      <div className="bg-white/5 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <span className="text-blue-200 text-sm">Toplam Belge</span>
                          <span className="text-white font-semibold">
                            {systemStats.total_documents.toLocaleString()}
                          </span>
                        </div>
                      </div>
                      
                      <div className="bg-white/5 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <span className="text-blue-200 text-sm">Çalışma Süresi</span>
                          <span className="text-white font-semibold">{systemStats.uptime}</span>
                        </div>
                      </div>
                      
                      <div className="bg-white/5 rounded-lg p-4">
                        <div className="text-blue-200 text-sm mb-2">LLM Model</div>
                        <div className="text-white text-xs font-mono">
                          {systemStats.llm_model}
                        </div>
                      </div>
                      
                      <div className="bg-white/5 rounded-lg p-4">
                        <div className="text-blue-200 text-sm mb-2">Embedding Model</div>
                        <div className="text-white text-xs">
                          Multilingual MiniLM
                        </div>
                      </div>
                    </div>

                    <div className="mt-6">
                      <h4 className="text-md font-medium text-white mb-3">İşlenen Belgeler</h4>
                      <div className="bg-white/5 rounded-lg p-4 max-h-40 overflow-y-auto">
                        <div className="space-y-2">
                          {documents.length > 0 ? (
                            documents.map((doc, index) => (
                              <div key={index} className="flex items-center justify-between text-sm">
                                <span className="text-blue-200 flex items-center">
                                  <FileText className="h-4 w-4 mr-2" />
                                  {doc.filename}
                                </span>
                                <span className="text-blue-400">
                                  {doc.chunks} parça
                                </span>
                              </div>
                            ))
                          ) : (
                            <div className="text-blue-300 text-sm text-center py-4">
                              Henüz belge yüklenmemiş
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
            </div>
          </div>

          {/* Main Chat Area */}
          <div className="lg:col-span-3">
            <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 h-full flex flex-col">
              
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                <AnimatePresence>
                  {messages.map((message) => (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`max-w-4xl ${message.role === 'user' ? 'bg-blue-600' : 'bg-white/10'} rounded-lg p-6 shadow-lg`}>
                        <div className={`${message.role === 'user' ? 'text-white' : 'text-blue-100'}`}>
                          <div className="whitespace-pre-wrap break-words leading-relaxed text-sm">
                            {message.content}
                          </div>
                        </div>
                        
                        {message.role === 'assistant' && (
                          <div className="mt-4 space-y-3">
                            {message.confidence && (
                              <div className="flex items-center space-x-2">
                                <span className="text-xs text-blue-300">Güven:</span>
                                <span className={`text-xs font-semibold ${getConfidenceColor(message.confidence)}`}>
                                  {getConfidenceText(message.confidence)} ({message.confidence.toFixed(2)})
                                </span>
                              </div>
                            )}
                            
                            {message.sources && message.sources.length > 0 && (
                              <div className="border-t border-white/20 pt-3 mt-3">
                                <div className="text-sm font-medium text-blue-300 mb-3">
                                  Kaynaklar ({message.sources.length}):
                                </div>
                                <div className="grid gap-3">
                                  {message.sources.map((source, index) => (
                                    <div key={index} className="bg-white/5 rounded-lg p-4 border border-white/10">
                                      <div className="flex items-center justify-between mb-2">
                                        <span className="text-sm font-semibold text-blue-200 flex items-center">
                                          <FileText className="h-4 w-4 mr-2" />
                                          {source.filename}
                                        </span>
                                        <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded">
                                          Benzerlik: {source.similarity}
                                        </span>
                                      </div>
                                      <p className="text-sm text-blue-100 leading-relaxed line-clamp-none">
                                        {source.preview}
                                      </p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                        
                        <div className="mt-2 text-xs text-blue-400">
                          {new Date(message.timestamp).toLocaleTimeString('tr-TR')}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
                
                {isLoading && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex justify-start"
                  >
                    <div className="bg-white/10 rounded-lg p-4">
                      <div className="flex items-center space-x-2">
                        <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
                        <span className="text-blue-200">Cevap hazırlanıyor...</span>
                      </div>
                    </div>
                  </motion.div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="border-t border-white/20 p-4">
                <div className="flex space-x-4">
                  <input
                    type="text"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Hukuki sorunuzu sorun..."
                    disabled={isLoading}
                    className="flex-1 bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button
                    onClick={sendMessage}
                    disabled={isLoading || !inputText.trim()}
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg transition-colors flex items-center space-x-2"
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                    <span>Gönder</span>
                  </button>
                </div>
              </div>
              
            </div>
          </div>
          
        </div>
      </div>
    </div>
  )
}