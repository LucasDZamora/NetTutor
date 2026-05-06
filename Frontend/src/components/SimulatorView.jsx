import React, { useState, useEffect, useRef } from 'react';

export default function SimulatorView() {
  const [currentLevel, setCurrentLevel] = useState(null);
  const [completedLevels, setCompletedLevels] = useState(new Set());
  const [chatLog, setChatLog] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [showLevelCompleteAnim, setShowLevelCompleteAnim] = useState(false);
  const [activeData, setActiveData] = useState(null); // Fetch this from backend
  const chatBoxRef = useRef(null);

  const loadAttack = (type) => {
    setCurrentLevel(type);
    // TODO: Fetch attack data (packets, guide, concepts) from the backend for 'type'
    // setActiveData(fetchedData);
    
    setChatLog([
      { sender: 'AI', text: 'He cargado el tráfico sospechoso. Analiza la tabla detalladamente. ¿Ves algo inusual en los protocolos o en la información de los paquetes? Cuéntame tu teoría.', type: 'normal' }
    ]);
  };

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [chatLog]);

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      sendSimChat();
    }
  };

  const sendSimChat = () => {
    if (!inputValue.trim() || !currentLevel) return;

    const userText = inputValue;
    setChatLog(prev => [...prev, { sender: 'User', text: userText }]);
    setInputValue('');

    // TODO: Send userText to backend to evaluate the response.
    // The backend should return whether it's correct (triggering completion) or feedback.
    console.log('Mensaje enviado al backend:', userText);
  };

  return (
    <div className="h-full flex flex-col p-6 fade-in">
      <div className="flex-1 flex flex-col gap-6 min-h-0">
        
        {/* Selector de Niveles */}
        <div className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 flex flex-col gap-3 flex-shrink-0">
          <div className="flex justify-between items-center px-1">
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Mapa de Entrenamiento por Niveles</span>
            <span className="text-[10px] font-bold text-indigo-600 bg-indigo-50 px-2 py-1 rounded">
              Progreso: {completedLevels.size} / 5
            </span>
          </div>
          <div className="grid grid-cols-5 gap-3">
            {[
              { id: 'text', label: "NIVEL 1\nTEXTO PLANO", bgHover: "hover:bg-indigo-50" },
              { id: 'phishing', label: "NIVEL 2\nPHISHING/HTTP", bgHover: "hover:bg-amber-50" },
              { id: 'scan', label: "NIVEL 3\nESCANEÓ PUERTOS", bgHover: "hover:bg-blue-50" },
              { id: 'ddos', label: "NIVEL 4\nDOS/ANOMALÍA", bgHover: "hover:bg-red-50" },
              { id: 'c2', label: "NIVEL 5\nMALWARE C2", bgHover: "hover:bg-purple-50" }
            ].map(lvl => {
              const isCompleted = completedLevels.has(lvl.id);
              const isActive = currentLevel === lvl.id;
              
              let btnClass = `px-3 py-3 bg-slate-50 border rounded-xl text-[10px] font-bold transition-all text-slate-700 ${lvl.bgHover} `;
              if (isCompleted) {
                btnClass += "bg-green-50 border-green-200 ";
              } else if (isActive) {
                btnClass += "ring-2 ring-indigo-500 bg-indigo-50 border-indigo-200 ";
              } else {
                btnClass += "border-slate-200 ";
              }

              return (
                <button key={lvl.id} onClick={() => loadAttack(lvl.id)} className={btnClass}>
                  {lvl.label.split('\n').map((line, i) => (
                    <React.Fragment key={i}>
                      {line}
                      {i === 0 && <br />}
                    </React.Fragment>
                  ))}
                  {isCompleted && ' ✅'}
                </button>
              );
            })}
          </div>
        </div>

        {/* Contenedor Principal del Simulador */}
        <div className="flex-1 flex gap-6 overflow-hidden min-h-0">
          
          {/* Centro: Tabla PCAP Realista y Chat */}
          <div className="flex-1 flex flex-col gap-4 overflow-hidden min-h-0">
            <div className="flex-1 bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col min-h-0">
              <div className="p-4 border-b bg-gray-50 flex justify-between items-center flex-shrink-0">
                <h3 className="text-xs font-bold text-gray-500 uppercase">
                  {currentLevel ? "Simulación en Ejecución" : "Simulación Detenida"}
                </h3>
                <div className="flex gap-2 items-center">
                  <span className="text-[10px] font-black bg-indigo-100 text-indigo-700 px-2 py-1 rounded">
                    {activeData ? activeData.label : "ESPERANDO SELECCIÓN"}
                  </span>
                </div>
              </div>
              <div className="flex-1 overflow-auto custom-scrollbar min-h-0">
                <table className="w-full text-left text-[11px] font-mono-custom border-collapse">
                  <thead className="bg-gray-100 sticky top-0 border-b text-gray-500 uppercase font-bold">
                    <tr>
                      <th className="px-3 py-2 border-r border-gray-200 w-12 text-center">No.</th>
                      <th className="px-3 py-2 border-r border-gray-200 w-24">Tiempo</th>
                      <th className="px-3 py-2 border-r border-gray-200 w-16">Delta</th>
                      <th className="px-3 py-2 border-r border-gray-200 w-32">Origen</th>
                      <th className="px-3 py-2 border-r border-gray-200 w-32">Destino</th>
                      <th className="px-3 py-2 border-r border-gray-200 w-16 text-center">Prot.</th>
                      <th className="px-3 py-2 border-r border-gray-200 w-16 text-right">Long.</th>
                      <th className="px-3 py-2">Información</th>
                    </tr>
                  </thead>
                  <tbody>
                    {!activeData || !activeData.packets ? (
                      <tr className="text-gray-300">
                        <td colSpan="8" className="px-4 py-20 text-center font-sans text-sm italic">
                          Carga un nivel para visualizar la captura forense.
                        </td>
                      </tr>
                    ) : (
                      activeData.packets.map((p, index) => (
                        <tr key={index} className="border-b border-gray-50 hover:bg-gray-50 cursor-pointer font-mono-custom text-[10px]">
                          <td className="px-3 py-1.5 border-r border-gray-100 text-center text-gray-400">{p.no}</td>
                          <td className="px-3 py-1.5 border-r border-gray-100 text-indigo-500">{p.time}</td>
                          <td className="px-3 py-1.5 border-r border-gray-100 text-gray-400">{p.delta}</td>
                          <td className="px-3 py-1.5 border-r border-gray-100 text-slate-700 font-medium">{p.src}</td>
                          <td className="px-3 py-1.5 border-r border-gray-100 text-slate-700 font-medium">{p.dst}</td>
                          <td className="px-3 py-1.5 border-r border-gray-100 text-center"><span className="bg-indigo-100 text-indigo-700 px-1 rounded font-bold">{p.pr}</span></td>
                          <td className="px-3 py-1.5 border-r border-gray-100 text-right text-gray-500">{p.len}</td>
                          <td className="px-3 py-1.5 text-slate-900 truncate max-w-[300px]">{p.info}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Chat de consulta inferior */}
            <div className={`h-48 bg-white rounded-2xl shadow-lg border border-indigo-100 flex flex-col overflow-hidden flex-shrink-0 ${showLevelCompleteAnim ? 'level-complete' : ''}`}>
              <div className="flex-1 p-4 overflow-y-auto custom-scrollbar text-xs space-y-3 min-h-0" ref={chatBoxRef}>
                {chatLog.length === 0 && (
                  <div className="bg-indigo-50 p-3 rounded-xl text-indigo-700">
                    <strong>NetTutor AI:</strong> Bienvenido al simulador. Encuentra la falla en la captura y explícamela para completar el nivel. No te daré la respuesta directamente, ¡tienes que investigar!
                  </div>
                )}
                {chatLog.map((msg, idx) => (
                  <div key={idx} className={msg.sender === 'User' ? 'text-right flex justify-end' : ''}>
                    {msg.sender === 'User' ? (
                      <span className="bg-gray-100 p-2 rounded-2xl inline-block max-w-[80%]">{msg.text}</span>
                    ) : msg.sender === 'System' ? (
                      <div className="p-3 bg-green-600 text-white rounded-xl shadow-lg animate-bounce" dangerouslySetInnerHTML={{ __html: msg.text }}></div>
                    ) : (
                      <span className="bg-indigo-600 text-white p-2 rounded-xl inline-block max-w-[85%]">
                        <strong>AI:</strong> {msg.text}
                      </span>
                    )}
                  </div>
                ))}
              </div>
              <div className="p-3 bg-gray-50 border-t flex gap-2 flex-shrink-0">
                <input type="text" value={inputValue} onChange={(e) => setInputValue(e.target.value)} onKeyPress={handleKeyPress}
                       placeholder="¿Qué encontraste en la captura?..."
                       className="flex-1 bg-white border border-gray-200 rounded-xl px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500" />
                <button onClick={sendSimChat}
                        className="bg-indigo-600 text-white px-5 rounded-xl font-bold text-xs hover:bg-indigo-700 transition-all">
                  Reportar Hallazgo
                </button>
              </div>
            </div>
          </div>

          {/* Derecha: Guía del Tutor (RAG) */}
          <div className="w-80 flex flex-col gap-4 flex-shrink-0">
            <div className="flex-1 bg-slate-900 rounded-3xl shadow-xl p-6 text-white flex flex-col border border-slate-700 overflow-hidden min-h-0">
              <div className="flex items-center gap-2 mb-4 flex-shrink-0">
                <div className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></div>
                <h3 className="text-sm font-bold text-indigo-400 uppercase tracking-widest">Guía del Tutor (RAG)</h3>
              </div>
              <div className="text-sm space-y-4 text-slate-300 flex-1 overflow-y-auto custom-scrollbar pr-2 leading-relaxed min-h-0">
                {!activeData || !activeData.guide ? (
                  <p>Selecciona un nivel del mapa de entrenamiento para iniciar el análisis guiado.</p>
                ) : (
                  <p dangerouslySetInnerHTML={{ __html: activeData.guide }}></p>
                )}
              </div>
              <div className="mt-6 pt-6 border-t border-slate-800 flex-shrink-0">
                <h4 className="text-[10px] font-bold text-slate-500 uppercase mb-3 tracking-widest">Pistas del Sistema</h4>
                <div className="flex flex-wrap gap-2">
                  {activeData && activeData.concepts && activeData.concepts.map((c, i) => (
                    <span key={i} className="bg-indigo-800 text-indigo-100 px-2 py-1 rounded text-[9px] font-bold uppercase tracking-wider">
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
