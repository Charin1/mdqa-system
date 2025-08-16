import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Upload from './components/features/Upload';
import DocumentLibrary from './components/features/DocumentLibrary';
import Chat from './components/features/Chat';
import Analytics from './components/features/Analytics';
import Config from './components/features/Config';
import DocumentViewer from './components/features/DocumentViewer';
import { Toaster } from './components/ui/Toast';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Upload />} />
          <Route path="/library" element={<DocumentLibrary />} />
          <Route path="/library/:docId" element={<DocumentViewer />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/config" element={<Config />} />
        </Routes>
      </Layout>
      <Toaster />
    </BrowserRouter>
  );
}

export default App;