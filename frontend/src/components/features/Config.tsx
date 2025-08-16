import { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { Card } from '../ui/Card';
import { Loader } from '../ui/Loader';

const Config = () => {
  const [config, setConfig] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api.get('/config/models')
      .then(res => setConfig(res.data))
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <Loader />;

  return (
    <Card className="p-8">
      <h1 className="text-3xl font-bold mb-6">System Configuration</h1>
      <div className="space-y-4">
        <div>
          <h2 className="text-lg font-semibold text-muted-foreground">Embedding Model</h2>
          <p className="text-xl">{config?.embedding_model}</p>
        </div>
        <div>
          <h2 className="text-lg font-semibold text-muted-foreground">Chunking Strategy</h2>
          <p className="text-xl">Size: {config?.chunk_size} characters</p>
          <p className="text-xl">Overlap: {config?.chunk_overlap} characters</p>
        </div>
        <p className="text-sm text-muted-foreground pt-4">
          This configuration is set on the backend and applies to all new document uploads.
        </p>
      </div>
    </Card>
  );
};

export default Config;