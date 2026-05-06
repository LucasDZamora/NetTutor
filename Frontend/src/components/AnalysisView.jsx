import React, { useState, useRef } from 'react';

export default function AnalysisView() {
  const [chatLog, setChatLog] = useState([]);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      // TODO: Implement file upload to backend
      console.log('File selected:', e.target.files[0]);
    }
  };

  return (
    <div className="h-full flex flex-col p-6 fade-in">
      <div className="max-w-6xl mx-auto w-full flex flex-col gap-6 h-full">
        <div className="flex justify-between items-center bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex-shrink-0">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Análisis de Tráfico Forense</h2>
            <p className="text-gray-500 text-sm">Sube tu captura para que el tutor analice eventos en tiempo real.</p>
          </div>
          <button onClick={() => fileInputRef.current.click()}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-xl font-bold shadow-md transition-all flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24"
                 stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            Analizar archivo .pcap
          </button>
          <input type="file" ref={fileInputRef} className="hidden" onChange={handleFileChange} />
        </div>
        
        <div className="flex-1 bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col overflow-hidden min-h-0">
          <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
            {chatLog.map((log, index) => (
              <div key={index}>
                {log.type === 'system' && (
                  <div className="bg-indigo-50 text-indigo-700 p-4 rounded-xl text-sm italic">{log.text}</div>
                )}
                {log.type === 'loading' && (
                  <div className="p-4 bg-indigo-50 rounded-xl animate-pulse text-sm text-indigo-700">{log.text}</div>
                )}
                {log.type === 'result' && log.content}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
