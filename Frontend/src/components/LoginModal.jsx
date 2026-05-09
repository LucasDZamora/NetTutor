import { useState } from "react";

export default function LoginModal({ onClose, onLoginSuccess }) {
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e) => {
    // Si lo usas dentro de un form, evitamos el refresh
    if (e) e.preventDefault();
    setErrorMsg("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: correo, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Error al iniciar sesión");
      }

      setCorreo("");
      setPassword("");
      onLoginSuccess(data.user); 
      
    } catch (error) {
      setErrorMsg(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    // Se añade backdrop-blur-sm y bg-black/40 para la distorsión igual al registro
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-[100] p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-[400px] p-8 animate-in fade-in zoom-in duration-200">
        
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Iniciar Sesión</h2>

        <form onSubmit={handleLogin} className="flex flex-col gap-4">
          <input
            placeholder="Correo"
            type="email"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg outline-none focus:border-indigo-600 transition-colors"
            value={correo}
            onChange={(e) => setCorreo(e.target.value)}
            disabled={isLoading}
            required
          />

          <input
            placeholder="Contraseña"
            type="password"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg outline-none focus:border-indigo-600 transition-colors"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isLoading}
            required
          />

          {errorMsg && (
            <p className="text-red-500 text-sm font-medium animate-pulse">{errorMsg}</p>
          )}

          {/* Botón con el color índigo exacto y efecto de escala al apretar */}
          <button
            type="submit"
            disabled={isLoading}
            className={`w-full py-3 rounded-lg text-white font-bold shadow-md transition-all active:scale-[0.98] ${
              isLoading ? "bg-gray-400" : "bg-[#4f46e5] hover:bg-[#4338ca]"
            }`}
          >
            {isLoading ? "Validando..." : "Entrar"}
          </button>

          <button
            type="button"
            onClick={onClose}
            className="text-gray-500 text-sm font-medium hover:text-gray-700 transition-colors mt-2"
          >
            Cancelar
          </button>
        </form>
      </div>
    </div>
  );
}