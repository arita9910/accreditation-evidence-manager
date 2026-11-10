import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { Cargando, Mensaje } from '../componentes'
import peticion from '../api/cliente'

const inicial = {
  password_actual: '',
  password_nueva: '',
}

function MiPerfil({ usuario, onActualizarPerfil }) {
  const [perfil, setPerfil] = useState(usuario)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [formulario, setFormulario] = useState(inicial)

  useEffect(() => {
    let vigente = true

    if (!usuario) {
      return undefined
    }

    peticion('/api/cuentas/yo/')
      .then((datos) => {
        if (vigente) {
          setPerfil(datos)
          onActualizarPerfil(datos)
        }
      })
      .catch((errorRecibido) => {
        if (vigente) {
          setError(errorRecibido.message)
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
  }, [usuario, onActualizarPerfil])

  if (!usuario) {
    return <Navigate to="/login" replace />
  }

  const actualizarCampo = (evento) => {
    const { name, value } = evento.target
    setFormulario((actual) => ({ ...actual, [name]: value }))
  }

  const cambiarClave = async (evento) => {
    evento.preventDefault()
    setError('')
    setMensaje('')

    try {
      await peticion('/api/cuentas/cambiar-clave/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formulario),
      })
      setMensaje('La contraseña se actualizó correctamente.')
      setFormulario(inicial)
    } catch (errorRecibido) {
      setError(errorRecibido.message)
    }
  }

  if (cargando) {
    return <Cargando texto="Cargando perfil..." />
  }

  const rolTitulo = perfil?.rol === 'administrador_tecnico'
    ? 'Administrador técnico'
    : perfil?.rol === 'director_carrera'
      ? 'Director de carrera'
      : 'Usuario'

  return (
    <section className="row g-4">
      <div className="col-lg-5">
        <div className="card h-100 shadow-sm">
          <div className="card-body">
            <h1 className="h3 mb-3">Mi perfil</h1>
            <dl className="row mb-0">
              <dt className="col-sm-4">Usuario</dt>
              <dd className="col-sm-8">{perfil?.username || '—'}</dd>

              <dt className="col-sm-4">Nombre</dt>
              <dd className="col-sm-8">{perfil?.nombre || '—'} {perfil?.apellidos || ''}</dd>

              <dt className="col-sm-4">Correo</dt>
              <dd className="col-sm-8">{perfil?.email || '—'}</dd>

              <dt className="col-sm-4">Rol</dt>
              <dd className="col-sm-8">{rolTitulo}</dd>

              <dt className="col-sm-4">Carrera</dt>
              <dd className="col-sm-8">{perfil?.carrera || 'Sin carrera asignada'}</dd>
            </dl>
          </div>
        </div>
      </div>

      <div className="col-lg-7">
        <div className="card shadow-sm">
          <div className="card-body">
            <h2 className="h4 mb-3">Cambiar contraseña</h2>

            {error ? (
              <Mensaje tipo="error" titulo="No se pudo cambiar la contraseña">{error}</Mensaje>
            ) : null}

            {mensaje ? (
              <Mensaje tipo="success" titulo="Contraseña actualizada">{mensaje}</Mensaje>
            ) : null}

            <form onSubmit={cambiarClave}>
              <div className="mb-3">
                <label className="form-label" htmlFor="perfil-password-actual">Contraseña actual</label>
                <input
                  className="form-control"
                  id="perfil-password-actual"
                  name="password_actual"
                  onChange={actualizarCampo}
                  required
                  type="password"
                  value={formulario.password_actual}
                />
              </div>

              <div className="mb-3">
                <label className="form-label" htmlFor="perfil-password-nueva">Nueva contraseña</label>
                <input
                  className="form-control"
                  id="perfil-password-nueva"
                  name="password_nueva"
                  minLength={8}
                  onChange={actualizarCampo}
                  required
                  type="password"
                  value={formulario.password_nueva}
                />
              </div>

              <button className="btn btn-primary" type="submit">
                Guardar nueva contraseña
              </button>
            </form>
          </div>
        </div>
      </div>
    </section>
  )
}

export default MiPerfil
