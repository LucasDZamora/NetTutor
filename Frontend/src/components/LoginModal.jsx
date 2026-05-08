import { useState } from "react";

export default function LoginModal({ onClose, onLoginSuccess }) {
  const [nombre, setNombre] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async () => {
    setErrorMsg("");
    setIsLoading(true);

    try {
      // Llamada al Backend en Python (FastAPI)
      const response = await fetch("http://localhost:8000/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ nombre, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Error al iniciar sesión");
      }

      setNombre("");
      setPassword("");
      onLoginSuccess(data.user); 
      
    } catch (error) {
      setErrorMsg(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[9999]">
      <div className="bg-white p-6 rounded-xl w-80 shadow-2xl">
        <h2 className="text-lg font-bold mb-4 text-gray-800">Iniciar Sesión</h2>

        <input
          placeholder="Nombre de usuario"
          className="w-full border p-2 mb-2 rounded focus:ring-2 focus:ring-indigo-500 outline-none"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          disabled={isLoading}
        />

        <input
          placeholder="Contraseña"
          type="password"
          className="w-full border p-2 mb-2 rounded focus:ring-2 focus:ring-indigo-500 outline-none"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={isLoading}
        />

        {errorMsg && (
          <p className="text-red-500 text-xs mb-3 font-medium">{errorMsg}</p>
        )}

        <button
          onClick={handleLogin}
          disabled={isLoading}
          className={`w-full py-2 rounded text-white font-semibold transition-colors ${
            isLoading ? "bg-gray-400" : "bg-indigo-600 hover:bg-indigo-700"
          }`}
        >
          {isLoading ? "Validando..." : "Entrar"}
        </button>

        <button
          onClick={onClose}
          className="mt-3 text-sm text-gray-500 w-full hover:underline"
        >
          Cancelar
        </button>
      </div>
    </div>
  );
}