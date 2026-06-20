const Footer = () => {
  return (
    <footer className="bg-gray-100 dark:bg-gray-800 py-4">
      <div className="container mx-auto px-4 text-center text-sm text-gray-600 dark:text-gray-400">
        <p>ArtificialInsight Web UI — © {new Date().getFullYear()}</p>
      </div>
    </footer>
  );
};

export default Footer;
