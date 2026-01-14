/**
 * FileUpload component for attaching files to council sessions
 */
import React, { useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import type { FileAttachment } from '@/types';
import { API_URLS, VALIDATION } from '@/lib/config';

interface FileUploadProps {
  files: FileAttachment[];
  onFilesChange: (files: FileAttachment[]) => void;
  disabled?: boolean;
}

export const FileUpload: React.FC<FileUploadProps> = ({ files, onFilesChange, disabled }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (!selectedFiles || selectedFiles.length === 0) return;

    setUploading(true);
    setError(null);

    try {
      const uploadedFiles: FileAttachment[] = [];

      for (const file of Array.from(selectedFiles)) {
        // Client-side file size validation
        if (file.size > VALIDATION.maxFileSize) {
          throw new Error(
            `File "${file.name}" is too large (${formatFileSize(file.size)}). Maximum size is ${VALIDATION.maxFileSizeMB}MB.`
          );
        }

        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(API_URLS.uploadFile, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Upload failed');
        }

        const fileAttachment: FileAttachment = await response.json();
        uploadedFiles.push(fileAttachment);
      }

      onFilesChange([...files, ...uploadedFiles]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload file');
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleRemoveFile = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    onFilesChange(newFiles);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || uploading}
        >
          {uploading ? '⏳ Uploading...' : '📎 Attach Files'}
        </Button>
        <span className="text-xs text-muted-foreground">
          Supports: images, PDFs, docs, code, spreadsheets (max 10MB)
        </span>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileSelect}
        className="hidden"
        accept=".jpg,.jpeg,.png,.gif,.bmp,.webp,.pdf,.txt,.md,.docx,.py,.js,.ts,.tsx,.jsx,.java,.cpp,.c,.cs,.go,.rs,.html,.css,.json,.xml,.yaml,.yml,.sh,.sql,.xlsx,.csv,.pptx"
      />

      {error && (
        <div className="text-sm text-destructive bg-destructive/10 p-2 rounded">
          {error}
        </div>
      )}

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((file, index) => (
            <Card key={index} className="p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium truncate">{file.filename}</span>
                    {file.base64_data && (
                      <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded">
                        Vision
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                    <span>{formatFileSize(file.size)}</span>
                    {file.extracted_text && (
                      <span>• {file.extracted_text.substring(0, 50)}...</span>
                    )}
                  </div>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRemoveFile(index)}
                  disabled={disabled}
                  className="text-destructive hover:text-destructive"
                >
                  ✕
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
