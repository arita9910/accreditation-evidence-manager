import { useEffect, useMemo, useState } from 'react'
import peticion from '../api/cliente'
import { Cargando, Mensaje } from '../componentes'

const AVISOS = [
  ['criterios_sin_evidencia', 'Criterios sin evidencia'],
  ['criterios_cuantitativos_sin_dato', 'Criterios cuantitativos sin dato'],
  ['datos_sin_respaldo', 'Datos sin respaldo'],
  ['dimensiones_sin_valoracion', 'Dimensiones sin valoración'],
  ['debilidades_sin_accion', 'Debilidades sin acción'],
]

function extraerLista(respuesta) {
  if (Array.isArray(respuesta)) return respuesta
  if (Array.isArray(respuesta?.results)) return respuesta.results
  return []
}

function formatearDatoSinRespaldo(elemento) {
  if (!elemento || typeof elemento !== 'object') {
    return `Dato sin respaldo #${elemento}`
  }

  if (typeof elemento.descripcion === 'string' && elemento.descripcion.trim()) {
    return elemento.descripcion.trim()
  }

  if (typeof elemento.mensaje === 'string' && elemento.mensaje.trim()) {
    return elemento.mensaje.trim()
  }

  if (elemento.tipo === 'valor_modelo') {
    const modeloId = elemento.numero_modelo ?? elemento.modelo_id ?? 'N/D'
    const curso = elemento.curso ?? 'N/D'
    return `Dato del modelo ${modeloId} - Curso ${curso} sin evidencia`
  }

  if (elemento.tipo === 'valor_criterio') {
    const curso = elemento.curso ?? 'N/D'
    return `Dato del criterio ${elemento.criterio_id ?? 'N/D'} - Curso ${curso} sin evidencia`
  }

  const modeloId = elemento.numero_modelo ?? elemento.modelo_id
  if (modeloId) {
    return `Dato del modelo ${modeloId} sin evidencia`
  }

  if (elemento.criterio_id) {
    return `Dato del criterio ${elemento.criterio_id} sin evidencia`
  }

  return 'Dato sin respaldo sin detalle legible'
}

function Analisis({ usuario }) {
  const autorizado = usuario?.rol === 'administrador_tecnico' || usuario?.rol === 'director_carrera'
  const [vista, setVista] = useState('estado')
  const [ciclos, setCiclos] = useState([])
  const [cicloId, setCicloId] = useState('')
  const [estado, setEstado] = useState(null)
  const [completitud, setCompletitud] = useState(null)
  const [cicloA, setCicloA] = useState('')
  const [cicloB, setCicloB] = useState('')
  const [comparacion, setComparacion] = useState(null)
  const [soloAvisos, setSoloAvisos] = useState(false)
  const [cargando, setCargando] = useState(autorizado)
  const [cargandoDetalle, setCargandoDetalle] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let vigente = true
    if (!autorizado) {
      return undefined
    }

    peticion('/api/ciclos/')
      .then((respuesta) => {
        if (!vigente) return
        const lista = extraerLista(respuesta)
        setCiclos(lista)
        if (lista.length > 0) {
          setCicloId(String(lista[0].id))
          setCicloA(String(lista[0].id))
          if (lista.length > 1) setCicloB(String(lista[1].id))
        }
        setError('')
      })
      .catch((errorRecibido) => vigente && setError(errorRecibido.message))
      .finally(() => vigente && setCargando(false))
    return () => { vigente = false }
  }, [autorizado])

  useEffect(() => {
    let vigente = true
    if (!cicloId) {
      return undefined
    }

    Promise.all([
      peticion(`/api/ciclos/${cicloId}/estado/`),
      peticion(`/api/ciclos/${cicloId}/completitud/`),
    ])
      .then(([estadoRespuesta, completitudRespuesta]) => {
        if (!vigente) return
        setEstado(estadoRespuesta)
        setCompletitud(completitudRespuesta)
      })
      .catch((errorRecibido) => {
        if (vigente) setError(errorRecibido.message)
      })
      .finally(() => vigente && setCargandoDetalle(false))
    return () => { vigente = false }
  }, [cicloId])

  const ciclosFiltrados = useMemo(() => {
    if (usuario?.rol !== 'director_carrera') return ciclos
    return ciclos.filter((ciclo) => String(ciclo.carrera) === String(usuario.carrera))
  }, [ciclos, usuario])

  const formatearElementoAviso = (clave, elemento) => {
    if (clave === 'datos_sin_respaldo' && elemento && typeof elemento === 'object') {
      return formatearDatoSinRespaldo(elemento)
    }

    if (typeof elemento === 'object') {
      if (typeof elemento.descripcion === 'string' && elemento.descripcion.trim()) return elemento.descripcion.trim()
      if (typeof elemento.mensaje === 'string' && elemento.mensaje.trim()) return elemento.mensaje.trim()
      return JSON.stringify(elemento)
    }
    return String(elemento)
  }

  const comparar = async (evento) => {
    evento.preventDefault()
    setComparacion(null)
    setError('')
    if (!cicloA || !cicloB) {
      setError('Debe seleccionar los dos ciclos.')
      return
    }
    if (cicloA === cicloB) {
      setError('Debe comparar dos ciclos distintos.')
      return
    }
    setCargandoDetalle(true)
    try {
      setComparacion(await peticion(`/api/comparaciones/?a=${encodeURIComponent(cicloA)}&b=${encodeURIComponent(cicloB)}`))
    } catch (errorRecibido) {
      setError(errorRecibido.message)
    } finally {
      setCargandoDetalle(false)
    }
  }

  if (!autorizado) {
    return <Mensaje tipo="error">Solo el Administrador técnico y el Director de carrera pueden consultar el análisis.</Mensaje>
  }
  if (cargando) return <Cargando texto="Cargando análisis..." />

  return (
    <section>
      <h1 className="h3 mb-3">Análisis de ciclos</h1>
      {error ? <Mensaje tipo="error">{error}</Mensaje> : null}

      <div className="btn-group mb-3" role="group" aria-label="Vistas de análisis">
        <button type="button" className={`btn ${vista === 'estado' ? 'btn-primary' : 'btn-outline-primary'}`} onClick={() => setVista('estado')} aria-pressed={vista === 'estado'}>Estado</button>
        <button type="button" className={`btn ${vista === 'completitud' ? 'btn-primary' : 'btn-outline-primary'}`} onClick={() => setVista('completitud')} aria-pressed={vista === 'completitud'}>Completitud</button>
        <button type="button" className={`btn ${vista === 'comparacion' ? 'btn-primary' : 'btn-outline-primary'}`} onClick={() => setVista('comparacion')} aria-pressed={vista === 'comparacion'}>Comparación</button>
      </div>

      {vista !== 'comparacion' ? (
        <div className="mb-3">
          <label className="form-label" htmlFor="analisis-ciclo">Ciclo</label>
          <select id="analisis-ciclo" className="form-select" value={cicloId} onChange={(evento) => {
            setCicloId(evento.target.value)
            setEstado(null)
            setCompletitud(null)
            setError('')
          }}>
            <option value="">Seleccione un ciclo</option>
            {ciclosFiltrados.map((ciclo) => (
              <option key={ciclo.id} value={ciclo.id}>{ciclo.tipo} · {ciclo.anio_base} · ciclo #{ciclo.id}</option>
            ))}
          </select>
        </div>
      ) : null}

      {cargandoDetalle ? <Cargando texto="Cargando datos..." /> : null}

      {vista === 'estado' && estado ? (
        <div>
          <h2 className="h5">Estado del ciclo #{estado.ciclo_id}</h2>
          {estado.dimensiones.length === 0 ? <Mensaje tipo="info">No hay dimensiones disponibles.</Mensaje> : null}
          {estado.dimensiones.map((dimension) => (
            <article key={dimension.id} className="card mb-3">
              <div className="card-header"><strong>{dimension.codigo}</strong> · {dimension.nombre}</div>
              <div className="card-body">
                {dimension.indicadores.map((indicador) => (
                  <section key={indicador.id} className="mb-3">
                    <h3 className="h6">{indicador.codigo} · {indicador.nombre}</h3>
                    <div className="list-group">
                      {indicador.criterios.map((criterio) => (
                        <div key={criterio.id} className="list-group-item">
                          <strong>{criterio.codigo}</strong> · {criterio.nombre}
                          <div className="mt-2">
                            Evidencias: {criterio.evidencias_clasificadas}, Datos: {criterio.datos_cuantitativos ? 'Sí' : 'No'}, Respaldo: {criterio.dato_con_respaldo ? 'Sí' : 'No'}, Valoración: {criterio.tiene_valoracion ? 'Sí' : 'No'}, Acción: {criterio.tiene_accion ? 'Sí' : 'No'}
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
                ))}
              </div>
            </article>
          ))}
        </div>
      ) : null}

      {vista === 'completitud' && completitud ? (
        <div>
          <div className="form-check mb-3">
            <input id="solo-avisos" className="form-check-input" type="checkbox" checked={soloAvisos} onChange={(evento) => setSoloAvisos(evento.target.checked)} />
            <label className="form-check-label" htmlFor="solo-avisos">Solo con avisos</label>
          </div>
          <h2 className="h5">Completitud del ciclo #{completitud.ciclo_id}</h2>
          {AVISOS.map(([clave]) => {
            const elementos = completitud[clave] ?? []
            if (soloAvisos && elementos.length === 0) return null
            return (
              <p key={clave} className="mb-2">
                <strong>{clave}:</strong>{' '}
                {elementos.length === 0
                  ? (clave === 'debilidades_sin_accion' ? 'No hay debilidades pendientes por resolver' : 'Sin avisos')
                  : elementos.map((elemento) => formatearElementoAviso(clave, elemento)).join(', ')}
              </p>
            )
          })}
        </div>
      ) : null}

      {vista === 'comparacion' ? (
        <div>
          <form className="row g-3 mb-3" onSubmit={comparar}>
            <div className="col-md-5">
              <label className="form-label" htmlFor="ciclo-a">Ciclo A</label>
              <select id="ciclo-a" className="form-select" value={cicloA} onChange={(evento) => setCicloA(evento.target.value)}>
                <option value="">Seleccione ciclo A</option>
                {ciclosFiltrados.map((ciclo) => <option key={ciclo.id} value={ciclo.id}>{ciclo.tipo} · {ciclo.anio_base} · #{ciclo.id}</option>)}
              </select>
            </div>
            <div className="col-md-5">
              <label className="form-label" htmlFor="ciclo-b">Ciclo B</label>
              <select id="ciclo-b" className="form-select" value={cicloB} onChange={(evento) => setCicloB(evento.target.value)}>
                <option value="">Seleccione ciclo B</option>
                {ciclosFiltrados.map((ciclo) => <option key={ciclo.id} value={ciclo.id}>{ciclo.tipo} · {ciclo.anio_base} · #{ciclo.id}</option>)}
              </select>
            </div>
            <div className="col-md-2 d-flex align-items-end">
              <button type="submit" className="btn btn-primary w-100">Comparar</button>
            </div>
          </form>

          {comparacion ? (
            <div>
              <h2 className="h5">Diferencias destacadas</h2>
              {[
                ['diferencias_modelos', 'Valores de modelo'],
                ['diferencias_criterios', 'Valores de criterio'],
                ['diferencias_acciones', 'Estados de acciones'],
              ].map(([clave, titulo]) => (
                <section key={clave} className="card mb-3">
                  <div className="card-header"><strong>{titulo}</strong></div>
                  <div className="card-body">
                    {(comparacion[clave] ?? []).length === 0 ? <span>Sin diferencias</span> : (
                      <ul className="mb-0">
                        {(comparacion[clave] ?? []).map((diferencia, indice) => (
                          <li key={`${clave}-${indice}`} className="alert alert-warning py-2 mb-2" data-testid={`diferencia-${clave}`}>
                            {JSON.stringify(diferencia)}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </section>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  )
}

export default Analisis
