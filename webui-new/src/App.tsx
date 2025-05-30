import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import CreatePipelinePage from './pages/CreatePipeline';
import PlaygroundPage from './pages/Playground';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/cpl" element={<CreatePipelinePage />} />
        <Route path="/pg" element={<PlaygroundPage />} />
        <Route path="/" element={<Navigate to="/cpl" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;