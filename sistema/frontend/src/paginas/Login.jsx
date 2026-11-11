import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { Mensaje } from '../componentes'
import peticion from '../api/cliente'

function Login({ usuario, onLogin }) {
  const [formulario, setFormulario] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  if (usuario) {
    return <Navigate to="/perfil" replace />
  }

  const actualizarCampo = (evento) => {
    const { name, value } = evento.target
    setFormulario((actual) => ({ ...actual, [name]: value }))
  }

  const enviar = async (evento) => {
    evento.preventDefault()
    setError('')
    setCargando(true)

    try {
      const respuesta = await peticion('/api/sesion/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formulario),
      })
      const perfil = respuesta?.usuario || { username: formulario.username }
      onLogin(perfil)
    } catch (errorRecibido) {
      setError(errorRecibido.message)
    } finally {
      setCargando(false)
    }
  }

  return (
    <section className="row justify-content-center">
      <div className="col-lg-5 col-md-7">
        <div className="card shadow-sm">
          <div className="card-body p-4">
            <h1 className="h3 mb-3">Iniciar sesión</h1>
            <p className="text-body-secondary">
              Accede para consultar tu perfil y gestionar usuarios si eres administrador técnico.
            </p>

            {error ? (
              <Mensaje tipo="error" titulo="No se pudo iniciar sesión">{error}</Mensaje>
            ) : null}

            <form onSubmit={enviar}>
              <div className="mb-3">
                <label className="form-label" htmlFor="login-usuario">Usuario</label>
                <input
                  className="form-control"
                  id="login-usuario"
                  name="username"
                  onChange={actualizarCampo}
                  required
                  value={formulario.username}
                />
              </div>

              <div className="mb-3">
                <label className="form-label" htmlFor="login-password">Contraseña</label>
                <input
                  className="form-control"
                  id="login-password"
                  name="password"
                  onChange={actualizarCampo}
                  required
                  type="password"
                  value={formulario.password}
                />
              </div>

              <button className="btn btn-primary w-100" disabled={cargando} type="submit">
                {cargando ? 'Iniciando sesión...' : 'Entrar'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </section>
  )
}

export default Login
