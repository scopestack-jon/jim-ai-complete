import { useState, useEffect, useCallback } from 'react'
import { Upload, FileText, Download, Trash2, AlertCircle, CheckCircle, Clock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { formatFileSize, formatDate } from '@/lib/utils'

const API_BASE = '/api'

function App() {
  const [files, setFiles] = useState([])
  const [uploadConfig, setUploadConfig] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState({})
  const [caseId, setCaseId] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState('')

  // Fetch configuration and files on load
  useEffect(() => {
    fetchConfig()
    fetchFiles()
  }, [])

  const fetchConfig = async () => {
    try {
      const response = await fetch(`${API_BASE}/config`)
      if (response.ok) {
        const config = await response.json()
        setUploadConfig(config)
      }
    } catch (error) {
      console.error('Failed to fetch config:', error)
      setError('Failed to load configuration')
    }
  }

  const fetchFiles = async () => {
    try {
      const response = await fetch(`${API_BASE}/files`)
      if (response.ok) {
        const fileList = await response.json()
        setFiles(fileList)
      }
    } catch (error) {
      console.error('Failed to fetch files:', error)
    }
  }

  const handleDrag = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(Array.from(e.dataTransfer.files))
    }
  }, [])

  const handleFileInput = (e) => {
    if (e.target.files) {
      handleFiles(Array.from(e.target.files))
    }
  }

  const validateFile = (file) => {
    if (!uploadConfig) return { valid: false, error: 'Configuration not loaded' }
    
    if (file.size > uploadConfig.max_file_size) {
      return { 
        valid: false, 
        error: `File too large. Maximum size: ${formatFileSize(uploadConfig.max_file_size)}` 
      }
    }

    const extension = file.name.split('.').pop()?.toLowerCase()
    if (extension && !uploadConfig.allowed_extensions.includes(extension)) {
      return { 
        valid: false, 
        error: `File type not supported. Allowed types: ${uploadConfig.allowed_extensions.join(', ')}` 
      }
    }

    return { valid: true }
  }

  const handleFiles = async (fileList) => {
    setError('')
    setUploading(true)

    for (const file of fileList) {
      const validation = validateFile(file)
      if (!validation.valid) {
        setError(validation.error)
        continue
      }

      try {
        await uploadFile(file)
      } catch (error) {
        console.error('Upload failed:', error)
        setError(`Failed to upload ${file.name}: ${error.message}`)
      }
    }

    setUploading(false)
    fetchFiles() // Refresh file list
  }

  const uploadFile = async (file) => {
    const fileId = Date.now().toString()
    
    // Initialize progress
    setUploadProgress(prev => ({ ...prev, [fileId]: 0 }))

    try {
      // Step 1: Get upload URL
      const uploadResponse = await fetch(`${API_BASE}/upload-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: file.name,
          file_size: file.size,
          file_type: file.type,
          case_id: caseId || null,
          description: description || null
        })
      })

      if (!uploadResponse.ok) {
        throw new Error('Failed to get upload URL')
      }

      const { upload_url, file_id, s3_key } = await uploadResponse.json()

      // Step 2: Upload to S3 with progress
      setUploadProgress(prev => ({ ...prev, [fileId]: 25 }))

      const s3Response = await fetch(upload_url, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type
        }
      })

      if (!s3Response.ok) {
        throw new Error('Failed to upload to S3')
      }

      setUploadProgress(prev => ({ ...prev, [fileId]: 75 }))

      // Step 3: Mark upload complete
      const completeResponse = await fetch(`${API_BASE}/upload-complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_id,
          s3_key,
          filename: file.name,
          file_size: file.size,
          file_type: file.type,
          case_id: caseId || null,
          description: description || null
        })
      })

      if (!completeResponse.ok) {
        throw new Error('Failed to complete upload')
      }

      setUploadProgress(prev => ({ ...prev, [fileId]: 100 }))

      // Clean up progress after delay
      setTimeout(() => {
        setUploadProgress(prev => {
          const newProgress = { ...prev }
          delete newProgress[fileId]
          return newProgress
        })
      }, 2000)

    } catch (error) {
      setUploadProgress(prev => {
        const newProgress = { ...prev }
        delete newProgress[fileId]
        return newProgress
      })
      throw error
    }
  }

  const downloadFile = async (fileId, filename) => {
    try {
      const response = await fetch(`${API_BASE}/files/${fileId}/download-url`)
      if (response.ok) {
        const { download_url } = await response.json()
        
        // Create temporary link and trigger download
        const link = document.createElement('a')
        link.href = download_url
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      }
    } catch (error) {
      console.error('Download failed:', error)
      setError('Failed to download file')
    }
  }

  const deleteFile = async (fileId) => {
    try {
      const response = await fetch(`${API_BASE}/files/${fileId}`, {
        method: 'DELETE'
      })
      if (response.ok) {
        fetchFiles() // Refresh file list
      }
    } catch (error) {
      console.error('Delete failed:', error)
      setError('Failed to delete file')
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'uploaded':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'processing':
        return <Clock className="w-4 h-4 text-yellow-500" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      default:
        return <Clock className="w-4 h-4 text-gray-500" />
    }
  }

  const getStatusBadge = (status) => {
    const variants = {
      uploaded: 'default',
      processing: 'secondary',
      error: 'destructive'
    }
    return <Badge variant={variants[status] || 'secondary'}>{status}</Badge>
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-slate-800 mb-2">JIM AI</h1>
          <p className="text-xl text-slate-600 mb-2">Forensic Analyst Agent for Legal Teams</p>
          <p className="text-sm text-slate-500">Secure file upload and management for forensic analysis</p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center gap-2 text-red-700">
              <AlertCircle className="w-4 h-4" />
              <span>{error}</span>
            </div>
          </div>
        )}

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="w-5 h-5" />
                Upload Files
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Case Information */}
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <Label htmlFor="case-id">Case ID (Optional)</Label>
                  <Input
                    id="case-id"
                    placeholder="e.g., CASE-2024-001"
                    value={caseId}
                    onChange={(e) => setCaseId(e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="description">Description (Optional)</Label>
                  <Textarea
                    id="description"
                    placeholder="Brief description of the evidence..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="min-h-[80px]"
                  />
                </div>
              </div>

              {/* Upload Area */}
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  dragActive 
                    ? 'border-blue-400 bg-blue-50' 
                    : 'border-slate-300 hover:border-slate-400'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <Upload className="w-12 h-12 mx-auto mb-4 text-slate-400" />
                <p className="text-lg font-medium mb-2">Drop files here or click to select</p>
                <p className="text-sm text-slate-500 mb-4">
                  Maximum file size: {uploadConfig ? formatFileSize(uploadConfig.max_file_size) : '500 MB'}
                </p>
                
                <input
                  type="file"
                  multiple
                  onChange={handleFileInput}
                  className="hidden"
                  id="file-input"
                  disabled={uploading}
                />
                <Button 
                  onClick={() => document.getElementById('file-input')?.click()}
                  disabled={uploading}
                  className="mb-4"
                >
                  {uploading ? 'Uploading...' : 'Select Files'}
                </Button>

                {/* Upload Progress */}
                {Object.keys(uploadProgress).length > 0 && (
                  <div className="space-y-2">
                    {Object.entries(uploadProgress).map(([fileId, progress]) => (
                      <div key={fileId} className="text-left">
                        <div className="flex justify-between text-sm mb-1">
                          <span>Uploading...</span>
                          <span>{progress}%</span>
                        </div>
                        <Progress value={progress} className="h-2" />
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Supported File Types */}
              {uploadConfig && (
                <div className="text-xs text-slate-500">
                  <p className="font-medium mb-1">Supported file types:</p>
                  <p>{uploadConfig.allowed_extensions.join(', ').toUpperCase()}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* File Management */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Uploaded Files
              </CardTitle>
            </CardHeader>
            <CardContent>
              {files.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No files uploaded yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {files.map((file) => (
                    <div key={file.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        {getStatusIcon(file.status)}
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate">{file.filename}</p>
                          <div className="flex items-center gap-2 text-xs text-slate-500">
                            <span>{formatFileSize(file.file_size)}</span>
                            <span>•</span>
                            <span>{formatDate(file.upload_date)}</span>
                            {file.case_id && (
                              <>
                                <span>•</span>
                                <span>{file.case_id}</span>
                              </>
                            )}
                          </div>
                          {file.description && (
                            <p className="text-xs text-slate-600 mt-1 truncate">{file.description}</p>
                          )}
                        </div>
                        {getStatusBadge(file.status)}
                      </div>
                      <div className="flex items-center gap-1 ml-2">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => downloadFile(file.id, file.filename)}
                          disabled={file.status !== 'uploaded'}
                        >
                          <Download className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => deleteFile(file.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-sm text-slate-500">
          <p>JIM AI - Secure forensic file management for legal professionals</p>
          <p>All files are encrypted and stored securely in AWS S3</p>
        </div>
      </div>
    </div>
  )
}

export default App

