import React from 'react';

export default function ChatView() {
  return (
    <div className="h-full flex flex-col items-center justify-center p-6 fade-in">
      <div className="w-full max-w-4xl h-full flex flex-col bg-white rounded-3xl shadow-xl overflow-hidden border border-gray-100">
        <div className="p-6 border-b flex items-center gap-4 bg-gray-50/50 flex-shrink-0">
          <div className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold">
            AI
          </div>
          <div>
            <h3 className="font-bold text-gray-800 text-sm">Asistente General</h3>
            <p className="text-xs text-gray-400">Consulta libre sobre conceptos de redes</p>
          </div>
        </div>
        <div className="flex-1 p-8 space-y-4 overflow-y-auto custom-scrollbar min-h-0">
          {/* Los mensajes dinámicos del backend se renderizarán aquí */}
        </div>
        <div className="p-6 border-t flex-shrink-0">
          <input type="text" placeholder="Escribe tu duda aquí..."
                 className="w-full bg-gray-100 border-none rounded-2xl py-3 px-6 outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
      </div>
    </div>
  );
}
