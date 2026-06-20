import { Link } from 'react-router-dom';

const Header = () => {
  return (
    <header className="bg-blue-600 text-white shadow-md">
      <div className="container mx-auto p-4 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">ArtificialInsight</h1>
          <p className="text-sm">RAG Pipeline Creator</p>
        </div>
        <nav className="flex gap-6">
          <Link 
            to="/create-pipeline" 
            className="hover:underline px-3 py-1 rounded hover:bg-blue-700 transition-colors"
          >
            Create Pipeline
          </Link>
          <Link 
            to="/playground" 
            className="hover:underline px-3 py-1 rounded hover:bg-blue-700 transition-colors"
          >
            Playground
          </Link>
        </nav>
      </div>
    </header>
  );
};

export default Header;