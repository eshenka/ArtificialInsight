import PipelineCreationPanel from '../../components/PipelineCreationPanel';
import Header from '../../components/Header';
import Footer from '../../components/Footer';

export default function CreatePipelinePage() {
  return (
    <div className="flex flex-col min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />
      <main className="flex-grow container mx-auto p-4">
        <PipelineCreationPanel
          onPipelineCreated={(token) => {
            localStorage.setItem('ragToken', token);
            window.location.href = '/playground';
          }}
        />
      </main>
      <Footer />
    </div>
  );
}