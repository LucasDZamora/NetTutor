import React, { useState } from 'react';
import Navbar from './components/Navbar';
import AnalysisView from './components/AnalysisView';
import ChatView from './components/ChatView';
import SimulatorView from './components/SimulatorView';
import LoginModal from './components/LoginModal';

function App() {
  const [activeView, setActiveView] = useState('analysis');
  const [showLoginModal, setShowLoginModal] = useState(false);
  
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("user");
    return savedUser ? JSON.parse(savedUser) : null;
  });

  const handleLoginSuccess = (userData) => {
    localStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);
    setShowLoginModal(false);
  };

  const handleLogout = () => {
    localStorage.removeItem("user");
    setUser(null);
  };

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-gray-100">

      <Navbar
        activeView={activeView}
        switchView={setActiveView}
        onLoginClick={() => setShowLoginModal(true)}
        user={user}
        onLogout={handleLogout}
      />

      {showLoginModal && (
        <LoginModal
          onClose={() => setShowLoginModal(false)}
          onLoginSuccess={handleLoginSuccess}
        />
      )}

      <main className="flex-1 overflow-hidden relative">
        {activeView === 'analysis' && <AnalysisView />}
        {activeView === 'chat' && <ChatView />}
        {activeView === 'sim' && <SimulatorView />}
      </main>

    </div>
  );
}

export default App;