import { useEffect, useState } from 'react'
import axios from 'axios'

function App() {
  const [data, setData] = useState('')

  useEffect(() => {
    axios.get('http://localhost:8000/')
      .then(res => setData(res.data.message))
      .catch(err => console.error(err))
  }, [])

  return (
    <div>
      <h1>Frontend en React</h1>
      <p>Respuesta del servidor: {data}</p>
    </div>
  )
}

export default App