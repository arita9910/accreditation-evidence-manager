import { useEffect, useMemo, useState } from 'react'
import { Cargando, Mensaje } from '../componentes'
import peticion from '../api/cliente'
import { formatearAsistentePorcentaje } from './valoracionesAsistente'

const FORMULARIO_INICIAL = {
  id: null,
  dimension: '',
  tipo: 'fortaleza',
  texto: '',
  criterios: [],
  evidencias: [],
}

function esEnteroNoNegativoTexto(valor) {
  return /^\d*$/.test(String(valor))
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

function Valoraciones({ usuario }) {
  const [ciclos, setCiclos] = useState([])
  const [catalogo, setCatalogo] = useState(null)
  const [cicloSeleccionadoId, setCicloSeleccionadoId] = useState('')
  const [valoraciones, setValoraciones] = useState([])
  const [evidenciasClasificadas, setEvidenciasClasificadas] = useState([])
  const [formulario, setFormulario] = useState(FORMULARIO_INICIAL)
  const [asistente, setAsistente] = useState({ porcentaje: '', numerador: '', denominador: '' })
  const [cargando, setCargando] = useState(true)
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState('')
  const [errorFormulario, setErrorFormulario] = useState('')
  const [errorAsistente, setErrorAsistente] = useState('')
  const [mensaje, setMensaje] = useState('')

  const puedeEditar = usuario?.rol === 'administrador_tecnico' || usuario?.rol === 'director_carrera'

  const cargarBase = async () => {
    setError('')
    setCargando(true)
    try {
      const respuestaCiclos = await peticion('/api/ciclos/')
      const ciclosRecibidos = extraerLista(respuestaCiclos)
      setCiclos(ciclosRecibidos)
      if (ciclosRecibidos.length > 0) {
        setCicloSeleccionadoId((previo) => previo || String(ciclosRecibidos[0].id))
      } else {
        setCatalogo(null)
        setCicloSeleccionadoId('')
      }
    } catch (errorRecibido) {
      setError(errorRecibido.message)
      setCiclos([])
      setCatalogo(null)
      setCicloSeleccionadoId('')
    } finally {
      setCargando(false)
    }
  }

  const cargarValoraciones = async (cicloId) => {
    if (!cicloId) {
      setValoraciones([])
      setEvidenciasClasificadas([])
      return
    }

    setError('')
    try {
      const [respuestaValoraciones, respuestaEvidencias, respuestaCatalogo] = await Promise.all([
        peticion(`/api/ciclos/${cicloId}/valoraciones/`),
        peticion(`/api/evidencias/?ciclo=${cicloId}`),
        peticion(`/api/ciclos/${cicloId}/valoraciones/catalogo/`),
      ])
      setValoraciones(extraerLista(respuestaValoraciones))
      setEvidenciasClasificadas(
        extraerLista(respuestaEvidencias).filter((item) => extraerLista(item?.clasificaciones).length > 0),
      )
      setCatalogo(respuestaCatalogo)
    } catch (errorRecibido) {
      setError(errorRecibido.message)
      setValoraciones([])
      setEvidenciasClasificadas([])
      setCatalogo(null)
    }
  }

  useEffect(() => {
    cargarBase()
  }, [])

  useEffect(() => {
    if (!cicloSeleccionadoId) {
      return
    }
    cargarValoraciones(cicloSeleccionadoId)
  }, [cicloSeleccionadoId])

  const dimensiones = useMemo(
    () => extraerLista(catalogo?.dimensiones),
    [catalogo],
  )

  const criteriosPorDimension = useMemo(
    () => dimensiones
      .filter((dimension) => dimension?.id !== undefined && dimension?.id !== null)
      .map((dimension) => ({
        valor: String(dimension.id),
        criterios: extraerLista(dimension?.indicadores)
          .flatMap((indicador) => extraerLista(indicador?.criterios))
          .filter((criterio) => criterio?.id !== undefined && criterio?.id !== null),
      })),
    [dimensiones],
  )

  const criteriosDisponibles = useMemo(
    () => criteriosPorDimension.find((item) => item.valor === String(formulario.dimension))?.criterios ?? [],
    [criteriosPorDimension, formulario.dimension],
  )

  const validacionAsistente = useMemo(() => {
    const numeradorTexto = String(asistente.numerador ?? '').trim()
    const denominadorTexto = String(asistente.denominador ?? '').trim()

    if (!numeradorTexto && !denominadorTexto) {
      return { porcentaje: '', error: '' }
    }
    if (!numeradorTexto || !denominadorTexto) {
      return { porcentaje: '', error: '' }
    }

    const numerador = Number.parseInt(numeradorTexto, 10)
    const denominador = Number.parseInt(denominadorTexto, 10)

    if (!Number.isInteger(numerador) || numerador < 0) {
      return { porcentaje: '', error: 'Debe indicar un numerador entero mayor o igual que cero.' }
    }
    if (!Number.isInteger(denominador) || denominador <= 0) {
      return { porcentaje: '', error: 'Debe indicar un denominador entero mayor que cero.' }
    }
    if (numerador > denominador) {
      return { porcentaje: '', error: 'El numerador no puede ser mayor que el denominador.' }
    }

    return {
      porcentaje: ((numerador / denominador) * 100).toFixed(1).replace('.', ','),
      error: '',
    }
  }, [asistente.numerador, asistente.denominador])

  const fortalezas = useMemo(
    () => valoraciones.filter((item) => item.tipo === 'fortaleza'),
    [valoraciones],
  )

  const debilidades = useMemo(
    () => valoraciones.filter((item) => item.tipo === 'debilidad'),
    [valoraciones],
  )

  const cambiarDimension = (dimensionId) => {
    setFormulario((previo) => ({
      ...previo,
      dimension: dimensionId,
      criterios: previo.dimension === dimensionId ? previo.criterios : [],
    }))
    setErrorFormulario('')
  }

  const alternarSeleccion = (campo, valorId) => {
    setFormulario((previo) => {
      const valorTexto = String(valorId)
      const existe = previo[campo].some((actual) => String(actual) === valorTexto)
      const actualizados = existe
        ? previo[campo].filter((actual) => String(actual) !== valorTexto)
        : [...previo[campo], valorTexto]

      return {
        ...previo,
        [campo]: actualizados,
      }
    })
    setErrorFormulario('')
  }

  const cargarEnFormulario = (valoracion) => {
    setFormulario({
      id: valoracion.id,
      dimension: valoracion.dimension ? String(valoracion.dimension) : '',
      tipo: valoracion.tipo,
      texto: valoracion.texto || '',
      criterios: extraerLista(valoracion.criterios).map((valor) => String(valor)),
      evidencias: extraerLista(valoracion.evidencias).map((valor) => String(valor)),
    })
    setErrorFormulario('')
    setMensaje('')
  }

  const reiniciarFormulario = () => {
    setFormulario(FORMULARIO_INICIAL)
    setErrorFormulario('')
    setErrorAsistente('')
    setAsistente({ porcentaje: '', numerador: '', denominador: '' })
  }

  const cambiarAsistenteEntero = (campo, valor) => {
    if (!esEnteroNoNegativoTexto(valor)) {
      return
    }
    setAsistente((previo) => ({ ...previo, [campo]: valor }))
    setErrorAsistente('')
  }

  const insertarPorcentaje = () => {
    if (validacionAsistente.error) {
      setErrorAsistente(validacionAsistente.error)
      return
    }
    try {
      const texto = formatearAsistentePorcentaje(
        validacionAsistente.porcentaje,
        asistente.numerador,
        asistente.denominador,
      )
      setFormulario((previo) => ({
        ...previo,
        texto: `${previo.texto}${previo.texto ? ' ' : ''}${texto}`,
      }))
      setErrorAsistente('')
    } catch (errorRecibido) {
      setErrorAsistente(errorRecibido.message)
    }
  }

  const enviarFormulario = async (evento) => {
    evento.preventDefault()
    setMensaje('')
    setErrorFormulario('')

    if (!cicloSeleccionadoId) {
      setErrorFormulario('Debe seleccionar un ciclo.')
      return
    }
    if (!formulario.dimension) {
      setErrorFormulario('Debe seleccionar una dimensión.')
      return
    }
    if (!formulario.texto.trim()) {
      setErrorFormulario('Debe redactar el texto de la valoración.')
      return
    }
    if (formulario.criterios.length === 0) {
      setErrorFormulario('Debe seleccionar al menos un criterio de la dimensión.')
      return
    }
    if (formulario.evidencias.length === 0) {
      setErrorFormulario('Debe seleccionar al menos una evidencia clasificada del ciclo.')
      return
    }

    const criteriosValidos = new Set(criteriosDisponibles.map((criterio) => String(criterio.id)))
    const evidenciasValidas = new Set(evidenciasClasificadas.map((evidencia) => String(evidencia.id)))
    const hayCriterioInvalido = formulario.criterios.some((id) => !criteriosValidos.has(String(id)))
    const hayEvidenciaInvalida = formulario.evidencias.some((id) => !evidenciasValidas.has(String(id)))
    if (hayCriterioInvalido || hayEvidenciaInvalida) {
      setErrorFormulario('La selección de criterios o evidencias ya no es válida. Actualice y vuelva a intentar.')
      return
    }

    setGuardando(true)
    try {
      const cuerpo = {
        dimension: Number(formulario.dimension),
        tipo: formulario.tipo,
        texto: formulario.texto.trim(),
        criterios: formulario.criterios.map((valor) => Number(valor)),
        evidencias: formulario.evidencias.map((valor) => Number(valor)),
      }

      if (formulario.id) {
        await peticion(`/api/valoraciones/${formulario.id}/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(cuerpo),
        })
        setMensaje('Valoración actualizada correctamente.')
      } else {
        await peticion(`/api/ciclos/${cicloSeleccionadoId}/valoraciones/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(cuerpo),
        })
        setMensaje('Valoración registrada correctamente.')
      }

      await cargarValoraciones(cicloSeleccionadoId)
      reiniciarFormulario()
    } catch (errorRecibido) {
      setErrorFormulario(errorRecibido.message)
    } finally {
      setGuardando(false)
    }
  }

  if (cargando) {
    return <Cargando texto="Cargando editor de valoraciones..." />
  }

  return (
    <section className="d-flex flex-column gap-4">
      <header>
        <h1 className="h3 mb-1">Valoraciones cualitativas</h1>
        <p className="text-secondary mb-0">
          Editor por dimensión para fortalezas y debilidades del ciclo.
        </p>
      </header>

      {error ? <Mensaje tipo="error">{error}</Mensaje> : null}
      {mensaje ? <Mensaje tipo="success">{mensaje}</Mensaje> : null}

      <div className="card shadow-sm">
        <div className="card-body">
          <label className="form-label" htmlFor="valoraciones-ciclo">Ciclo</label>
          <select
            id="valoraciones-ciclo"
            className="form-select"
            value={cicloSeleccionadoId}
            onChange={(evento) => setCicloSeleccionadoId(evento.target.value)}
          >
            {ciclos.map((ciclo) => (
              <option key={ciclo.id} value={String(ciclo.id)}>
                #{ciclo.id} · {ciclo.tipo} · {ciclo.anio_base}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="row g-3">
        <div className="col-12 col-lg-6">
          <div className="card h-100 shadow-sm">
            <div className="card-body">
              <h2 className="h5">Fortalezas</h2>
              <ul className="list-group list-group-flush">
                {fortalezas.length === 0 ? (
                  <li className="list-group-item px-0 text-secondary">Sin fortalezas registradas.</li>
                ) : fortalezas.map((valoracion) => (
                  <li key={valoracion.id} className="list-group-item px-0">
                    <button
                      type="button"
                      className="btn btn-link p-0 text-start"
                      onClick={() => cargarEnFormulario(valoracion)}
                    >
                      {valoracion.texto}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
        <div className="col-12 col-lg-6">
          <div className="card h-100 shadow-sm">
            <div className="card-body">
              <h2 className="h5">Debilidades</h2>
              <ul className="list-group list-group-flush">
                {debilidades.length === 0 ? (
                  <li className="list-group-item px-0 text-secondary">Sin debilidades registradas.</li>
                ) : debilidades.map((valoracion) => (
                  <li key={valoracion.id} className="list-group-item px-0">
                    <button
                      type="button"
                      className="btn btn-link p-0 text-start"
                      onClick={() => cargarEnFormulario(valoracion)}
                    >
                      {valoracion.texto}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {puedeEditar ? (
        <form className="card shadow-sm" onSubmit={enviarFormulario}>
          <div className="card-body d-flex flex-column gap-3">
            <h2 className="h5 mb-0">{formulario.id ? 'Editar valoración' : 'Nueva valoración'}</h2>

            <Mensaje tipo="info">
              Recordatorio Anexo 5: redacte fortalezas y debilidades con sustento verificable, lenguaje claro y sin juicios automáticos.
            </Mensaje>

            <div>
              <span className="form-label d-block">Tipo de valoración</span>
              <div className="btn-group" role="group" aria-label="Tipo de valoración">
                <button
                  type="button"
                  className={`btn ${formulario.tipo === 'fortaleza' ? 'btn-primary' : 'btn-outline-primary'}`}
                  onClick={() => setFormulario((previo) => ({ ...previo, tipo: 'fortaleza' }))}
                >
                  Fortaleza
                </button>
                <button
                  type="button"
                  className={`btn ${formulario.tipo === 'debilidad' ? 'btn-primary' : 'btn-outline-primary'}`}
                  onClick={() => setFormulario((previo) => ({ ...previo, tipo: 'debilidad' }))}
                >
                  Debilidad
                </button>
              </div>
            </div>

            <div>
              <label className="form-label" htmlFor="valoracion-dimension">Dimensión</label>
              <select
                id="valoracion-dimension"
                className="form-select"
                value={formulario.dimension}
                onChange={(evento) => cambiarDimension(evento.target.value)}
              >
                <option value="">Seleccione</option>
                {dimensiones.map((dimension) => (
                  <option key={dimension.id} value={String(dimension.id)}>
                    {dimension.codigo} · {dimension.nombre}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="form-label" htmlFor="valoracion-texto">Texto</label>
              <textarea
                id="valoracion-texto"
                className="form-control"
                rows={5}
                value={formulario.texto}
                onChange={(evento) => setFormulario((previo) => ({ ...previo, texto: evento.target.value }))}
              />
            </div>

            <fieldset className="border rounded p-3">
              <legend className="float-none w-auto px-2 fs-6">Asistente de porcentaje</legend>
              <div className="row g-2 align-items-end">
                <div className="col-12 col-md-4">
                  <label className="form-label" htmlFor="asistente-porcentaje">Porcentaje (%)</label>
                  <input
                    id="asistente-porcentaje"
                    className="form-control"
                    type="text"
                    value={validacionAsistente.porcentaje}
                    readOnly
                    placeholder="86,2"
                  />
                </div>
                <div className="col-12 col-md-3">
                  <label className="form-label" htmlFor="asistente-numerador">Numerador</label>
                  <input
                    id="asistente-numerador"
                    className="form-control"
                    type="number"
                    min="0"
                    step="1"
                    value={asistente.numerador}
                    onChange={(evento) => cambiarAsistenteEntero('numerador', evento.target.value)}
                  />
                </div>
                <div className="col-12 col-md-3">
                  <label className="form-label" htmlFor="asistente-denominador">Denominador</label>
                  <input
                    id="asistente-denominador"
                    className="form-control"
                    type="number"
                    min="0"
                    step="1"
                    value={asistente.denominador}
                    onChange={(evento) => cambiarAsistenteEntero('denominador', evento.target.value)}
                  />
                </div>
                <div className="col-12 col-md-2">
                  <button className="btn btn-outline-secondary w-100" type="button" onClick={insertarPorcentaje}>
                    Insertar porcentaje
                  </button>
                </div>
              </div>
              {errorAsistente || validacionAsistente.error ? (
                <div className="text-danger small mt-2">{errorAsistente || validacionAsistente.error}</div>
              ) : null}
            </fieldset>

            <fieldset className="border rounded p-3">
              <legend className="float-none w-auto px-2 fs-6">Criterios de la dimensión</legend>
              {criteriosDisponibles.length === 0 ? (
                <div className="text-secondary small">Seleccione una dimensión para cargar criterios.</div>
              ) : (
                <div className="d-flex flex-column gap-2">
                  {criteriosDisponibles.map((criterio) => (
                    <label key={criterio.id} className="form-check">
                      <input
                        className="form-check-input"
                        type="checkbox"
                        checked={formulario.criterios.some((valor) => String(valor) === String(criterio.id))}
                        onChange={() => alternarSeleccion('criterios', criterio.id)}
                      />
                      <span className="form-check-label">{criterio.codigo} · {criterio.texto}</span>
                    </label>
                  ))}
                </div>
              )}
            </fieldset>

            <fieldset className="border rounded p-3">
              <legend className="float-none w-auto px-2 fs-6">Evidencias clasificadas del ciclo</legend>
              {evidenciasClasificadas.length === 0 ? (
                <div className="text-secondary small">No hay evidencias clasificadas disponibles para este ciclo.</div>
              ) : (
                <div className="d-flex flex-column gap-2">
                  {evidenciasClasificadas.map((evidencia) => (
                    <label key={evidencia.id} className="form-check">
                      <input
                        className="form-check-input"
                        type="checkbox"
                        checked={formulario.evidencias.some((valor) => String(valor) === String(evidencia.id))}
                        onChange={() => alternarSeleccion('evidencias', evidencia.id)}
                      />
                      <span className="form-check-label">{evidencia.titulo}</span>
                    </label>
                  ))}
                </div>
              )}
            </fieldset>

            {errorFormulario ? <Mensaje tipo="error">{errorFormulario}</Mensaje> : null}

            <div className="d-flex gap-2">
              <button className="btn btn-primary" type="submit" disabled={guardando}>
                {guardando ? 'Guardando...' : (formulario.id ? 'Guardar cambios' : 'Registrar valoración')}
              </button>
              <button className="btn btn-outline-secondary" type="button" onClick={reiniciarFormulario} disabled={guardando}>
                Limpiar
              </button>
            </div>
          </div>
        </form>
      ) : (
        <Mensaje tipo="warning">
          Tu rol no permite registrar valoraciones. Puedes revisar el listado.
        </Mensaje>
      )}
    </section>
  )
}

export default Valoraciones
