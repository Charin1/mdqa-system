import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../../services/api';
import { Card } from '../ui/Card';
import { Loader } from '../ui/Loader';
import { Button } from '../ui/Button';
import { ArrowLeft, Download } from 'lucide-react';

type Chunk = {
  id: string;
  text_preview: string;
  page: number | null;
  metadata: any;
};

const DocumentViewer = () => {
  const { docId } = useParams();
  const navigate = useNavigate();
  const [doc, setDoc] = useState<any>(null);
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!docId) return;
    const fetchData = async () => {
      try {
        const [docRes, chunksRes] = await Promise.all([
          api.get(`/documents/${docId}`),
          api.get(`/documents/${docId}/chunks`),
        ]);
        setDoc(docRes.data);
        setChunks(chunksRes.data);
      } catch (error) {
        console.error("Failed to fetch document details", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [docId]);

  const handleDownload = async () => {
    const response = await api.get(`/documents/${docId}/download`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', doc.filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  if (isLoading) return <Loader />;
  if (!doc) return <p>Document not found.</p>;

  return (
    <div className="space-y-6">
      <Button variant="outline" onClick={() => navigate('/library')}>
        <ArrowLeft className="mr-2 h-4 w-4" /> Back to Library
      </Button>
      <Card className="p-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold">{doc.filename}</h1>
            <p className="text-muted-foreground">
              {doc.chunk_count} chunks • Processed on {new Date(doc.processed_at).toLocaleString()}
            </p>
          </div>
          <Button onClick={handleDownload}>
            <Download className="mr-2 h-4 w-4" /> Download Original
          </Button>
        </div>
      </Card>
      
      <h2 className="text-xl font-semibold">Document Chunks</h2>
      <div className="space-y-4">
        {chunks.map(chunk => (
          <Card key={chunk.id} className="p-4 bg-muted/50">
            <p className="text-sm text-muted-foreground">
              Chunk ID: {chunk.id.substring(0, 8)}... {chunk.page && `(Page ${chunk.page})`}
            </p>
            <p className="mt-2 text-foreground/80">{chunk.text_preview}</p>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default DocumentViewer;