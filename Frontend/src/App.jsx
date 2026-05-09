import React, { useState } from 'react';
import Navbar from './components/Navbar';
import AnalysisView from './components/AnalysisView';
import ChatView from './components/ChatView';
import SimulatorView from './components/SimulatorView';
import LoginModal from './components/LoginModal';
import RegisterModal from './components/RegisterModal'; // Importar el nuevo modal

function App() {
  const [activeView, setActiveView] = useState('analysis');
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false); // Estado para el registro
  
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
        onRegisterClick={() => setShowRegisterModal(true)} // Nueva prop para el Navbar
        user={user}
        onLogout={handleLogout}
      />

      {showLoginModal && (
        <LoginModal
          onClose={() => setShowLoginModal(false)}
          onLoginSuccess={handleLoginSuccess}
        />
      )}

      {/* Nuevo componente de registro */}
      {showRegisterModal && (
        <RegisterModal
          onClose={() => setShowRegisterModal(false)}
          onSwitchToLogin={() => {
            setShowRegisterModal(false);
            setShowLoginModal(true);
          }}
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