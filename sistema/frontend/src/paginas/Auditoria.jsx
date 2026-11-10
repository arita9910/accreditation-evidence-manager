import { useEffect, useMemo, useState } from 'react'
import { Cargando, Mensaje } from '../componentes'
import peticion from '../api/cliente'

const FILTROS_INICIALES = {
  usuario: '',
  accion: '',
  desde: '',
  hasta: '',
  resultado: '',
}

const TAMANO_PAGINA = 20

function construirQuery(filtros, pagina) {
  const query = new URLSearchParams()
  const usuario = filtros.usuario.trim()
  const accion = filtros.accion.trim()

  if (usuario) {
    query.set('usuario', usuario)
  }
  if (accion) {
    query.set('accion', accion)
  }
  if (filtros.desde) {
    query.set('desde', `${filtros.desde}T00:00:00`)
  }
  if (filtros.hasta) {
    query.set('hasta', `${filtros.hasta}T23:59:59`)
  }
  if (filtros.resultado) {
    query.set('resultado', filtros.resultado)
  }
  query.set('page', String(pagina))

  return query.toString()
}

function formatearFecha(valor) {
  if (!valor) {
    return '—'
  }
  const fecha = new Date(valor)
  if (Number.isNaN(fecha.getTime())) {
    return valor
  }
  return fecha.toLocaleString('es-PE')
}

function formatearDetalle(detalle) {
  if (!detalle) {
    return '—'
  }
  return JSON.stringify(detalle)
}

function Auditoria() {
  const [filtros, setFiltros] = useState(FILTROS_INICIALES)
  const [filtrosAplicados, setFiltrosAplicados] = useState(FILTROS_INICIALES)
  const [registros, setRegistros] = useState([])
  const [conteoTotal, setConteoTotal] = useState(0)
  const [paginaActual, setPaginaActual] = useState(1)
  const [haySiguiente, setHaySiguiente] = useState(false)
  const [hayAnterior, setHayAnterior] = useState(false)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)

  const totalPaginas = useMemo(() => {
    if (conteoTotal === 0) {
      return 1
    }
    return Math.ceil(conteoTotal / TAMANO_PAGINA)
  }, [conteoTotal])

  const cargarRegistros = async (nuevosFiltros, pagina) => {
    setCargando(true)
    setError(null)
    try {
      const query = construirQuery(nuevosFiltros, pagina)
      const respuesta = await peticion(`/api/auditoria/?${query}`)
      setRegistros(Array.isArray(respuesta?.results) ? respuesta.results : [])
      setConteoTotal(Number(respuesta?.count) || 0)
      setPaginaActual(pagina)
      setHaySiguiente(Boolean(respuesta?.next))
      setHayAnterior(Boolean(respuesta?.previous))
      setFiltrosAplicados(nuevosFiltros)
    } catch (errorRecibido) {
      setError(errorRecibido.message)
      setRegistros([])
      setConteoTotal(0)
      setHaySiguiente(false)
      setHayAnterior(false)
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => {
    let vigente = true
    const cargarInicial = async () => {
      if (!vigente) {
        return
      }
      await cargarRegistros(FILTROS_INICIALES, 1)
    }
    cargarInicial()
    return () => {
      vigente = false
    }
  }, [])

  const enviarFiltros = async (evento) => {
    evento.preventDefault()
    await cargarRegistros(filtros, 1)
  }

  const irAPaginaAnterior = async () => {
    if (!hayAnterior || paginaActual <= 1) {
      return
    }
    await cargarRegistros(filtrosAplicados, paginaActual - 1)
  }

  const irAPaginaSiguiente = async () => {
    if (!haySiguiente || paginaActual >= totalPaginas) {
      return
    }
    await cargarRegistros(filtrosAplicados, paginaActual + 1)
  }

  return (
    <section aria-labelledby="titulo-auditoria" className="d-grid gap-4">
      <header>
        <h1 id="titulo-auditoria">Consulta de auditoría</h1>
        <p className="text-body-secondary mb-0">
          Filtra registros por usuario, acción, fecha y resultado.
        </p>
      </header>

      <section aria-labelledby="titulo-filtros-auditoria" className="card">
        <div className="card-body">
          <h2 className="h5" id="titulo-filtros-auditoria">Filtros</h2>
          <form className="row g-3" onSubmit={enviarFiltros}>
            <div className="col-md-3">
              <label className="form-label" htmlFor="auditoria-usuario">Usuario</label>
              <input
                className="form-control"
                id="auditoria-usuario"
                onChange={(evento) => setFiltros((previo) => ({ ...previo, usuario: evento.target.value }))}
                type="text"
                value={filtros.usuario}
              />
            </div>
            <div className="col-md-3">
              <label className="form-label" htmlFor="auditoria-accion">Acción</label>
              <input
                className="form-control"
                id="auditoria-accion"
                onChange={(evento) => setFiltros((previo) => ({ ...previo, accion: evento.target.value }))}
                type="text"
                value={filtros.accion}
              />
            </div>
            <div className="col-md-2">
              <label className="form-label" htmlFor="auditoria-desde">Desde</label>
              <input
                className="form-control"
                id="auditoria-desde"
                onChange={(evento) => setFiltros((previo) => ({ ...previo, desde: evento.target.value }))}
                type="date"
                value={filtros.desde}
              />
            </div>
            <div className="col-md-2">
              <label className="form-label" htmlFor="auditoria-hasta">Hasta</label>
              <input
                className="form-control"
                id="auditoria-hasta"
                onChange={(evento) => setFiltros((previo) => ({ ...previo, hasta: evento.target.value }))}
                type="date"
                value={filtros.hasta}
              />
            </div>
            <div className="col-md-2">
              <label className="form-label" htmlFor="auditoria-resultado">Resultado</label>
              <select
                className="form-select"
                id="auditoria-resultado"
                onChange={(evento) => setFiltros((previo) => ({ ...previo, resultado: evento.target.value }))}
                value={filtros.resultado}
              >
                <option value="">Todos</option>
                <option value="correcto">Correcto</option>
                <option value="denegado">Denegado</option>
              </select>
            </div>
            <div className="col-12">
              <button className="btn btn-primary" type="submit">Aplicar filtros</button>
            </div>
          </form>
        </div>
      </section>

      <section aria-labelledby="titulo-listado-auditoria" className="card">
        <div className="card-body">
          <h2 className="h5" id="titulo-listado-auditoria">Listado</h2>
          {cargando ? <Cargando texto="Cargando auditoría..." /> : null}
          {error ? (
            <Mensaje tipo="error" titulo="No se pudo cargar la auditoría.">{error}</Mensaje>
          ) : null}
          {!cargando && !error ? (
            <>
              <p aria-live="polite" className="text-body-secondary">
                {conteoTotal} registros · Página {paginaActual} de {totalPaginas}
              </p>
              {registros.length === 0 ? (
                <Mensaje tipo="info">No hay registros para los filtros seleccionados.</Mensaje>
              ) : (
                <div className="table-responsive">
                  <table className="table table-sm align-middle">
                    <thead>
                      <tr>
                        <th scope="col">Fecha y hora</th>
                        <th scope="col">Usuario</th>
                        <th scope="col">Acción</th>
                        <th scope="col">Entidad</th>
                        <th scope="col">Resultado</th>
                        <th scope="col">Detalle</th>
                      </tr>
                    </thead>
                    <tbody>
                      {registros.map((registro) => (
                        <tr key={registro.id}>
                          <td>{formatearFecha(registro.fecha_hora)}</td>
                          <td>{registro.usuario || '—'}</td>
                          <td>{registro.accion || '—'}</td>
                          <td>{registro.entidad || '—'}</td>
                          <td>
                            <span className={`badge ${registro.resultado === 'correcto' ? 'text-bg-success' : 'text-bg-warning'}`}>
                              {registro.resultado || '—'}
                            </span>
                          </td>
                          <td>{formatearDetalle(registro.detalle)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <nav aria-label="Paginación de auditoría" className="d-flex align-items-center gap-2">
                <button
                  className="btn btn-outline-secondary btn-sm"
                  disabled={!hayAnterior}
                  onClick={irAPaginaAnterior}
                  type="button"
                >
                  Anterior
                </button>
                <span className="small text-body-secondary">Página {paginaActual}</span>
                <button
                  className="btn btn-outline-secondary btn-sm"
                  disabled={!haySiguiente}
                  onClick={irAPaginaSiguiente}
                  type="button"
                >
                  Siguiente
                </button>
              </nav>
            </>
          ) : null}
        </div>
      </section>
    </section>
  )
}

export default Auditoria
