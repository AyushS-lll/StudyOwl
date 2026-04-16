import React, { useRef } from 'react'

interface PhotoUploadProps {
  onPhotoCapture: (base64: string) => void
  loading?: boolean
}

export const PhotoUpload: React.FC<PhotoUploadProps> = ({ onPhotoCapture, loading = false }) => {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (event) => {
      const base64 = event.target?.result as string
      onPhotoCapture(base64)
    }
    reader.readAsDataURL(file)
  }

  return (
    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
      <button
        onClick={() => fileInputRef.current?.click()}
        disabled={loading}
        className="text-gray-600 hover:text-gray-900 font-semibold disabled:opacity-50 transition"
      >
        📷 Upload Photo or Problem Image
      </button>
      <p className="text-sm text-gray-500 mt-2">
        or drag and drop
      </p>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  )
}

export default PhotoUpload
