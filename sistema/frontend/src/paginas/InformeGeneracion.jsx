import { useEffect, useMemo, useState } from 'react'
import { Cargando, Mensaje } from '../componentes'
import peticion from '../api/cliente'

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
  if (modeloId) return `Dato del modelo ${modeloId} sin evidencia`
  if (elemento.criterio_id) return `Dato del criterio ${elemento.criterio_id} sin evidencia`
  return 'Dato sin respaldo sin detalle legible'
}

function formatearAviso(clave, valor) {
  if (typeof valor === 'string') return valor
  if (typeof valor === 'number') return String(valor)
  if (!valor || typeof valor !== 'object') return String(valor)

  if (clave === 'datos_sin_respaldo') return formatearDatoSinRespaldo(valor)
  if (typeof valor.descripcion === 'string' && valor.descripcion.trim()) return valor.descripcion.trim()
  if (typeof valor.mensaje === 'string' && valor.mensaje.trim()) return valor.mensaje.trim()
  return JSON.stringify(valor)
}

function avisosCompletitud(completitud) {
  if (!completitud) return []

  if (Array.isArray(completitud.avisos)) {
    return [{ clave: 'avisos', elementos: completitud.avisos.map((valor) => formatearAviso('Aviso', valor)) }]
  }
  if (Array.isArray(completitud.mensajes)) {
    return [{ clave: 'mensajes', elementos: completitud.mensajes.map((valor) => formatearAviso('Mensaje', valor)) }]
  }

  return AVISOS.flatMap(([clave]) => {
    const valor = completitud[clave]
    if (!Array.isArray(valor)) {
      return valor ? [{ clave, elementos: [formatearAviso(clave, valor)] }] : []
    }
    if (valor.length === 0 && clave === 'debilidades_sin_accion') {
      return [{ clave, elementos: ['No hay debilidades pendientes por resolver'] }]
    }
    if (valor.length === 0) return []
    return [{
      clave,
      elementos: valor.map((elemento) => formatearAviso(clave, elemento)),
    }]
  })
}

function InformeGeneracion({ usuario }) {
  const autorizado = usuario?.rol === 'administrador_tecnico' || usuario?.rol === 'director_carrera'
  const [ciclos, setCiclos] = useState([])
  const [cicloId, setCicloId] = useState('')
  const [completitud, setCompletitud] = useState(null)
  const [versiones, setVersiones] = useState([])
  const [generando, setGenerando] = useState(false)
  const [cargando, setCargando] = useState(autorizado)
  const [error, setError] = useState('')
  const [mensaje, setMensaje] = useState('')

  useEffect(() => {
    if (!autorizado) {
      setCargando(false)
      return undefined
    }
    let vigente = true
    peticion('/api/ciclos/')
      .then((respuesta) => {
        if (!vigente) return
        const lista = extraerLista(respuesta)
        const permitidos = usuario?.rol === 'director_carrera'
          ? lista.filter((ciclo) => String(ciclo.carrera) === String(usuario.carrera))
          : lista
        setCiclos(permitidos)
        if (permitidos.length > 0) setCicloId(String(permitidos[0].id))
      })
      .catch((errorRecibido) => vigente && setError(errorRecibido.message))
      .finally(() => vigente && setCargando(false))
    return () => { vigente = false }
  }, [autorizado, usuario])

  useEffect(() => {
    if (!cicloId) return undefined
    let vigente = true
    setError('')
    Promise.all([
      peticion(`/api/ciclos/${cicloId}/completitud/`),
      peticion(`/api/ciclos/${cicloId}/informe/versiones/`),
    ])
      .then(([completitudRespuesta, versionesRespuesta]) => {
        if (!vigente) return
        setCompletitud(completitudRespuesta)
        setVersiones(extraerLista(versionesRespuesta?.versiones))
      })
      .catch((errorRecibido) => vigente && setError(errorRecibido.message))
    return () => { vigente = false }
  }, [cicloId])

  const avisos = useMemo(() => {
    return avisosCompletitud(completitud)
  }, [completitud])

  const generar = async () => {
    setGenerando(true)
    setError('')
    setMensaje('')
    try {
      const creada = await peticion(`/api/ciclos/${cicloId}/informe/generar/`, { method: 'POST' })
      setMensaje(`Versión ${creada.numero} generada correctamente.`)
      const respuesta = await peticion(`/api/ciclos/${cicloId}/informe/versiones/`)
      setVersiones(extraerLista(respuesta?.versiones))
    } catch (errorRecibido) {
      setError(errorRecibido.message)
    } finally {
      setGenerando(false)
    }
  }

  if (!autorizado) {
    return <Mensaje tipo="error" titulo="Acceso denegado">Tu rol no permite generar informes.</Mensaje>
  }
  if (cargando) return <Cargando texto="Cargando generación de informes..." />

  const ciclo = ciclos.find((item) => String(item.id) === String(cicloId))
  const cerrado = ciclo?.estado === 'cerrado'

  return (
    <section aria-labelledby="titulo-informe-generacion">
      <h1 id="titulo-informe-generacion">Generación de informe</h1>
      {error ? <Mensaje tipo="error" titulo="Error">{error}</Mensaje> : null}
      {mensaje ? <Mensaje tipo="success" titulo="Informe generado">{mensaje}</Mensaje> : null}
      <div className="mb-4">
        <label className="form-label" htmlFor="generacion-ciclo">Ciclo</label>
        <select className="form-select" id="generacion-ciclo" value={cicloId} onChange={(evento) => setCicloId(evento.target.value)}>
          <option value="">Seleccione un ciclo</option>
          {ciclos.map((item) => (
            <option key={item.id} value={item.id}>{item.tipo} · {item.anio_base}</option>
          ))}
        </select>
      </div>
      {cerrado ? <Mensaje tipo="warning" titulo="Ciclo cerrado">La generación requiere un ciclo abierto.</Mensaje> : null}
      {avisos.length > 0 ? (
        <Mensaje tipo="warning" titulo="Avisos de completitud">
          <ul className="mb-0">
            {avisos.map((grupo) => (
              <li key={grupo.clave}>
                <strong>{grupo.clave}:</strong> {grupo.elementos.join(', ')}
              </li>
            ))}
          </ul>
        </Mensaje>
      ) : null}
      <button
        className="btn btn-primary mb-4"
        type="button"
        disabled={!cicloId || cerrado || generando}
        onClick={generar}
      >
        {generando ? 'Generando...' : 'Generar informe'}
      </button>
      <h2 className="h4">Historial de versiones</h2>
      {versiones.length === 0 ? <Mensaje tipo="info">Aún no existen versiones generadas.</Mensaje> : (
        <div className="table-responsive">
          <table className="table align-middle">
            <thead><tr><th>Versión</th><th>Páginas</th><th>Método</th><th>Acciones</th></tr></thead>
            <tbody>
              {versiones.map((version) => (
                <tr key={version.id}>
                  <td>v{version.numero}</td>
                  <td>{version.paginas ?? '—'}</td>
                  <td>{version.metodo_conteo ?? '—'}</td>
                  <td>
                    <a className="btn btn-outline-primary btn-sm" href={`/api/informes/versiones/${version.id}/descarga/`}>
                      Descargar
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default InformeGeneracion
