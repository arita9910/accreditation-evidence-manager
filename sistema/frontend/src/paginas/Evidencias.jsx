import { useEffect, useMemo, useState } from 'react'
import { Cargando, Mensaje } from '../componentes'
import peticion from '../api/cliente'

const TAMANO_MAXIMO_ARCHIVO_BYTES = 10 * 1024 * 1024

const FORMULARIO_INICIAL = {
  ciclo: '',
  tipo_evidencia: '',
  dimension: '',
  criterio: '',
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
  dimension: '',
  criterio: '',
  soporte: '',
  ciclo: '',
  curso: '',
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
  if (filtros.dimension) {
    query.set('dimension', filtros.dimension)
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
  const [tiposEvidencia, setTiposEvidencia] = useState([])
  const [catalogo, setCatalogo] = useState(null)
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
  const [datosRespaldo, setDatosRespaldo] = useState([])
  const [datosSinRespaldo, setDatosSinRespaldo] = useState([])
  const [datoPendienteSeleccionado, setDatoPendienteSeleccionado] = useState('')
  const [cargandoVinculosDato, setCargandoVinculosDato] = useState(false)
  const [guardandoVinculoDato, setGuardandoVinculoDato] = useState(false)
  const [errorVinculoDato, setErrorVinculoDato] = useState('')

  const puedeEditar = usuario?.rol === 'administrador_tecnico' || usuario?.rol === 'director_carrera'

  const cargarBase = async (filtrosConsulta) => {
    setCargando(true)
    setError('')
    try {
      const query = construirQuery(filtrosConsulta)
      const [respuestaEvidencias, respuestaCiclos, respuestaTipos, respuestaCatalogo] = await Promise.all([
        peticion(`/api/evidencias/${query ? `?${query}` : ''}`),
        peticion('/api/ciclos/'),
        peticion('/api/tipos-evidencia/'),
        peticion('/api/catalogo/'),
      ])
      setEvidencias(extraerLista(respuestaEvidencias))
      setCiclos(extraerLista(respuestaCiclos))
      setTiposEvidencia(extraerLista(respuestaTipos))
      setCatalogo(respuestaCatalogo)
      setFiltrosAplicados(filtrosConsulta)
    } catch (errorRecibido) {
      setError(errorRecibido.message)
      setEvidencias([])
      setTiposEvidencia([])
      setCatalogo(null)
    } finally {
      setCargando(false)
    }
  }

  const cargarDetalle = async (evidenciaId) => {
    if (!evidenciaId) {
      setDetalle(null)
      setDatosRespaldo([])
      setDatosSinRespaldo([])
      setDatoPendienteSeleccionado('')
      return
    }
    setCargandoDetalle(true)
    setErrorDetalle('')
    setErrorVinculoDato('')
    setCargandoVinculosDato(true)
    let cicloDetalle = null
    try {
      const datos = await peticion(`/api/evidencias/${evidenciaId}/`)
      setDetalle(datos)
      cicloDetalle = datos?.ciclo ?? null
    } catch (errorRecibido) {
      setErrorDetalle(errorRecibido.message)
      setDetalle(null)
      setDatosRespaldo([])
      setDatosSinRespaldo([])
      setDatoPendienteSeleccionado('')
      setCargandoDetalle(false)
      setCargandoVinculosDato(false)
      return
    } finally {
      setCargandoDetalle(false)
    }

    try {
      if (!cicloDetalle) {
        setDatosRespaldo([])
        setDatosSinRespaldo([])
        return
      }
      const [datosAsociados, pendientes] = await Promise.all([
        peticion(`/api/evidencias/${evidenciaId}/datos/`),
        peticion(`/api/ciclos/${cicloDetalle}/datos/sin-respaldo/`),
      ])
      setDatosRespaldo(extraerLista(datosAsociados?.datos))
      setDatosSinRespaldo(extraerLista(pendientes?.datos_sin_respaldo ?? pendientes?.datos))
    } catch (errorRecibido) {
      setErrorVinculoDato(errorRecibido.message)
      setDatosRespaldo([])
      setDatosSinRespaldo([])
      setDatoPendienteSeleccionado('')
    } finally {
      setCargandoVinculosDato(false)
    }
  }

  const describirDato = (dato) => {
    if (dato?.tipo === 'modelo') {
      return `Modelo ${dato.modelo} · valor ${dato.valor ?? '—'}`
    }
    return `Criterio ${dato?.codigo ?? dato?.criterio} · valor ${dato?.valor ?? '—'}`
  }

  const vincularDatoPendiente = async (evento) => {
    evento.preventDefault()
    if (!detalle?.id) {
      setErrorVinculoDato('Seleccione una evidencia.')
      return
    }
    if (!datoPendienteSeleccionado) {
      setErrorVinculoDato('Seleccione un dato pendiente.')
      return
    }

    const [tipo, datoId] = datoPendienteSeleccionado.split(':')
    setGuardandoVinculoDato(true)
    setErrorVinculoDato('')
    try {
      await peticion('/api/vinculos/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          evidencia: detalle.id,
          dato: { tipo, id: datoId },
        }),
      })
      setDatoPendienteSeleccionado('')
      await cargarDetalle(detalle.id)
      setMensaje('Dato cuantitativo vinculado correctamente.')
    } catch (errorRecibido) {
      setErrorVinculoDato(errorRecibido.message)
    } finally {
      setGuardandoVinculoDato(false)
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

  const dimensiones = useMemo(
    () => extraerLista(catalogo?.dimensiones),
    [catalogo],
  )

  const tipoSeleccionado = useMemo(
    () => tiposEvidencia.find((tipo) => String(tipo.id) === String(formulario.tipo_evidencia)),
    [tiposEvidencia, formulario.tipo_evidencia],
  )

  const soporteForzadoPapel = tipoSeleccionado?.soporte_exigido === 'papel_firmado'

  const criteriosPorDimension = useMemo(
    () => dimensiones
      .filter((dimension) => dimension?.id !== null && dimension?.id !== undefined)
      .map((dimension) => ({
        valor: String(dimension.id),
        criterios: extraerLista(dimension?.indicadores)
          .flatMap((indicador) => extraerLista(indicador?.criterios))
          .filter((criterio) => criterio?.id !== null && criterio?.id !== undefined),
      })),
    [dimensiones],
  )

  const criteriosFormulario = useMemo(
    () => criteriosPorDimension.find((item) => item.valor === String(formulario.dimension))?.criterios ?? [],
    [criteriosPorDimension, formulario.dimension],
  )

  const criteriosFiltro = useMemo(
    () => criteriosPorDimension.find((item) => item.valor === String(filtros.dimension))?.criterios ?? [],
    [criteriosPorDimension, filtros.dimension],
  )

  const manejarCambioFormulario = (evento) => {
    const { name, value } = evento.target
    if (name === 'tipo_evidencia') {
      const tipo = tiposEvidencia.find((item) => String(item.id) === String(value))
      setFormulario((previo) => ({
        ...previo,
        tipo_evidencia: value,
        soporte: tipo?.soporte_exigido === 'papel_firmado' ? 'papel' : previo.soporte,
        archivo: tipo?.soporte_exigido === 'papel_firmado' ? null : previo.archivo,
      }))
      return
    }

    if (name === 'dimension') {
      setFormulario((previo) => ({ ...previo, dimension: value, criterio: '' }))
      return
    }

    setFormulario((previo) => ({ ...previo, [name]: value }))
  }

  const manejarArchivo = (evento) => {
    const [archivo] = evento.target.files ?? []
    if (archivo && archivo.size > TAMANO_MAXIMO_ARCHIVO_BYTES) {
      setErrorFormulario('El archivo supera el límite de 10 MB.')
      evento.target.value = ''
      setFormulario((previo) => ({ ...previo, archivo: null }))
      return
    }
    setErrorFormulario('')
    setFormulario((previo) => ({ ...previo, archivo: archivo ?? null }))
  }

  const limpiarFormulario = () => {
    setFormulario(FORMULARIO_INICIAL)
  }

  const crearEvidencia = async (evento) => {
    evento.preventDefault()
    setMensaje('')
    setErrorFormulario('')

    if (!formulario.ciclo || !formulario.tipo_evidencia || !formulario.dimension || !formulario.criterio || !formulario.titulo.trim()) {
      setErrorFormulario('Debe completar ciclo, tipo de evidencia, dimensión, criterio y título.')
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
      cuerpo.set('curso_academico', formulario.curso_academico.trim())
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

      await peticion(`/api/evidencias/${creada.id}/clasificaciones/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          criterio: formulario.criterio,
        }),
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
              <label className="form-label" htmlFor="evidencias-dimension">Dimensión</label>
              <select
                className="form-select"
                id="evidencias-dimension"
                onChange={(evento) => setFiltros((previo) => ({ ...previo, dimension: evento.target.value, criterio: '' }))}
                value={filtros.dimension}
              >
                <option value="">Todas</option>
                {dimensiones
                  .filter((dimension) => dimension?.id !== null && dimension?.id !== undefined)
                  .map((dimension) => (
                  <option key={dimension.id} value={String(dimension.id)}>
                    {dimension.codigo} {dimension.nombre}
                  </option>
                  ))}
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
            <div className="col-md-1">
              <label className="form-label" htmlFor="evidencias-curso">Curso</label>
              <input
                className="form-control"
                id="evidencias-curso"
                inputMode="numeric"
                onChange={(evento) => setFiltros((previo) => ({ ...previo, curso: evento.target.value }))}
                value={filtros.curso}
              />
            </div>
            <div className="col-md-3">
              <label className="form-label" htmlFor="evidencias-criterio">Criterio</label>
              <select
                className="form-select"
                id="evidencias-criterio"
                disabled={!filtros.dimension}
                onChange={(evento) => setFiltros((previo) => ({ ...previo, criterio: evento.target.value }))}
                value={filtros.criterio}
              >
                <option value="">{filtros.dimension ? 'Todos' : 'Seleccione dimensión'}</option>
                {criteriosFiltro.map((criterio) => (
                  <option key={criterio.id} value={String(criterio.id)}>
                    {criterio.codigo} {criterio.texto}
                  </option>
                ))}
              </select>
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
                <label className="form-label" htmlFor="evidencia-tipo">Tipo de evidencia</label>
                <select
                  className="form-select"
                  id="evidencia-tipo"
                  name="tipo_evidencia"
                  onChange={manejarCambioFormulario}
                  value={formulario.tipo_evidencia}
                >
                  <option value="">Seleccione</option>
                  {tiposEvidencia.map((tipo) => (
                    <option key={tipo.id} value={tipo.id}>
                      {tipo.nombre} ({tipo.soporte_exigido === 'papel_firmado' ? 'Papel' : tipo.soporte_exigido === 'ambos' ? 'Ambos' : 'Digital'})
                    </option>
                  ))}
                </select>
              </div>
              <div className="col-md-4">
                <label className="form-label" htmlFor="evidencia-dimension">Dimensión</label>
                <select
                  className="form-select"
                  id="evidencia-dimension"
                  name="dimension"
                  onChange={manejarCambioFormulario}
                  value={formulario.dimension}
                >
                  <option value="">Seleccione</option>
                  {dimensiones
                    .filter((dimension) => dimension?.id !== null && dimension?.id !== undefined)
                    .map((dimension) => (
                    <option key={dimension.id} value={String(dimension.id)}>
                      {dimension.codigo} {dimension.nombre}
                    </option>
                    ))}
                </select>
              </div>
              <div className="col-md-4">
                <label className="form-label" htmlFor="evidencia-criterio">Criterio</label>
                <select
                  className="form-select"
                  disabled={!formulario.dimension}
                  id="evidencia-criterio"
                  name="criterio"
                  onChange={manejarCambioFormulario}
                  value={formulario.criterio}
                >
                  <option value="">{formulario.dimension ? 'Seleccione' : 'Seleccione dimensión'}</option>
                  {criteriosFormulario.map((criterio) => (
                    <option key={criterio.id} value={String(criterio.id)}>
                      {criterio.codigo} {criterio.texto}
                    </option>
                  ))}
                </select>
              </div>
              <div className="col-md-4">
                <label className="form-label" htmlFor="evidencia-soporte">Soporte</label>
                <select
                  className="form-select"
                  disabled={soporteForzadoPapel}
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
                  inputMode="text"
                  name="curso_academico"
                  onChange={manejarCambioFormulario}
                  placeholder="2024-2025"
                  type="text"
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

              <section aria-labelledby="titulo-datos-respaldo">
                <h3 className="h6" id="titulo-datos-respaldo">Datos respaldados por esta evidencia</h3>
                {cargandoVinculosDato ? <Cargando texto="Cargando datos cuantitativos..." /> : null}
                {errorVinculoDato ? <Mensaje tipo="error">{errorVinculoDato}</Mensaje> : null}
                {!cargandoVinculosDato ? (
                  datosRespaldo.length > 0 ? (
                    <ul>
                      {datosRespaldo.map((dato) => (
                        <li key={`${dato.tipo}-${dato.id}`}>{describirDato(dato)}</li>
                      ))}
                    </ul>
                  ) : (
                    <Mensaje tipo="info">Esta evidencia todavía no respalda datos cuantitativos.</Mensaje>
                  )
                ) : null}
              </section>

              <section aria-labelledby="titulo-datos-sin-respaldo">
                <h3 className="h6" id="titulo-datos-sin-respaldo">Datos sin respaldo del ciclo</h3>
                {datosSinRespaldo.length > 0 ? (
                  <>
                    {puedeEditar ? (
                      <form className="row g-2 align-items-end" onSubmit={vincularDatoPendiente}>
                        <div className="col-md-8">
                          <label className="form-label" htmlFor="dato-pendiente">Dato pendiente</label>
                          <select
                            className="form-select"
                            id="dato-pendiente"
                            onChange={(evento) => setDatoPendienteSeleccionado(evento.target.value)}
                            value={datoPendienteSeleccionado}
                          >
                            <option value="">Seleccione</option>
                            {datosSinRespaldo.map((dato) => (
                              <option key={`${dato.tipo}-${dato.id}`} value={`${dato.tipo}:${dato.id}`}>
                                {describirDato(dato)}
                              </option>
                            ))}
                          </select>
                        </div>
                        <div className="col-md-4">
                          <button className="btn btn-outline-primary w-100" disabled={guardandoVinculoDato} type="submit">
                            {guardandoVinculoDato ? 'Vinculando...' : 'Vincular dato'}
                          </button>
                        </div>
                      </form>
                    ) : null}
                    <ul className="mt-2 mb-0">
                      {datosSinRespaldo.map((dato) => (
                        <li key={`pendiente-${dato.tipo}-${dato.id}`}>{describirDato(dato)}</li>
                      ))}
                    </ul>
                  </>
                ) : (
                  <Mensaje tipo="info">No hay datos pendientes de respaldo para este ciclo.</Mensaje>
                )}
              </section>

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
