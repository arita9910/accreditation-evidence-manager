import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Cargando, Diseno } from './componentes'
import Catalogo from './paginas/Catalogo.jsx'
import FichaCriterio from './paginas/FichaCriterio.jsx'

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
          <Route path="/" element={<Catalogo />} />
          <Route path="/criterios/:codigo" element={<FichaCriterio />} />
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
