import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import { Cargando, Diseno, Mensaje } from './componentes'

function RutaProtegida({ children, habilitada = false }) {
  if (!habilitada) {
    return children
  }

  return <Navigate to="/" replace />
}

function App() {
  const sesionActiva = false

  return (
    <BrowserRouter>
      <Diseno>
        <Routes>
          <Route path="/" element={<Mensaje tipo="info">Sistema en preparación.</Mensaje>} />
          <Route
            path="/protegido"
            element={
              <RutaProtegida habilitada={sesionActiva}>
                <Cargando texto="Cargando panel" />
              </RutaProtegida>
            }
          />
        </Routes>
      </Diseno>
    </BrowserRouter>
  )
}

export default App
