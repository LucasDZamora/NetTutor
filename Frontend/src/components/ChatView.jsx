import React, { useState, useEffect, useRef } from 'react';

export default function ChatView() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMsg = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg }),
      });
      const data = await response.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Lo siento, perdí conexión con mi base de conocimientos.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col items-center justify-center p-6 fade-in">
      <div className="w-full max-w-4xl h-full flex flex-col bg-white rounded-3xl shadow-xl overflow-hidden border border-gray-100">
        <div className="p-6 border-b flex items-center gap-4 bg-gray-50/50 flex-shrink-0">
          <div className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold shadow-lg shadow-indigo-200">AI</div>
          <div>
            <h3 className="font-bold text-gray-800 text-sm">Tutor de Conceptos</h3>
            <p className="text-xs text-gray-400 font-medium">Conectado a Documentación Oficial (RAG)</p>
          </div>
        </div>
        
        <div ref={scrollRef} className="flex-1 p-8 space-y-6 overflow-y-auto custom-scrollbar min-h-0 bg-slate-50/30">
          {messages.length === 0 && (
            <p className="text-center text-gray-400 mt-20 italic">Pregúntame sobre protocolos, capas OSI o técnicas de mitigación.</p>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] p-4 rounded-2xl text-sm leading-relaxed ${
                m.role === 'user' ? 'bg-indigo-600 text-white shadow-md' : 'bg-white border border-gray-200 text-gray-800 shadow-sm'
              }`}>
                {m.content}
              </div>
            </div>
          ))}
          {isLoading && <div className="text-xs text-indigo-500 animate-pulse font-bold">Tutor pensando...</div>}
        </div>

        <div className="p-6 border-t bg-white flex-shrink-0">
          <div className="relative">
            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Escribe tu duda técnica aquí..."
              className="w-full bg-gray-100 border-none rounded-2xl py-4 px-6 outline-none focus:ring-2 focus:ring-indigo-500 transition-all pr-16" 
            />
            <button 
              onClick={handleSend}
              className="absolute right-3 top-2 bg-indigo-600 text-white p-2 rounded-xl hover:bg-indigo-700 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" /></svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}