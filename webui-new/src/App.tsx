import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import CreatePipelinePage from './pages/CreatePipeline';
import PlaygroundPage from './pages/Playground';
import Header from './components/Header';
import Footer from './components/Footer';

function App() {
  return (
    <div className="flex flex-col min-h-screen bg-slate-50">
      <BrowserRouter>
        <Header />
        <main className="flex-grow container mx-auto px-4 py-6">
          <Routes>
            <Route path="/" element={<Navigate to="/create-pipeline" replace />} />
            <Route path="/create-pipeline" element={<CreatePipelinePage />} />
            <Route path="/playground" element={<PlaygroundPage />} />
            <Route path="*" element={<Navigate to="/create-pipeline" replace />} />
          </Routes>
        </main>
        <Footer />
      </BrowserRouter>
    </div>
  );
}

export default App;