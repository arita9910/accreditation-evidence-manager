import { useEffect, useMemo, useState } from 'react'
import { Cargando, Mensaje } from '../componentes'
import peticion from '../api/cliente'

const FORMULARIO_INICIAL = {
  ciclo: '',
  tipo_evidencia: '',
  titulo: '',
  descripcion: '',
  curso_academico: '',
  periodo_desde: '',
  periodo_hasta: '',
  soporte: 'digital',
  custodia_original: '',
  archivo: null,
}

const FILTROS_INICIALES = {
  q: '',
  soporte: '',
  ciclo: '',
  curso: '',
  criterio: '',
}

function extraerLista(respuesta) {
  if (Array.isArray(respuesta)) {
    return respuesta
  }
  if (Array.isArray(respuesta?.results)) {
    return respuesta.results
  }
  return []
}

function formatearFecha(valor) {
  if (!valor) {
    return '—'
  }
  const fecha = new Date(valor)
  if (Number.isNaN(fecha.getTime())) {
    return valor
  }
  return fecha.toLocaleDateString('es-PE')
}

function construirQuery(filtros) {
  const query = new URLSearchParams()
  const texto = filtros.q.trim()
  if (texto) {
    query.set('q', texto)
  }
  if (filtros.soporte) {
    query.set('soporte', filtros.soporte)
  }
  if (filtros.ciclo) {
    query.set('ciclo', filtros.ciclo)
  }
  if (filtros.curso) {
    query.set('curso', filtros.curso)
  }
  if (filtros.criterio) {
    query.set('criterio', filtros.criterio)
  }
  return query.toString()
}

function Evidencias({ usuario }) {
  const [filtros, setFiltros] = useState(FILTROS_INICIALES)
  const [filtrosAplicados, setFiltrosAplicados] = useState(FILTROS_INICIALES)
  const [evidencias, setEvidencias] = useState([])
  const [ciclos, setCiclos] = useState([])
  const [cargando, setCargando] = useState(true)
  const [cargandoDetalle, setCargandoDetalle] = useState(false)
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState('')
  const [errorDetalle, setErrorDetalle] = useState('')
  const [errorFormulario, setErrorFormulario] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [detalle, setDetalle] = useState(null)
  const [evidenciaSeleccionadaId, setEvidenciaSeleccionadaId] = useState(null)
  const [formulario, setFormulario] = useState(FORMULARIO_INICIAL)

  const puedeEditar = usuario?.rol === 'administrador_tecnico' || usuario?.rol === 'director_carrera'

  const cargarBase = async (filtrosConsulta) => {
    setCargando(true)
    setError('')
    try {
      const query = construirQuery(filtrosConsulta)
      const [respuestaEvidencias, respuestaCiclos] = await Promise.all([
        peticion(`/api/evidencias/${query ? `?${query}` : ''}`),
        peticion('/api/ciclos/'),
      ])
      setEvidencias(extraerLista(respuestaEvidencias))
      setCiclos(extraerLista(respuestaCiclos))
      setFiltrosAplicados(filtrosConsulta)
    } catch (errorRecibido) {
      setError(errorRecibido.message)
      setEvidencias([])
    } finally {
      setCargando(false)
    }
  }

  const cargarDetalle = async (evidenciaId) => {
    if (!evidenciaId) {
      setDetalle(null)
      return
    }
    setCargandoDetalle(true)
    setErrorDetalle('')
    try {
      const datos = await peticion(`/api/evidencias/${evidenciaId}/`)
      setDetalle(datos)
    } catch (errorRecibido) {
      setErrorDetalle(errorRecibido.message)
      setDetalle(null)
    } finally {
      setCargandoDetalle(false)
    }
  }

  useEffect(() => {
    cargarBase(FILTROS_INICIALES)
  }, [])

  const enviarFiltros = async (evento) => {
    evento.preventDefault()
    await cargarBase(filtros)
  }

  const seleccionarEvidencia = async (evidencia) => {
    setEvidenciaSeleccionadaId(evidencia.id)
    await cargarDetalle(evidencia.id)
  }

  const cicloSeleccionado = useMemo(
    () => ciclos.find((item) => String(item.id) === String(formulario.ciclo)),
    [ciclos, formulario.ciclo],
  )

  const manejarCambioFormulario = (evento) => {
    const { name, value } = evento.target
    setFormulario((previo) => ({ ...previo, [name]: value }))
  }

  const manejarArchivo = (evento) => {
    const [archivo] = evento.target.files ?? []
    setFormulario((previo) => ({ ...previo, archivo: archivo ?? null }))
  }

  const limpiarFormulario = () => {
    setFormulario(FORMULARIO_INICIAL)
  }

  const crearEvidencia = async (evento) => {
    evento.preventDefault()
    setMensaje('')
    setErrorFormulario('')

    if (!formulario.ciclo || !formulario.tipo_evidencia || !formulario.titulo.trim()) {
      setErrorFormulario('Debe completar ciclo, tipo de evidencia y título.')
      return
    }

    if (formulario.soporte === 'digital' && !formulario.archivo) {
      setErrorFormulario('Debe adjuntar un archivo para evidencias digitales.')
      return
    }

    if (formulario.soporte === 'papel' && !formulario.custodia_original.trim()) {
      setErrorFormulario('Debe indicar la custodia original para evidencias en papel.')
      return
    }

    setGuardando(true)
    try {
      const cuerpo = new FormData()
      cuerpo.set('ciclo', formulario.ciclo)
      cuerpo.set('tipo_evidencia', formulario.tipo_evidencia)
      cuerpo.set('titulo', formulario.titulo.trim())
      cuerpo.set('descripcion', formulario.descripcion.trim())
      cuerpo.set('curso_academico', formulario.curso_academico)
      cuerpo.set('periodo_desde', formulario.periodo_desde)
      cuerpo.set('periodo_hasta', formulario.periodo_hasta)
      cuerpo.set('soporte', formulario.soporte)
      if (formulario.soporte === 'papel') {
        cuerpo.set('custodia_original', formulario.custodia_original.trim())
      }
      if (formulario.archivo) {
        cuerpo.set('archivo', formulario.archivo)
      }

      const creada = await peticion('/api/evidencias/', {
        method: 'POST',
        body: cuerpo,
      })

      setMensaje('Evidencia creada correctamente.')
      setErrorFormulario('')
      limpiarFormulario()
      await cargarBase(filtrosAplicados)
      if (creada?.id) {
        setEvidenciaSeleccionadaId(creada.id)
        await cargarDetalle(creada.id)
      }
    } catch (errorRecibido) {
      setErrorFormulario(errorRecibido.message)
    } finally {
      setGuardando(false)
    }
  }

  return (
    <section aria-labelledby="titulo-evidencias" className="d-grid gap-4">
      <header>
        <h1 id="titulo-evidencias">Gestión de evidencias</h1>
        <p className="text-body-secondary mb-0">
          Busca evidencias del ciclo, identifica soporte en papel y revisa historial de versiones.
        </p>
      </header>

      {mensaje ? <Mensaje tipo="success">{mensaje}</Mensaje> : null}

      <section aria-labelledby="titulo-filtros-evidencias" className="card">
        <div className="card-body">
          <h2 className="h5" id="titulo-filtros-evidencias">Listado y filtros</h2>
          <form className="row g-3" onSubmit={enviarFiltros}>
            <div className="col-md-4">
              <label className="form-label" htmlFor="evidencias-q">Búsqueda</label>
              <input
                className="form-control"
                id="evidencias-q"
                onChange={(evento) => setFiltros((previo) => ({ ...previo, q: evento.target.value }))}
                placeholder="Título o descripción"
                value={filtros.q}
              />
            </div>
            <div className="col-md-2">
              <label className="form-label" htmlFor="evidencias-soporte">Soporte</label>
              <select
                className="form-select"
                id="evidencias-soporte"
                onChange={(evento) => setFiltros((previo) => ({ ...previo, soporte: evento.target.value }))}
                value={filtros.soporte}
              >
                <option value="">Todos</option>
                <option value="digital">Digital</option>
                <option value="papel">Papel</option>
              </select>
            </div>
            <div className="col-md-2">
              <label className="form-label" htmlFor="evidencias-ciclo">Ciclo</label>
              <select
                className="form-select"
                id="evidencias-ciclo"
                onChange={(evento) => setFiltros((previo) => ({ ...previo, ciclo: evento.target.value }))}
                value={filtros.ciclo}
              >
                <option value="">Todos</option>
                {ciclos.map((ciclo) => (
                  <option key={ciclo.id} value={ciclo.id}>
                    #{ciclo.id} {ciclo.tipo} {ciclo.anio_base}
                  </option>
                ))}
              </select>
            </div>
            <div className="col-md-2">
              <label className="form-label" htmlFor="evidencias-curso">Curso</label>
              <input
                className="form-control"
                id="evidencias-curso"
                inputMode="numeric"
                onChange={(evento) => setFiltros((previo) => ({ ...previo, curso: evento.target.value }))}
                value={filtros.curso}
              />
            </div>
            <div className="col-md-2">
              <label className="form-label" htmlFor="evidencias-criterio">Criterio</label>
              <input
                className="form-control"
                id="evidencias-criterio"
                inputMode="numeric"
                onChange={(evento) => setFiltros((previo) => ({ ...previo, criterio: evento.target.value }))}
                value={filtros.criterio}
              />
            </div>
            <div className="col-12">
              <button className="btn btn-primary" type="submit">Aplicar filtros</button>
            </div>
          </form>

          {cargando ? <Cargando texto="Cargando evidencias..." /> : null}
          {error ? <Mensaje tipo="error" titulo="No se pudo cargar evidencias.">{error}</Mensaje> : null}
          {!cargando && !error ? (
            evidencias.length === 0 ? (
              <Mensaje tipo="info">No hay evidencias para los filtros seleccionados.</Mensaje>
            ) : (
              <div className="table-responsive mt-3">
                <table className="table table-sm align-middle">
                  <thead>
                    <tr>
                      <th scope="col">Título</th>
                      <th scope="col">Ciclo</th>
                      <th scope="col">Curso</th>
                      <th scope="col">Soporte</th>
                      <th scope="col">Huella</th>
                      <th scope="col" className="text-end">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evidencias.map((evidencia) => (
                      <tr key={evidencia.id}>
                        <td>{evidencia.titulo}</td>
                        <td>{evidencia.ciclo}</td>
                        <td>{evidencia.curso_academico}</td>
                        <td>
                          {evidencia.soporte === 'papel' ? (
                            <span className="badge text-bg-warning">Papel</span>
                          ) : (
                            <span className="badge text-bg-primary">Digital</span>
                          )}
                        </td>
                        <td>{evidencia.estado_huella ?? '—'}</td>
                        <td className="text-end">
                          <button
                            className="btn btn-outline-secondary btn-sm"
                            onClick={() => seleccionarEvidencia(evidencia)}
                            type="button"
                          >
                            Ver detalle
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          ) : null}
        </div>
      </section>

      {puedeEditar ? (
        <section aria-labelledby="titulo-formulario-evidencia" className="card">
          <div className="card-body">
            <h2 className="h5" id="titulo-formulario-evidencia">Formulario de carga</h2>
            {errorFormulario ? <Mensaje tipo="error">{errorFormulario}</Mensaje> : null}
            <form className="row g-3" onSubmit={crearEvidencia}>
              <div className="col-md-4">
                <label className="form-label" htmlFor="evidencia-ciclo">Ciclo</label>
                <select
                  className="form-select"
                  id="evidencia-ciclo"
                  name="ciclo"
                  onChange={manejarCambioFormulario}
                  value={formulario.ciclo}
                >
                  <option value="">Seleccione</option>
                  {ciclos.map((ciclo) => (
                    <option key={ciclo.id} value={ciclo.id}>
                      #{ciclo.id} {ciclo.tipo} {ciclo.anio_base}
                    </option>
                  ))}
                </select>
              </div>
              <div className="col-md-4">
                <label className="form-label" htmlFor="evidencia-tipo">Tipo de evidencia (ID)</label>
                <input
                  className="form-control"
                  id="evidencia-tipo"
                  inputMode="numeric"
                  name="tipo_evidencia"
                  onChange={manejarCambioFormulario}
                  value={formulario.tipo_evidencia}
                />
              </div>
              <div className="col-md-4">
                <label className="form-label" htmlFor="evidencia-soporte">Soporte</label>
                <select
                  className="form-select"
                  id="evidencia-soporte"
                  name="soporte"
                  onChange={manejarCambioFormulario}
                  value={formulario.soporte}
                >
                  <option value="digital">Digital</option>
                  <option value="papel">Papel</option>
                </select>
              </div>
              <div className="col-md-6">
                <label className="form-label" htmlFor="evidencia-titulo">Título</label>
                <input
                  className="form-control"
                  id="evidencia-titulo"
                  name="titulo"
                  onChange={manejarCambioFormulario}
                  value={formulario.titulo}
                />
              </div>
              <div className="col-md-3">
                <label className="form-label" htmlFor="evidencia-curso-academico">Curso académico</label>
                <input
                  className="form-control"
                  id="evidencia-curso-academico"
                  inputMode="numeric"
                  name="curso_academico"
                  onChange={manejarCambioFormulario}
                  value={formulario.curso_academico}
                />
              </div>
              <div className="col-md-3">
                <label className="form-label" htmlFor="evidencia-carrera">Carrera del ciclo</label>
                <input
                  className="form-control"
                  disabled
                  id="evidencia-carrera"
                  value={cicloSeleccionado?.carrera ?? '—'}
                />
              </div>
              <div className="col-md-6">
                <label className="form-label" htmlFor="evidencia-periodo-desde">Periodo desde</label>
                <input
                  className="form-control"
                  id="evidencia-periodo-desde"
                  name="periodo_desde"
                  onChange={manejarCambioFormulario}
                  type="date"
                  value={formulario.periodo_desde}
                />
              </div>
              <div className="col-md-6">
                <label className="form-label" htmlFor="evidencia-periodo-hasta">Periodo hasta</label>
                <input
                  className="form-control"
                  id="evidencia-periodo-hasta"
                  name="periodo_hasta"
                  onChange={manejarCambioFormulario}
                  type="date"
                  value={formulario.periodo_hasta}
                />
              </div>
              <div className="col-12">
                <label className="form-label" htmlFor="evidencia-descripcion">Descripción</label>
                <textarea
                  className="form-control"
                  id="evidencia-descripcion"
                  name="descripcion"
                  onChange={manejarCambioFormulario}
                  rows={2}
                  value={formulario.descripcion}
                />
              </div>
              {formulario.soporte === 'papel' ? (
                <div className="col-12">
                  <label className="form-label" htmlFor="evidencia-custodia">Custodia original</label>
                  <input
                    className="form-control"
                    id="evidencia-custodia"
                    name="custodia_original"
                    onChange={manejarCambioFormulario}
                    value={formulario.custodia_original}
                  />
                </div>
              ) : (
                <div className="col-12">
                  <label className="form-label" htmlFor="evidencia-archivo">Archivo</label>
                  <input
                    className="form-control"
                    id="evidencia-archivo"
                    onChange={manejarArchivo}
                    type="file"
                  />
                </div>
              )}
              <div className="col-12">
                <button className="btn btn-primary" disabled={guardando} type="submit">
                  {guardando ? 'Guardando...' : 'Registrar evidencia'}
                </button>
              </div>
            </form>
          </div>
        </section>
      ) : (
        <Mensaje tipo="warning">
          Tu rol no permite registrar evidencias. Puedes revisar el listado y el detalle.
        </Mensaje>
      )}

      <section aria-labelledby="titulo-detalle-evidencia" className="card">
        <div className="card-body">
          <h2 className="h5" id="titulo-detalle-evidencia">Detalle e historial</h2>
          {!evidenciaSeleccionadaId ? (
            <Mensaje tipo="info">Selecciona una evidencia para revisar su historial.</Mensaje>
          ) : null}
          {cargandoDetalle ? <Cargando texto="Cargando detalle..." /> : null}
          {errorDetalle ? <Mensaje tipo="error">{errorDetalle}</Mensaje> : null}
          {detalle ? (
            <div className="d-grid gap-3">
              <div>
                <h3 className="h6 mb-1">{detalle.titulo}</h3>
                <p className="mb-1 text-body-secondary">
                  Soporte: {detalle.soporte} · Estado de huella: {detalle.estado_huella ?? '—'}
                </p>
                <p className="mb-0">
                  Periodo: {formatearFecha(detalle.periodo_desde)} - {formatearFecha(detalle.periodo_hasta)}
                </p>
              </div>

              {Array.isArray(detalle.ficheros) && detalle.ficheros.length > 0 ? (
                <div className="table-responsive">
                  <table className="table table-sm align-middle">
                    <thead>
                      <tr>
                        <th scope="col">Versión</th>
                        <th scope="col">Nombre</th>
                        <th scope="col">SHA-256</th>
                        <th scope="col">Vigente</th>
                        <th scope="col" className="text-end">Descarga</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detalle.ficheros
                        .slice()
                        .sort((a, b) => Number(b.version) - Number(a.version))
                        .map((fichero) => (
                          <tr key={fichero.id}>
                            <td>{fichero.version}</td>
                            <td>{fichero.nombre_original}</td>
                            <td>{fichero.sha256}</td>
                            <td>{fichero.vigente ? 'Sí' : 'No'}</td>
                            <td className="text-end">
                              <a
                                className="btn btn-outline-secondary btn-sm"
                                href={`/api/ficheros/${fichero.id}/descarga/`}
                              >
                                Descargar
                              </a>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <Mensaje tipo="info">Esta evidencia no tiene historial de ficheros.</Mensaje>
              )}
            </div>
          ) : null}
        </div>
      </section>
    </section>
  )
}

export default Evidencias
