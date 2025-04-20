import React, { useState, useEffect } from 'react';
import { sendPrompt } from '../api/api';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
}

interface ChatPanelProps {
  initialToken?: string | null;
  onTokenChange: (newToken: string) => void;
  onClearToken: () => void;
}

const ChatPanel: React.FC<ChatPanelProps> = ({ initialToken, onTokenChange, onClearToken }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [token, setToken] = useState(initialToken);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setToken(initialToken);
  }, [initialToken]);

  const handleSendMessage = async () => {
    if (!input.trim()) return;
    if (!token) {
      setError("No token provided. Please create a pipeline first.");
      return;
    }

    // Add user message
    const newMessage: Message = {
      id: Date.now().toString(),
      content: input,
      sender: 'user',
      timestamp: new Date()
    };
    
    setMessages([...messages, newMessage]);
    const userInput = input;
    setInput('');
    setIsLoading(true);
    setError(null);
    
    try {
      // Make API call to get a response
      const response = await sendPrompt(token, userInput);
      
      const aiResponse: Message = {
        id: Date.now().toString(),
        content: response.answer,
        sender: 'ai',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiResponse]);
    } catch (err: any) {
      setError(err.message || "Failed to get response from the server");
      console.error("Error sending prompt:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-gray-800 dark:text-white">Chat with RAG Pipeline</h2>
        
        {token && (
          <button
            onClick={onClearToken}
            className="text-sm bg-red-100 text-red-700 px-3 py-1 rounded hover:bg-red-200"
          >
            Disconnect
          </button>
        )}
      </div>
      
      {!token ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-4 mb-4">
          <p className="text-yellow-700">
            No token connected. Please create a RAG pipeline first or enter a token.
          </p>
          <div className="mt-3 flex">
            <input
              type="text"
              className="flex-grow border rounded px-2 py-1 mr-2"
              placeholder="Enter existing token..."
              onChange={(e) => setToken(e.target.value)}
            />
            <button
              className="bg-blue-600 text-white px-3 py-1 rounded"
              onClick={() => {
                if (token) onTokenChange(token);
              }}
            >
              Connect
            </button>
          </div>
        </div>
      ) : null}
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          <p>{error}</p>
        </div>
      )}
      
      <div className="messages-container h-96 overflow-y-auto border border-gray-200 rounded p-4 mb-4 bg-gray-50 dark:bg-gray-900">
        {messages.length === 0 ? (
          <p className="text-gray-500 italic text-center mt-32">No messages yet. Start the conversation!</p>
        ) : (
          messages.map((msg) => (
            <div 
              key={msg.id} 
              className={`mb-4 ${msg.sender === 'user' ? 'text-right' : 'text-left'}`}
            >
              <div 
                className={`inline-block max-w-xs sm:max-w-md px-4 py-2 rounded-lg ${
                  msg.sender === 'user' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
                }`}
              >
                <p>{msg.content}</p>
                <span className={`text-xs ${msg.sender === 'user' ? 'text-blue-200' : 'text-gray-500 dark:text-gray-400'}`}>
                  {msg.timestamp.toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
      
      <div className="flex">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          disabled={isLoading || !token}
          placeholder={token ? "Type your message..." : "Connect a token first..."}
          className="flex-grow px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        />
        <button
          onClick={handleSendMessage}
          disabled={isLoading || !token}
          className="bg-blue-600 text-white px-4 py-2 rounded-r-md hover:bg-blue-700 disabled:bg-blue-300"
        >
          {isLoading ? (
            <span className="flex items-center">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Sending...
            </span>
          ) : (
            'Send'
          )}
        </button>
      </div>
    </div>
  );
};

export default ChatPanel;
