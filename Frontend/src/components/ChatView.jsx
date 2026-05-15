import React, { useState, useEffect, useRef } from 'react';

export default function ChatView() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [backendReady, setBackendReady] = useState(false);
  const [backendMessage, setBackendMessage] = useState('Inicializando tutor...');

  const scrollRef = useRef(null);
  const userEmail = localStorage.getItem("userEmail");

  
  // =========================
  // AUTO SCROLL
  // =========================
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  // =========================
  // VERIFICAR STATUS BACKEND
  // =========================
  useEffect(() => {
    let interval;
    const checkBackend = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/status');
        if (!res.ok) throw new Error('Backend caído');
        const data = await res.json();

        if (data.status === 'ready') {
          setBackendReady(true);
          setBackendMessage('Tutor listo');
        } else {
          setBackendReady(false);
          setBackendMessage(data.message || 'Inicializando base vectorial...');
        }
      } catch (err) {
        setBackendReady(false);
        setBackendMessage('Backend desconectado');
      }
    };

    checkBackend();
    interval = setInterval(checkBackend, 2000);
    return () => clearInterval(interval);
  }, []);

  // =========================
  // CARGAR HISTORIAL
  // =========================
useEffect(() => {
  const cargarHistorial = async () => {
    // Buscamos el email justo cuando el componente se monta
    const emailEnStorage = localStorage.getItem("userEmail");

    if (!emailEnStorage || emailEnStorage === "undefined") {
      setMessages([]);
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/chat/history/${emailEnStorage}`);
      if (response.ok) {
        const data = await response.json();
        if (data.status === "success" && data.history) {
          const historialFormateado = data.history
            .filter(msg => msg.nodo === 'inicio')
            .map(msg => ({
              role: msg.role,
              content: msg.content
            }));
          setMessages(historialFormateado);
        }
      }
    } catch (error) {
      console.error("Error al cargar:", error);
    }
  };

  cargarHistorial();
}, []);

  // =========================
  // ENVIAR MENSAJE
  // =========================
  const handleSend = async () => {
    // 1. Obtener el email actualizado justo en el momento del click
    const emailActual = localStorage.getItem("userEmail");

    // 2. Validaciones previas
    if (!emailActual || emailActual === "undefined") {
      alert("Error: No se detectó tu sesión. Por favor, inicia sesión de nuevo.");
      return;
    }

    if (!input.trim() || isLoading) return;

    if (!backendReady) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'El tutor todavía está cargando la base de conocimientos.'
      }]);
      return;
    }

    const userMsg = input;
    setInput('');

    // Actualización optimista
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: emailActual, // Enviamos el email verificado
          message: userMsg,
          nodo_actual: "inicio"
        })
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || `Error ${response.status}`);
      }

      const data = await response.json();
      console.log("Router Intent (General Chat):", data.router);

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response || 'El tutor no devolvió contenido.'
      }]);
    } catch (error) {
      console.error("Error al enviar mensaje:", error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error del sistema: ${error.message}`
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // =========================
  // BORRAR HISTORIAL
  // =========================
  const handleDeleteHistory = async () => {
    if (!window.confirm("¿Estás seguro de que deseas borrar todo el historial de este chat?")) return;
    
    const emailActual = localStorage.getItem("userEmail");
    if (!emailActual || emailActual === "undefined") return;

    try {
      const res = await fetch(`http://localhost:8000/api/chat/history/${encodeURIComponent(emailActual)}?nodo_actual=inicio`, {
        method: 'DELETE'
      });
      if (res.ok) {
        setMessages([]);
      } else {
        alert("Error al borrar el historial");
      }
    } catch (err) {
      alert("Error de conexión");
    }
  };

  // =========================
  // MONITOR DE SESIÓN (NUEVO)
  // =========================
  useEffect(() => {
    const emailEnStorage = localStorage.getItem("userEmail");
    
    // Si no hay email (deslogueo), limpiamos los mensajes inmediatamente
    if (!emailEnStorage || emailEnStorage === "undefined") {
      setMessages([]);
    }
  }, [localStorage.getItem("userEmail")]); // Se ejecuta cuando cambia el email

  // Obtenemos el email solo para mostrarlo en el Header (UI)
  const displayEmail = localStorage.getItem("userEmail") || "Invitado";

  return (
    <div className="h-full flex flex-col items-center justify-center p-6 fade-in">
      <div className="w-full max-w-4xl h-full flex flex-col bg-white rounded-3xl shadow-xl overflow-hidden border border-gray-100">

        {/* HEADER */}
        <div className="p-6 border-b flex items-center justify-between gap-4 bg-gray-50/50 flex-shrink-0">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold shadow-lg shadow-indigo-200">
              AI
            </div>
            <div>
              <h3 className="font-bold text-gray-800 text-sm">Tutor de Ciberseguridad</h3>
              <p className="text-xs text-gray-400 font-medium">Estudiante: {displayEmail}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {messages.length > 0 && (
              <button 
                onClick={handleDeleteHistory}
                disabled={isLoading}
                className="bg-red-50 text-red-600 hover:bg-red-100 px-3 py-1.5 rounded-xl font-bold shadow-sm transition-all flex items-center gap-2 text-xs border border-red-200"
                title="Borrar Historial"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Borrar
              </button>
            )}
            <div className={`text-xs font-bold px-3 py-1 rounded-full ${
              backendReady ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
            }`}>
              {backendMessage}
            </div>
          </div>
        </div>

        {/* CHAT AREA */}
        <div ref={scrollRef} className="flex-1 p-8 space-y-6 overflow-y-auto custom-scrollbar min-h-0 bg-slate-50/30">
          {messages.length === 0 && (
            <p className="text-center text-gray-400 mt-20 italic">
              ¡Bienvenido! Pregúntame sobre protocolos, análisis de red o mitigación de ataques.
            </p>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                m.role === 'user'
                  ? 'bg-indigo-600 text-white shadow-md rounded-tr-none'
                  : 'bg-white border border-gray-200 text-gray-800 shadow-sm rounded-tl-none'
              }`}>
                {m.content}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="text-xs text-indigo-500 animate-pulse font-bold bg-indigo-50 px-3 py-1 rounded-full">
                Tutor pensando...
              </div>
            </div>
          )}
        </div>

        {/* INPUT */}
        <div className="p-6 border-t bg-white flex-shrink-0">
          <div className="relative flex gap-2">
            <input
              type="text"
              value={input}
              disabled={!backendReady || isLoading}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder={backendReady ? 'Escribe tu duda técnica aquí...' : 'Esperando al tutor...'}
              className="flex-1 bg-gray-100 border-none rounded-2xl py-4 px-6 outline-none focus:ring-2 focus:ring-indigo-500 transition-all disabled:opacity-50"
            />
            <button
              disabled={!backendReady || isLoading}
              onClick={handleSend}
              className="bg-indigo-600 text-white p-4 rounded-2xl hover:bg-indigo-700 transition-colors disabled:opacity-50 shadow-lg flex items-center justify-center"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}