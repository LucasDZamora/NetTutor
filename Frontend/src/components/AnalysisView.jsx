import React, { useState, useRef } from 'react';

export default function AnalysisView() {
  const [chatLog, setChatLog] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsAnalyzing(true);
    setChatLog(prev => [...prev, { type: 'system', text: `Analizando archivo: ${file.name}...` }]);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.status === 'success') {
        setChatLog(prev => [
          ...prev,
          { 
            type: 'result', 
            content: (
              <div className="space-y-4">
                <div className="bg-white p-6 rounded-2xl border-l-4 border-indigo-500 shadow-sm prose max-w-none">
                  <h4 className="text-indigo-600 font-bold mb-2">Informe del Tutor:</h4>
                  <p className="text-gray-700 whitespace-pre-wrap">{data.narrative}</p>
                </div>
                <div className="bg-slate-900 p-4 rounded-xl text-xs font-mono text-green-400 overflow-x-auto">
                  <p className="text-slate-500 mb-2">// Metadatos Técnicos (Scapy)</p>
                  <pre>{JSON.stringify(data.technical_details, null, 2)}</pre>
                </div>
              </div>
            )
          }
        ]);
      }
    } catch (error) {
      setChatLog(prev => [...prev, { type: 'system', text: 'Error en la conexión con el servidor.' }]);
    } finally {
      setIsAnalyzing(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
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
          <button 
            onClick={() => fileInputRef.current.click()}
            disabled={isAnalyzing}
            className={`${isAnalyzing ? 'bg-gray-400' : 'bg-indigo-600 hover:bg-indigo-700'} text-white px-6 py-3 rounded-xl font-bold shadow-md transition-all flex items-center gap-2`}
          >
            {isAnalyzing ? 'Procesando...' : 'Analizar archivo .pcap'}
          </button>
          <input type="file" ref={fileInputRef} className="hidden" onChange={handleFileChange} accept=".pcap,.pcapng" />
        </div>
        
        <div className="flex-1 bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col overflow-hidden min-h-0">
          <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
            {chatLog.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-gray-400 opacity-50">
                <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p>Esperando captura de red para iniciar tutoría...</p>
              </div>
            )}
            {chatLog.map((log, index) => (
              <div key={index} className="fade-in">
                {log.type === 'system' && (
                  <div className="bg-indigo-50 text-indigo-700 p-4 rounded-xl text-sm italic border border-indigo-100">{log.text}</div>
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