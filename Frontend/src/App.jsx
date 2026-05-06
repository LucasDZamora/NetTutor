import React, { useState } from 'react';
import Navbar from './components/Navbar';
import AnalysisView from './components/AnalysisView';
import ChatView from './components/ChatView';
import SimulatorView from './components/SimulatorView';

function App() {
  const [activeView, setActiveView] = useState('analysis');

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-gray-100">
      <Navbar activeView={activeView} switchView={setActiveView} />
      
      <main className="flex-1 overflow-hidden relative">
        {activeView === 'analysis' && <AnalysisView />}
        {activeView === 'chat' && <ChatView />}
        {activeView === 'sim' && <SimulatorView />}
      </main>
    </div>
  );
}

export default App;