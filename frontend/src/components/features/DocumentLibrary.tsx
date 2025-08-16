import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../services/api';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Loader } from '../ui/Loader';
import { FileText, Trash2 } from 'lucide-react';
import { useToast } from '../../hooks/useToast';

type Document = {
  id: number;
  filename: string;
  chunk_count: number;
  processed_at: string;
};

const DocumentLibrary = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();
  const { toast } = useToast();

  const fetchDocuments = () => {
    setIsLoading(true);
    api.get('/documents')
      .then(res => setDocuments(res.data))
      .catch(console.error)
      .finally(() => setIsLoading(false));
  };

  useEffect(fetchDocuments, []);

  const handleDelete = async (docId: number, filename: string) => {
    if (window.confirm(`Are you sure you want to delete ${filename}? This action cannot be undone.`)) {
      try {
        await api.delete(`/documents/${docId}`);
        toast({ title: "Success", description: `${filename} has been deleted.` });
        fetchDocuments(); // Refresh the list
      } catch (error) {
        toast({ title: "Error", description: `Failed to delete ${filename}.`, variant: "destructive" });
      }
    }
  };

  if (isLoading) return <Loader />;

  return (
    <Card>
      <div className="p-6">
        <h2 className="text-2xl font-semibold">Document Library</h2>
      </div>
      <div className="border-t border-muted">
        {documents.length === 0 ? (
          <p className="p-6 text-muted-foreground">No documents uploaded yet.</p>
        ) : (
          <ul className="divide-y divide-muted">
            {documents.map(doc => (
              <li key={doc.id} className="p-4 flex justify-between items-center hover:bg-muted/50 transition-colors">
                <div className="flex items-center gap-4">
                  <FileText className="h-8 w-8 text-primary" />
                  <div>
                    <p className="font-medium">{doc.filename}</p>
                    <p className="text-sm text-muted-foreground">
                      {doc.chunk_count} chunks • Processed on {new Date(doc.processed_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => navigate(`/library/${doc.id}`)}>
                    View Details
                  </Button>
                  <Button variant="destructive" size="icon" onClick={() => handleDelete(doc.id, doc.filename)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Card>
  );
};

export default DocumentLibrary;