import React from 'react';

export default function Navbar({ activeView, switchView }) {
  return (
    <nav className="bg-white border-b border-gray-200 px-8 py-3 flex justify-between items-center shadow-sm z-50">
      <div className="flex items-center gap-3">
        <div className="bg-indigo-600 p-2 rounded-xl shadow-lg shadow-indigo-200">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24"
               stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                  d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <span className="text-xl font-bold text-gray-800 tracking-tight">NetTutor <span className="text-indigo-600">AI</span></span>
      </div>

      <div className="flex gap-1">
        <button onClick={() => switchView('analysis')}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all hover:bg-gray-100 ${activeView === 'analysis' ? 'active-nav' : 'text-gray-600'}`}>
          Analizar PCAP
        </button>
        <button onClick={() => switchView('chat')}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all hover:bg-gray-100 ${activeView === 'chat' ? 'active-nav' : 'text-gray-600'}`}>
          Chat General
        </button>
        <button onClick={() => switchView('sim')}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all hover:bg-gray-100 ${activeView === 'sim' ? 'active-nav' : 'text-gray-600'}`}>
          Simulador de Ataques
        </button>
      </div>

      <div className="flex items-center gap-6">
        <div className="hidden md:block text-right border-r pr-6 border-gray-100">
          <p className="text-[10px] font-bold text-gray-400 uppercase">Estado del RAG</p>
          <p className="text-xs font-semibold text-green-500 flex items-center gap-1 justify-end">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span> Conectado
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="text-sm font-semibold text-gray-600 hover:text-indigo-600 px-3">Iniciar Sesión</button>
          <button className="bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-bold shadow-sm hover:bg-slate-900 transition-all">
            Registrarse
          </button>
        </div>
      </div>
    </nav>
  );
}
