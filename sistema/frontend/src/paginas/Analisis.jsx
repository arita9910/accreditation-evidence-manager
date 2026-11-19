import { useEffect, useMemo, useState } from 'react'
import peticion from '../api/cliente'
import { Cargando, Mensaje } from '../componentes'

const AVISOS = [
  ['criterios_sin_evidencia', 'Criterios sin evidencia'],
  ['criterios_cuantitativos_sin_dato', 'Criterios cuantitativos sin dato'],
  ['datos_sin_respaldo', 'Datos sin respaldo'],
  ['modelos_incompletos', 'Modelos incompletos'],
  ['dimensiones_sin_valoracion', 'Dimensiones sin valoración'],
  ['debilidades_sin_accion', 'Debilidades sin acción'],
]

function extraerLista(respuesta) {
  if (Array.isArray(respuesta)) return respuesta
  if (Array.isArray(respuesta?.results)) return respuesta.results
  return []
}

function nombreAviso(clave) {
  return AVISOS.find(([valor]) => valor === clave)?.[1] ?? clave
}

function codigoCriterioVisible(criterio) {
  return criterio?.codigo_manual || criterio?.codigo || null
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

  const criteriosPorId = useMemo(() => {
    const criterios = new Map()
    for (const dimension of estado?.dimensiones ?? []) {
      for (const indicador of dimension.indicadores ?? []) {
        for (const criterio of indicador.criterios ?? []) {
          criterios.set(Number(criterio.id), criterio)
        }
      }
    }
    return criterios
  }, [estado])

  const dimensionesPorId = useMemo(() => {
    const dimensiones = new Map()
    for (const dimension of estado?.dimensiones ?? []) {
      dimensiones.set(Number(dimension.id), dimension)
    }
    return dimensiones
  }, [estado])

  const formatearElementoAviso = (clave, elemento) => {
    if (clave === 'modelos_incompletos' && elemento && typeof elemento === 'object') {
      const faltantes = Math.max(0, Number(elemento.campos_esperados ?? 0) - Number(elemento.campos_presentes ?? 0))
      const numeroModelo = elemento.numero_modelo ?? elemento.modelo_id
      return `Modelo ${numeroModelo} - Curso ${elemento.curso}: Faltan ${faltantes} campos`
    }

    if (
      (clave === 'criterios_sin_evidencia' || clave === 'criterios_cuantitativos_sin_dato')
      && (typeof elemento === 'number' || typeof elemento === 'string')
    ) {
      const criterio = criteriosPorId.get(Number(elemento))
      if (!criterio) return `Criterio #${elemento}`
      const codigo = codigoCriterioVisible(criterio)
      return codigo ? `${codigo} · ${criterio.nombre}` : criterio.nombre
    }

    if (clave === 'dimensiones_sin_valoracion' && (typeof elemento === 'number' || typeof elemento === 'string')) {
      const dimension = dimensionesPorId.get(Number(elemento))
      if (!dimension) return `Dimensión #${elemento}`
      return dimension.nombre
    }

    if (clave === 'datos_sin_respaldo' && elemento && typeof elemento === 'object') {
      if (elemento.tipo === 'valor_modelo') {
        const modeloId = elemento.numero_modelo ?? elemento.modelo_id ?? 'N/D'
        const curso = elemento.curso ?? 'N/D'
        return `Dato del modelo ${modeloId} - Curso ${curso} sin evidencia`
      }
      if (elemento.tipo === 'valor_criterio') {
        const curso = elemento.curso ?? 'N/D'
        return `Dato del criterio ${elemento.criterio_id ?? 'N/D'} - Curso ${curso} sin evidencia`
      }
    }

    if (typeof elemento === 'object') return JSON.stringify(elemento)
    return `${nombreAviso(clave)} #${elemento}`
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
                          <div className="d-flex flex-wrap gap-2 mt-2">
                            <span className={`badge ${criterio.evidencias_clasificadas > 0 ? 'text-bg-success' : 'text-bg-warning'}`}>Evidencias: {criterio.evidencias_clasificadas}</span>
                            <span className={`badge ${criterio.datos_cuantitativos ? 'text-bg-success' : 'text-bg-secondary'}`}>Datos: {criterio.datos_cuantitativos ? 'Sí' : 'No'}</span>
                            <span className={`badge ${criterio.dato_con_respaldo ? 'text-bg-success' : 'text-bg-warning'}`}>Respaldo: {criterio.dato_con_respaldo ? 'Sí' : 'No'}</span>
                            <span className={`badge ${criterio.tiene_valoracion ? 'text-bg-success' : 'text-bg-secondary'}`}>Valoración: {criterio.tiene_valoracion ? 'Sí' : 'No'}</span>
                            <span className={`badge ${criterio.tiene_accion ? 'text-bg-success' : 'text-bg-secondary'}`}>Acción: {criterio.tiene_accion ? 'Sí' : 'No'}</span>
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
          {AVISOS.map(([clave, titulo]) => {
            const elementos = completitud[clave] ?? []
            if (soloAvisos && elementos.length === 0) return null
            return (
              <section key={clave} className="card mb-3">
                <div className="card-header d-flex justify-content-between">
                  <strong>{titulo}</strong>
                  <span className={`badge ${elementos.length ? 'text-bg-warning' : 'text-bg-success'}`}>{elementos.length}</span>
                </div>
                <div className="card-body">
                  {elementos.length === 0 ? <span>Sin avisos</span> : (
                    <ul className="mb-0">
                      {elementos.map((elemento, indice) => (
                        <li key={`${clave}-${indice}`} data-testid={`aviso-${clave}`}>
                          {formatearElementoAviso(clave, elemento)}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </section>
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
