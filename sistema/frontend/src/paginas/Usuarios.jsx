import { useEffect, useMemo, useState } from 'react'
import { Cargando, Mensaje } from '../componentes'
import peticion from '../api/cliente'

const ESTADO_INICIAL = {
  username: '',
  nombre: '',
  apellidos: '',
  email: '',
  activo: true,
  rol: 'director_carrera',
  carrera: '',
  password: '',
}

function normalizarTexto(valor) {
  return String(valor ?? '').trim().toLocaleLowerCase('es')
}

function Usuarios({ usuario }) {
  const [usuarios, setUsuarios] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [filtro, setFiltro] = useState('')
  const [formulario, setFormulario] = useState(ESTADO_INICIAL)
  const [editandoId, setEditandoId] = useState(null)

  const esAdmin = usuario?.rol === 'administrador_tecnico'

  const cargarUsuarios = async () => {
    setError('')
    setCargando(true)
    try {
      const datos = await peticion('/api/usuarios/')
      setUsuarios(datos)
    } catch (errorRecibido) {
      setError(errorRecibido.message)
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => {
    if (!esAdmin) {
      return undefined
    }

    cargarUsuarios()
    return undefined
  }, [esAdmin])

  const usuariosFiltrados = useMemo(() => {
    const consulta = normalizarTexto(filtro)
    return usuarios.filter((registro) => {
      const hayTexto = !consulta || [
        registro.username,
        registro.nombre,
        registro.apellidos,
        registro.email,
      ].some((valor) => normalizarTexto(valor).includes(consulta))

      return hayTexto
    })
  }, [usuarios, filtro])

  const manejarCambio = (evento) => {
    const { name, value, type, checked } = evento.target
    setFormulario((actual) => ({
      ...actual,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const restablecerFormulario = () => {
    setEditandoId(null)
    setFormulario(ESTADO_INICIAL)
  }

  const guardarUsuario = async (evento) => {
    evento.preventDefault()
    setError('')
    setMensaje('')

    const payload = {
      ...formulario,
      carrera: formulario.rol === 'director_carrera' && formulario.carrera ? Number(formulario.carrera) : null,
    }

    if (!payload.username || !payload.email) {
      setError('El nombre de usuario y el correo son obligatorios.')
      return
    }

    if (!editandoId && !payload.password) {
      setError('La contraseña es obligatoria para crear un usuario.')
      return
    }

    try {
      if (editandoId) {
        const datosActualizacion = { ...payload }
        if (!datosActualizacion.password) {
          delete datosActualizacion.password
        }
        await peticion(`/api/usuarios/${editandoId}/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(datosActualizacion),
        })
        setMensaje('El usuario se actualizó correctamente.')
      } else {
        await peticion('/api/usuarios/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        setMensaje('El usuario se creó correctamente.')
      }

      restablecerFormulario()
      await cargarUsuarios()
    } catch (errorRecibido) {
      setError(errorRecibido.message)
    }
  }

  const editarUsuario = (registro) => {
    setEditandoId(registro.id)
    setFormulario({
      username: registro.username,
      nombre: registro.nombre ?? '',
      apellidos: registro.apellidos ?? '',
      email: registro.email ?? '',
      activo: Boolean(registro.activo),
      rol: registro.rol ?? 'director_carrera',
      carrera: registro.carrera ?? '',
      password: '',
    })
  }

  const asignarRol = async (usuarioId, rol, carreraId) => {
    setError('')
    setMensaje('')

    try {
      await peticion(`/api/usuarios/${usuarioId}/roles/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rol, carrera: carreraId || null }),
      })
      setMensaje('Rol actualizado correctamente.')
      await cargarUsuarios()
    } catch (errorRecibido) {
      setError(errorRecibido.message)
    }
  }

  const revocarAcceso = async (usuarioId) => {
    setError('')
    setMensaje('')

    try {
      await peticion(`/api/usuarios/${usuarioId}/roles/`, { method: 'DELETE' })
      setMensaje('Se revocó el acceso del usuario.')
      await cargarUsuarios()
    } catch (errorRecibido) {
      setError(errorRecibido.message)
    }
  }

  if (!esAdmin) {
    return (
      <Mensaje tipo="error" titulo="Acceso restringido">
        Solo el administrador técnico puede gestionar usuarios y roles.
      </Mensaje>
    )
  }

  return (
    <section className="row g-4">
      <div className="col-xl-5">
        <div className="card shadow-sm">
          <div className="card-body">
            <h1 className="h3 mb-3">Gestión de usuarios</h1>
            {mensaje ? <Mensaje tipo="success">{mensaje}</Mensaje> : null}
            {error ? <Mensaje tipo="error">{error}</Mensaje> : null}

            <form onSubmit={guardarUsuario}>
              <div className="mb-3">
                <label className="form-label" htmlFor="usuario-username">Usuario</label>
                <input
                  className="form-control"
                  id="usuario-username"
                  name="username"
                  onChange={manejarCambio}
                  required
                  value={formulario.username}
                />
              </div>

              <div className="row g-2">
                <div className="col-md-6 mb-3">
                  <label className="form-label" htmlFor="usuario-nombre">Nombre</label>
                  <input
                    className="form-control"
                    id="usuario-nombre"
                    name="nombre"
                    onChange={manejarCambio}
                    value={formulario.nombre}
                  />
                </div>

                <div className="col-md-6 mb-3">
                  <label className="form-label" htmlFor="usuario-apellidos">Apellidos</label>
                  <input
                    className="form-control"
                    id="usuario-apellidos"
                    name="apellidos"
                    onChange={manejarCambio}
                    value={formulario.apellidos}
                  />
                </div>
              </div>

              <div className="mb-3">
                <label className="form-label" htmlFor="usuario-email">Correo</label>
                <input
                  className="form-control"
                  id="usuario-email"
                  name="email"
                  onChange={manejarCambio}
                  required
                  type="email"
                  value={formulario.email}
                />
              </div>

              <div className="row g-2">
                <div className="col-md-6 mb-3">
                  <label className="form-label" htmlFor="usuario-rol">Rol</label>
                  <select
                    className="form-select"
                    id="usuario-rol"
                    name="rol"
                    onChange={manejarCambio}
                    value={formulario.rol}
                  >
                    <option value="administrador_tecnico">Administrador técnico</option>
                    <option value="director_carrera">Director de carrera</option>
                  </select>
                </div>

                <div className="col-md-6 mb-3">
                  <label className="form-label" htmlFor="usuario-carrera">Carrera</label>
                  <input
                    className="form-control"
                    disabled={formulario.rol !== 'director_carrera'}
                    id="usuario-carrera"
                    name="carrera"
                    onChange={manejarCambio}
                    placeholder="ID de la carrera"
                    type="number"
                    value={formulario.carrera}
                  />
                </div>
              </div>

              {!editandoId ? (
                <div className="mb-3">
                  <label className="form-label" htmlFor="usuario-password">Contraseña</label>
                  <input
                    className="form-control"
                    id="usuario-password"
                    name="password"
                    onChange={manejarCambio}
                    required
                    type="password"
                    value={formulario.password}
                  />
                </div>
              ) : null}

              <div className="form-check mb-3">
                <input
                  checked={formulario.activo}
                  className="form-check-input"
                  id="usuario-activo"
                  name="activo"
                  onChange={manejarCambio}
                  type="checkbox"
                />
                <label className="form-check-label" htmlFor="usuario-activo">
                  Usuario activo
                </label>
              </div>

              <div className="d-flex gap-2">
                <button className="btn btn-primary" type="submit">
                  {editandoId ? 'Guardar cambios' : 'Crear usuario'}
                </button>
                {editandoId ? (
                  <button className="btn btn-outline-secondary" onClick={restablecerFormulario} type="button">
                    Cancelar
                  </button>
                ) : null}
              </div>
            </form>
          </div>
        </div>
      </div>

      <div className="col-xl-7">
        <div className="card shadow-sm">
          <div className="card-body">
            <div className="d-flex justify-content-between align-items-center gap-3 mb-3 flex-wrap">
              <h2 className="h4 mb-0">Listado</h2>
              <input
                aria-label="Filtrar usuarios"
                className="form-control w-auto"
                onChange={(evento) => setFiltro(evento.target.value)}
                placeholder="Buscar usuario"
                type="search"
                value={filtro}
              />
            </div>

            {cargando ? (
              <Cargando texto="Cargando usuarios..." />
            ) : usuariosFiltrados.length === 0 ? (
              <Mensaje tipo="info">No hay usuarios que coincidan con el filtro.</Mensaje>
            ) : (
              <div className="table-responsive">
                <table className="table align-middle">
                  <thead>
                    <tr>
                      <th>Usuario</th>
                      <th>Rol</th>
                      <th>Carrera</th>
                      <th>Estado</th>
                      <th className="text-end">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {usuariosFiltrados.map((registro) => (
                      <tr key={registro.id}>
                        <td>
                          <strong>{registro.username}</strong>
                          <div className="text-body-secondary small">
                            {registro.nombre} {registro.apellidos}
                          </div>
                        </td>
                        <td>
                          <select
                            className="form-select form-select-sm"
                            defaultValue={registro.rol}
                            onChange={(evento) => asignarRol(registro.id, evento.target.value, registro.carrera)}
                          >
                            <option value="administrador_tecnico">Administrador técnico</option>
                            <option value="director_carrera">Director de carrera</option>
                          </select>
                        </td>
                        <td>{registro.carrera ?? '—'}</td>
                        <td>
                          <span className={`badge ${registro.activo ? 'text-bg-success' : 'text-bg-secondary'}`}>
                            {registro.activo ? 'Activo' : 'Inactivo'}
                          </span>
                        </td>
                        <td className="text-end">
                          <div className="d-flex gap-2 justify-content-end">
                            <button className="btn btn-sm btn-outline-primary" onClick={() => editarUsuario(registro)} type="button">
                              Editar
                            </button>
                            <button className="btn btn-sm btn-outline-danger" onClick={() => revocarAcceso(registro.id)} type="button">
                              Revocar acceso
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}

export default Usuarios
