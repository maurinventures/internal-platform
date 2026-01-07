import React, { useState } from 'react';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { Header } from './components/layout/Header';
import { ChatScreen } from './components/screens/chat-screen';
import { UsageDisplay } from './components/usage/UsageDisplay';

// Type definitions for Chat components
interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  scriptData?: any; // Simplified for now
}

interface Chat {
  id: string;
  title: string;
  messages: Message[];
  starred?: boolean;
  projectId?: string;
  projectName?: string;
  lastModified?: number;
}

// Dashboard component with new UI design
function Dashboard() {
  const [allChats, setAllChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState('');

  const handleProjectClick = () => {
    console.log('Project clicked');
  };

  const handleLibraryClick = () => {
    console.log('Library clicked');
  };

  const handleProjectsClick = () => {
    console.log('Projects clicked');
  };

  const handleLibraryHeaderClick = () => {
    console.log('Library header clicked');
  };

  const handleChatSelect = (chatId: string) => {
    setCurrentChatId(chatId);
  };

  const handleNewChat = () => {
    console.log('New chat');
  };

  return (
    <div className="min-h-screen">
      <ChatScreen
        onProjectClick={handleProjectClick}
        onLibraryClick={handleLibraryClick}
        onProjectsClick={handleProjectsClick}
        onLibraryHeaderClick={handleLibraryHeaderClick}
        allChats={allChats}
        setAllChats={setAllChats}
        currentChatId={currentChatId}
        onChatSelect={handleChatSelect}
        onNewChat={handleNewChat}
      />
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <div className="App">
        <ProtectedRoute>
          <Dashboard />
        </ProtectedRoute>
      </div>
    </AuthProvider>
  );
}

export default App;
