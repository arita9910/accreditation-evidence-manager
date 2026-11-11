import { useEffect, useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import peticion from './api/cliente'
import { Cargando, Diseno } from './componentes'
import Auditoria from './paginas/Auditoria.jsx'
import Catalogo from './paginas/Catalogo.jsx'
import Ciclos from './paginas/Ciclos.jsx'
import Evidencias from './paginas/Evidencias.jsx'
import FichaCriterio from './paginas/FichaCriterio.jsx'
import Login from './paginas/Login.jsx'
import MiPerfil from './paginas/MiPerfil.jsx'
import Usuarios from './paginas/Usuarios.jsx'

const CLAVE_USUARIO = 'acuenta.usuario'

function obtenerUsuarioGuardado() {
  try {
    const valor = window.localStorage.getItem(CLAVE_USUARIO)
    return valor ? JSON.parse(valor) : null
  } catch {
    return null
  }
}

function RutaProtegida({ autenticado, children }) {
  if (!autenticado) {
    return <Navigate to="/login" replace />
  }

  return children
}

function App() {
  const [usuario, setUsuario] = useState(() => obtenerUsuarioGuardado())
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    if (!usuario) {
      window.localStorage.removeItem(CLAVE_USUARIO)
      setCargando(false)
      return undefined
    }

    window.localStorage.setItem(CLAVE_USUARIO, JSON.stringify(usuario))
    setCargando(false)
    return undefined
  }, [usuario])

  useEffect(() => {
    const perfil = obtenerUsuarioGuardado()
    if (!perfil) {
      setCargando(false)
      return undefined
    }

    let vigente = true
    peticion('/api/cuentas/yo/')
      .catch(() => {
        if (vigente) {
          setUsuario(null)
        }
      })
      .finally(() => {
        if (vigente) {
          setCargando(false)
        }
      })

    return () => {
      vigente = false
    }
  }, [])

  const cerrarSesion = async () => {
    try {
      await peticion('/api/sesion/', { method: 'DELETE' })
    } catch {
      // Si la sesión ya no existe, no bloquea la UI.
    } finally {
      setUsuario(null)
    }
  }

  if (cargando) {
    return <Cargando texto="Cargando sesión..." />
  }

  return (
    <BrowserRouter>
      <Diseno onLogout={cerrarSesion} usuario={usuario}>
        <Routes>
          <Route path="/" element={<Catalogo />} />
          <Route path="/login" element={<Login onLogin={setUsuario} usuario={usuario} />} />
          <Route path="/perfil" element={<RutaProtegida autenticado={Boolean(usuario)}><MiPerfil onActualizarPerfil={setUsuario} usuario={usuario} /></RutaProtegida>} />
          <Route path="/usuarios" element={<RutaProtegida autenticado={Boolean(usuario)}><Usuarios usuario={usuario} /></RutaProtegida>} />
          <Route path="/ciclos" element={<Ciclos />} />
          <Route path="/evidencias" element={<RutaProtegida autenticado={Boolean(usuario)}><Evidencias usuario={usuario} /></RutaProtegida>} />
          <Route path="/auditoria" element={<Auditoria />} />
          <Route path="/criterios/:codigo" element={<FichaCriterio />} />
          <Route path="/protegido" element={<RutaProtegida autenticado={Boolean(usuario)}><Cargando texto="Cargando panel" /></RutaProtegida>} />
        </Routes>
      </Diseno>
    </BrowserRouter>
  )
}

export default App
