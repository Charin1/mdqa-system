import { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { Card } from '../ui/Card';
import { Loader } from '../ui/Loader';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const Analytics = () => {
  const [overview, setOverview] = useState<any>(null);
  const [latency, setLatency] = useState<any>({});
  const [precision, setPrecision] = useState<any>({});
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [overviewRes, latencyRes, precisionRes] = await Promise.all([
          api.get('/analytics/overview'),
          api.get('/analytics/latency'),
          api.get('/analytics/precision'),
        ]);
        setOverview(overviewRes.data);
        setLatency(latencyRes.data);
        setPrecision(precisionRes.data);
      } catch (error) {
        console.error("Failed to fetch analytics data", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  if (isLoading) return <Loader />;

  const chartOptions = {
    responsive: true,
    plugins: { legend: { labels: { color: '#fff' } } },
    scales: {
      x: { ticks: { color: '#fff' }, grid: { color: 'rgba(255,255,255,0.1)' } },
      y: { ticks: { color: '#fff' }, grid: { color: 'rgba(255,255,255,0.1)' } },
    },
  };

  const latencyData = {
    labels: Object.keys(latency),
    datasets: [{ label: 'Query Count', data: Object.values(latency), backgroundColor: '#3b82f6' }]
  };

  const precisionData = {
    labels: Object.keys(precision),
    datasets: [{ label: 'Precision Score', data: Object.values(precision), backgroundColor: '#10b981' }]
  };

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">System Analytics</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6">
          <h3 className="text-muted-foreground">Total Documents</h3>
          <p className="text-3xl font-bold">{overview?.total_documents ?? 0}</p>
        </Card>
        <Card className="p-6">
          <h3 className="text-muted-foreground">Total Chunks</h3>
          <p className="text-3xl font-bold">{overview?.total_chunks ?? 0}</p>
        </Card>
        <Card className="p-6">
          <h3 className="text-muted-foreground">Total Queries</h3>
          <p className="text-3xl font-bold">{overview?.total_queries ?? 0}</p>
        </Card>
        <Card className="p-6">
          <h3 className="text-muted-foreground">Avg. Response Time</h3>
          <p className="text-3xl font-bold">{overview?.avg_response_time ?? 0}s</p>
        </Card>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="font-semibold mb-4">Query Latency Distribution</h3>
          <Bar data={latencyData} options={chartOptions} />
        </Card>
        <Card className="p-6">
          <h3 className="font-semibold mb-4">Retrieval Precision @ K</h3>
          <Bar data={precisionData} options={chartOptions} />
        </Card>
      </div>
    </div>
  );
};

export default Analytics;