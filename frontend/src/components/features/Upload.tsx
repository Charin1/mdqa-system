import { useState, useCallback } from 'react';
import { UploadCloud } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { api } from '../../services/api';
import { useToast } from '../../hooks/useToast';

const Upload = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const { toast } = useToast();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles(prev => [...prev, ...acceptedFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    }
  });

  const handleUpload = async () => {
    if (files.length === 0) return;
    setIsUploading(true);
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    try {
      const response = await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const { success, errors } = response.data;
      
      if (success.length > 0) {
        toast({ title: "Upload Complete", description: `${success.length} file(s) processed successfully.` });
      }
      if (errors.length > 0) {
        const errorDetails = errors.map((e: any) => `${e.filename}: ${e.error}`).join('\n');
        toast({ title: `${errors.length} Upload(s) Failed`, description: errorDetails, variant: "destructive" });
      }
      
      setFiles([]);
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || "An unexpected error occurred.";
      toast({ title: "Upload Failed", description: errorMsg, variant: "destructive" });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Card className="p-8">
      <h2 className="text-2xl font-semibold mb-4">Upload Documents</h2>
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-primary bg-muted' : 'border-muted-foreground hover:border-primary'
        }`}
      >
        <input {...getInputProps()} />
        <UploadCloud className="mx-auto h-12 w-12 text-muted-foreground" />
        <p className="mt-4 text-muted-foreground">Drag & drop files here, or click to select</p>
        <p className="text-xs text-muted-foreground/70">Supported: PDF, DOCX, TXT, MD</p>
      </div>
      {files.length > 0 && (
        <div className="mt-6">
          <h3 className="font-semibold">Selected files:</h3>
          <ul className="list-disc list-inside mt-2 max-h-40 overflow-y-auto">
            {files.map((file, i) => <li key={i}>{file.name}</li>)}
          </ul>
          <div className="mt-4 flex gap-4">
            <Button onClick={handleUpload} disabled={isUploading}>
              {isUploading ? 'Uploading...' : `Upload ${files.length} File(s)`}
            </Button>
            <Button variant="outline" onClick={() => setFiles([])} disabled={isUploading}>
              Clear
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
};

export default Upload;