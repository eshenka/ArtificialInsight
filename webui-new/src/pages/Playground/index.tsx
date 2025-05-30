import ChatPanel from '../../components/ChatPanel';
import Header from '../../components/Header';
import Footer from '../../components/Footer';

export default function PlaygroundPage() {
  return (
    <div className="flex flex-col min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />
      <main className="flex-grow container mx-auto p-4">
        <ChatPanel
          initialToken={localStorage.getItem('ragToken')}
          onTokenChange={(token) => localStorage.setItem('ragToken', token)}
          onClearToken={() => localStorage.removeItem('ragToken')}
        />
      </main>
      <Footer />
    </div>
  );
}