import { useState } from 'react';
import PipelineCreationPanel from './components/PipelineCreationPanel';
import ChatPanel from './components/ChatPanel';
import Header from './components/Header';
import Footer from './components/Footer';

function App() {
  const [token, setToken] = useState<string | null>(
    localStorage.getItem('ragToken')
  );

  // Handler for when a new pipeline is created
  const handlePipelineCreated = (newToken: string) => {
    localStorage.setItem('ragToken', newToken);
    setToken(newToken);
  };return (
    <div className="flex flex-col min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />
      
      <main className="flex-grow container mx-auto p-4">
        <div className="lg:flex gap-6">
          {/* Pipeline Creation Form */}
          <div className={`lg:w-1/2 mb-8 lg:mb-0 ${token ? 'lg:hidden' : ''}`}>
            <PipelineCreationPanel onPipelineCreated={handlePipelineCreated} />
          </div>
          
          {/* Chat Interface */}
          <div className={`lg:w-1/2 ${!token ? 'lg:hidden' : ''}`}>
            <ChatPanel 
              initialToken={token} 
              onTokenChange={(newToken: string) => {
                localStorage.setItem('ragToken', newToken);
                setToken(newToken);
              }} 
              onClearToken={() => {
                localStorage.removeItem('ragToken');
                setToken(null);
              }}
            />
          </div>
        </div>
      </main>
      
      <Footer />
    </div>
  );
}

export default App;
