import React, { useState } from 'react'
import axios from 'axios'

interface SymbolResponse {
  company_name: string
  symbol: string | null
  success: boolean
  confidence: number | null
  source: string
  timestamp: string
}

interface EnrichmentResult {
  message: string
  output_file: string | null
  rows_processed: number
  rows_updated: number
  rows_failed: number
  processing_time_seconds: number
  success_rate: number
  timestamp: string
}

interface CompanyData {
  [key: string]: string
}

interface ErrorResult {
  error: string
}

type UploadResult = EnrichmentResult | ErrorResult

function App() {
  const [activeTab, setActiveTab] = useState<'single' | 'csv'>('single')
  const [companyName, setCompanyName] = useState('')
  const [singleResult, setSingleResult] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [csvResult, setCsvResult] = useState<EnrichmentResult | null>(null)
  const [resultData, setResultData] = useState<CompanyData[]>([])
  const [columns, setColumns] = useState<string[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleSingleLookup = async () => {
    if (!companyName.trim()) {
      setError('Please enter a company name')
      return
    }

    setUploading(true)
    setError(null)
    setSingleResult(null)

    try {
      const response = await axios.get<SymbolResponse>(`/api/lookup?company_name=${encodeURIComponent(companyName)}`)
      
      if (response.data.success && response.data.symbol) {
        setSingleResult(response.data.symbol)
        setColumns(['Name', 'Symbol'])
        setResultData([{ Name: companyName, Symbol: response.data.symbol }])
      } else {
        setError('No symbol found')
      }
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Lookup failed')
      } else {
        setError('Lookup failed')
      }
    } finally {
      setUploading(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0]
      if (selectedFile.name.endsWith('.csv')) {
        setFile(selectedFile)
        setError(null)
      } else {
        setError('Please upload a CSV file')
      }
    }
  }

  const handleCsvUpload = async () => {
    if (!file) {
      setError('Please select a file first')
      return
    }

    setUploading(true)
    setError(null)
    setCsvResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post<UploadResult>('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      if ('error' in response.data) {
        setError(response.data.error)
      } else {
        setCsvResult(response.data as EnrichmentResult)
        await loadCsvData(response.data.output_file)
      }
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || err.message || 'Upload failed')
      } else {
        setError('An unexpected error occurred')
      }
    } finally {
      setUploading(false)
    }
  }

  const loadCsvData = async (filePath: string) => {
    try {
      const filename = filePath.split('/').pop()
      const response = await axios.get(`/api/download/${filename}`, {
        responseType: 'text',
      })

      const lines = response.data.split('\n').filter((line: string) => line.trim())
      const headers = lines[0].split(',').map((h: string) => h.trim())
      setColumns(headers)
      
      const data: CompanyData[] = []

      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',')
        const row: CompanyData = {}
        
        headers.forEach((header, index) => {
          row[header] = values[index]?.trim() || ''
        })
        
        data.push(row)
      }

      setResultData(data)
    } catch (err: unknown) {
      console.error('Failed to load CSV data:', err)
    }
  }

  const handleDownload = async () => {
    if (!csvResult?.output_file) return

    try {
      const filename = csvResult.output_file.split('/').pop()
      const response = await axios.get(`/api/download/${filename}`, {
        responseType: 'blob',
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename || 'enriched.csv')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Download failed')
      } else {
        setError('Download failed')
      }
    }
  }

  const handleTabChange = (tab: 'single' | 'csv') => {
    setActiveTab(tab)
    setResultData([])
    setColumns([])
    setSingleResult(null)
    setCsvResult(null)
    setError(null)
    setSearchTerm('')
    setFile(null)
    setCompanyName('')
  }

  const filteredData = resultData.filter(item =>
    Object.values(item).some(value => 
      value.toLowerCase().includes(searchTerm.toLowerCase())
    )
  ).slice(0, 50)

  return (
    <div className="min-h-screen stock-bg p-8">
      {/* Floating Ticker Symbols */}
      <div className="ticker-symbol ticker-1">AAPL</div>
      <div className="ticker-symbol ticker-2">MSFT</div>
      <div className="ticker-symbol ticker-3">GOOGL</div>
      <div className="ticker-symbol ticker-4">TSLA</div>
      <div className="ticker-symbol ticker-5">AMZN</div>
      <div className="ticker-symbol ticker-6">NVDA</div>
      <div className="ticker-symbol ticker-7">META</div>
      <div className="ticker-symbol ticker-8">NFLX</div>
      
      {/* Floating Price Changes */}
      <div className="price-change price-up price-1">+2.45%</div>
      <div className="price-change price-down price-2">-1.23%</div>
      <div className="price-change price-up price-3">+3.67%</div>
      <div className="price-change price-down price-4">-0.89%</div>
      <div className="price-change price-up price-5">+1.92%</div>
      <div className="price-change price-down price-6">-2.15%</div>
      
      <div className="max-w-4xl mx-auto content-wrapper">
        <h1 className="text-5xl font-bold text-white mb-10 text-center drop-shadow-2xl tracking-tight">
          Finding Tickers
        </h1>
        
        {/* Container 1: Input */}
        <div className="glass-container rounded-xl p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-slate-200">Input</h2>
          
          {/* Tabs */}
          <div className="flex gap-2 mb-6 border-b border-slate-600">
            <button
              onClick={() => handleTabChange('single')}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === 'single'
                  ? 'border-b-2 border-blue-400 text-blue-400'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Single Lookup
            </button>
            <button
              onClick={() => handleTabChange('csv')}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === 'csv'
                  ? 'border-b-2 border-blue-400 text-blue-400'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              CSV Upload
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'single' ? (
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Company Name
              </label>
              <input
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Enter company name..."
                className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 mb-4 transition-all text-white placeholder-slate-400"
                onKeyPress={(e) => e.key === 'Enter' && handleSingleLookup()}
              />
              <button
                onClick={handleSingleLookup}
                disabled={uploading}
                className="w-full bg-gradient-to-r from-blue-600 to-blue-500 text-white py-3 px-4 rounded-lg hover:from-blue-700 hover:to-blue-600 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed transition-all font-medium shadow-lg hover:shadow-blue-500/50"
              >
                {uploading ? 'Looking up...' : 'Get Symbol'}
              </button>
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Upload CSV File
              </label>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="w-full mb-4 text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-700 file:cursor-pointer file:transition-colors"
              />
              <button
                onClick={handleCsvUpload}
                disabled={!file || uploading}
                className="w-full bg-gradient-to-r from-blue-600 to-blue-500 text-white py-3 px-4 rounded-lg hover:from-blue-700 hover:to-blue-600 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed transition-all font-medium shadow-lg hover:shadow-blue-500/50"
              >
                {uploading ? 'Processing...' : 'Upload & Enrich'}
              </button>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="mt-4 p-3 bg-red-900/30 border-l-4 border-red-500 rounded text-red-300 text-sm backdrop-blur-sm">
              {error}
            </div>
          )}
        </div>

        {/* Container 2: Results */}
        <div className="glass-container rounded-xl p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-slate-200">Results</h2>
            {csvResult && activeTab === 'csv' && (
              <button
                onClick={handleDownload}
                className="bg-gradient-to-r from-emerald-600 to-emerald-500 text-white px-4 py-2 rounded-lg hover:from-emerald-700 hover:to-emerald-600 text-sm font-medium transition-all shadow-lg hover:shadow-emerald-500/50"
              >
                Download CSV
              </button>
            )}
          </div>

          {/* Search Bar */}
          {resultData.length > 0 && (
            <input
              type="text"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg mb-4 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all text-white placeholder-slate-400"
            />
          )}

          {/* Results Table */}
          {resultData.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-slate-600 bg-slate-800/40">
                    {columns.map((column, index) => (
                      <th key={index} className="text-left py-3 px-4 text-sm font-semibold text-slate-200">
                        {column}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredData.map((item, index) => (
                    <tr key={index} className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors">
                      {columns.map((column, colIndex) => (
                        <td 
                          key={colIndex} 
                          className={`py-3 px-4 text-sm ${
                            column === 'Symbol' 
                              ? 'font-semibold text-blue-400' 
                              : 'text-slate-300'
                          }`}
                        >
                          {item[column]}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-xs text-slate-400 mt-3 italic">
                Showing {filteredData.length} of {resultData.length} results (max 50 displayed)
              </p>
            </div>
          ) : (
            <div className="text-center text-slate-400 py-12">
              <p className="text-sm">No results yet.</p>
              <p className="text-xs mt-1">Enter a company name or upload a CSV file.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
