import { useEffect, useMemo, useState } from 'react'
import peticion from '../api/cliente'
import { Cargando, Mensaje } from '../componentes'

const ESTADOS_FINALES = new Set(['cumplida', 'no_cumplida'])

const FORM_ACCION_INICIAL = {
  debilidad: '',
  descripcion: '',
  responsable: '',
  fecha_limite: '',
}

const FORM_SEGUIMIENTO_INICIAL = {
  avance: '',
  nota: '',
}

const FORM_PLAN_INICIAL = {
  estado: '',
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

function esFechaVencida(fechaLimite) {
  if (!fechaLimite) {
    return false
  }
  const hoy = new Date().toISOString().slice(0, 10)
  return String(fechaLimite) < hoy
}

function esAccionVencida(accion) {
  return !ESTADOS_FINALES.has(String(accion.estado)) && esFechaVencida(accion.fecha_limite)
}

function Mejora() {
  const [ciclos, setCiclos] = useState([])
  const [cicloId, setCicloId] = useState('')
  const [plan, setPlan] = useState(null)
  const [acciones, setAcciones] = useState([])
  const [usuarios, setUsuarios] = useState([])
  const [debilidades, setDebilidades] = useState([])
  const [planAnterior, setPlanAnterior] = useState(null)
  const [seguimientos, setSeguimientos] = useState([])
  const [accionSeleccionadaId, setAccionSeleccionadaId] = useState('')
  const [cargandoBase, setCargandoBase] = useState(true)
  const [cargandoDetalle, setCargandoDetalle] = useState(false)
  const [creandoPlan, setCreandoPlan] = useState(false)
  const [guardandoAccion, setGuardandoAccion] = useState(false)
  const [guardandoSeguimiento, setGuardandoSeguimiento] = useState(false)
  const [mensaje, setMensaje] = useState('')
  const [errorGeneral, setErrorGeneral] = useState('')
  const [errorPlan, setErrorPlan] = useState('')
  const [errorFormularioAccion, setErrorFormularioAccion] = useState('')
  const [errorFormularioSeguimiento, setErrorFormularioSeguimiento] = useState('')
  const [formularioAccion, setFormularioAccion] = useState(FORM_ACCION_INICIAL)
  const [formularioSeguimiento, setFormularioSeguimiento] = useState(FORM_SEGUIMIENTO_INICIAL)
  const [formularioPlan, setFormularioPlan] = useState(FORM_PLAN_INICIAL)
  const [editandoPlan, setEditandoPlan] = useState(false)
  const [guardandoPlan, setGuardandoPlan] = useState(false)
  const [accionEditandoId, setAccionEditandoId] = useState('')
  const [eliminandoAccionId, setEliminandoAccionId] = useState('')

  const cicloSeleccionado = useMemo(
    () => ciclos.find((ciclo) => String(ciclo.id) === String(cicloId)) ?? null,
    [ciclos, cicloId],
  )

  const cicloAbierto = cicloSeleccionado?.estado === 'abierto'

  const accionSeleccionada = useMemo(
    () => acciones.find((accion) => String(accion.id) === String(accionSeleccionadaId)) ?? null,
    [acciones, accionSeleccionadaId],
  )

  const nombreResponsable = (accion) => {
    if (accion?.responsable_nombre) {
      return accion.responsable_nombre
    }
    const encontrado = usuarios.find((usuario) => String(usuario.id) === String(accion?.responsable))
    if (!encontrado) {
      return accion?.responsable ?? ''
    }
    return [encontrado.nombre, encontrado.apellidos].filter(Boolean).join(' ') || encontrado.username
  }

  const cargarCiclos = async () => {
    const respuesta = await peticion('/api/ciclos/')
    const lista = extraerLista(respuesta)
    setCiclos(lista)
    if (lista.length > 0) {
      setCicloId((previo) => previo || String(lista[0].id))
    } else {
      setCicloId('')
    }
  }

  const cargarSeguimientos = async (accionId) => {
    if (!accionId) {
      setSeguimientos([])
      return
    }
    const respuesta = await peticion(`/api/acciones/${accionId}/seguimientos/`)
    setSeguimientos(extraerLista(respuesta))
  }

  const cargarDetalle = async (idCiclo) => {
    if (!idCiclo) {
      setPlan(null)
      setAcciones([])
      setDebilidades([])
      setPlanAnterior(null)
      setSeguimientos([])
      setAccionSeleccionadaId('')
      return
    }

    setCargandoDetalle(true)
    setErrorGeneral('')
    setErrorPlan('')
    setMensaje('')
    setErrorFormularioAccion('')
    setErrorFormularioSeguimiento('')
    try {
      const ciclo = ciclos.find((registro) => String(registro.id) === String(idCiclo))
      const carreraQuery = ciclo?.carrera ? `?carrera=${ciclo.carrera}` : ''
      const [respuestaDebilidades, respuestaPlanAnterior, respuestaUsuarios] = await Promise.all([
        peticion(`/api/ciclos/${idCiclo}/valoraciones/?tipo=debilidad`),
        peticion(`/api/ciclos/${idCiclo}/plan-anterior/`).catch(() => null),
        peticion(`/api/usuarios/${carreraQuery}`),
      ])

      setDebilidades(extraerLista(respuestaDebilidades))
      setPlanAnterior(respuestaPlanAnterior)
      setUsuarios(extraerLista(respuestaUsuarios))

      try {
        const planRecibido = await peticion(`/api/ciclos/${idCiclo}/plan/`)
        setPlan(planRecibido)
        setFormularioPlan({ estado: planRecibido.estado || '' })
        setEditandoPlan(false)
        const accionesRecibidas = await peticion(`/api/planes/${planRecibido.id}/acciones/`)
        const accionesLista = extraerLista(accionesRecibidas)
        setAcciones(accionesLista)
        const siguienteAccionId = (() => {
          let seleccion = ''
          setAccionSeleccionadaId((previo) => {
            if (accionesLista.some((accion) => String(accion.id) === String(previo))) {
              seleccion = String(previo)
              return previo
            }
            seleccion = accionesLista.length > 0 ? String(accionesLista[0].id) : ''
            return seleccion
          })
          return seleccion
        })()
        if (siguienteAccionId) {
          await cargarSeguimientos(siguienteAccionId)
        } else {
          setSeguimientos([])
        }
      } catch (errorPlanRecibido) {
        setPlan(null)
        setFormularioPlan(FORM_PLAN_INICIAL)
        setEditandoPlan(false)
        setAcciones([])
        setAccionSeleccionadaId('')
        setSeguimientos([])
        setErrorPlan(errorPlanRecibido.message)
      }
    } catch (errorRecibido) {
      setErrorGeneral(errorRecibido.message)
      setPlan(null)
      setAcciones([])
      setDebilidades([])
      setUsuarios([])
      setPlanAnterior(null)
      setAccionSeleccionadaId('')
      setSeguimientos([])
    } finally {
      setCargandoDetalle(false)
    }
  }

  useEffect(() => {
    let vigente = true

    setCargandoBase(true)
    cargarCiclos()
      .catch((errorRecibido) => {
        if (vigente) {
          setErrorGeneral(errorRecibido.message)
          setCiclos([])
          setCicloId('')
        }
      })
      .finally(() => {
        if (vigente) {
          setCargandoBase(false)
        }
      })

    return () => {
      vigente = false
    }
  }, [])

  useEffect(() => {
    cargarDetalle(cicloId)
  }, [cicloId])

  useEffect(() => {
    cargarSeguimientos(accionSeleccionadaId).catch(() => {
      setSeguimientos([])
    })
  }, [accionSeleccionadaId])

  const crearPlan = async () => {
    if (!cicloId) {
      setErrorPlan('Debe seleccionar un ciclo.')
      return
    }
    if (!cicloAbierto) {
      setErrorPlan('No se puede crear el plan porque el ciclo está cerrado.')
      return
    }

    setCreandoPlan(true)
    setErrorPlan('')
    setMensaje('')
    try {
      const creado = await peticion(`/api/ciclos/${cicloId}/plan/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })
      setPlan(creado)
      setFormularioPlan({ estado: creado.estado || '' })
      setEditandoPlan(false)
      const accionesRecibidas = await peticion(`/api/planes/${creado.id}/acciones/`)
      const accionesLista = extraerLista(accionesRecibidas)
      setAcciones(accionesLista)
      if (accionesLista.length > 0) {
        const accionId = String(accionesLista[0].id)
        setAccionSeleccionadaId(accionId)
        await cargarSeguimientos(accionId)
      } else {
        setAccionSeleccionadaId('')
        setSeguimientos([])
      }
      setMensaje('Plan de mejora creado correctamente.')
    } catch (errorRecibido) {
      setErrorPlan(errorRecibido.message)
    } finally {
      setCreandoPlan(false)
    }
  }

  const enviarAccion = async (evento) => {
    evento.preventDefault()
    setErrorFormularioAccion('')
    setMensaje('')

    if (!cicloAbierto) {
      setErrorFormularioAccion('El ciclo seleccionado está cerrado; no se pueden registrar acciones.')
      return
    }
    if (!plan) {
      setErrorFormularioAccion('Debe crear el plan de mejora antes de registrar acciones.')
      return
    }
    if (!formularioAccion.debilidad) {
      setErrorFormularioAccion('Debe seleccionar una debilidad de origen.')
      return
    }
    if (!debilidades.some((debilidad) => String(debilidad.id) === String(formularioAccion.debilidad))) {
      setErrorFormularioAccion('La debilidad seleccionada no es válida para este ciclo.')
      return
    }
    if (!formularioAccion.descripcion.trim()) {
      setErrorFormularioAccion('Debe indicar la descripción de la acción.')
      return
    }
    if (!formularioAccion.responsable || !Number.isInteger(Number(formularioAccion.responsable))) {
      setErrorFormularioAccion('Debe indicar un responsable válido.')
      return
    }
    if (!formularioAccion.fecha_limite) {
      setErrorFormularioAccion('Debe indicar la fecha límite de la acción.')
      return
    }

    setGuardandoAccion(true)
    try {
      const payload = {
        descripcion: formularioAccion.descripcion.trim(),
        responsable: Number(formularioAccion.responsable),
        fecha_limite: formularioAccion.fecha_limite,
      }
      if (accionEditandoId) {
        await peticion(`/api/acciones/${accionEditandoId}/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
      } else {
        await peticion(`/api/planes/${plan.id}/acciones/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            debilidad: Number(formularioAccion.debilidad),
            ...payload,
          }),
        })
      }
      const accionesRecibidas = await peticion(`/api/planes/${plan.id}/acciones/`)
      const accionesLista = extraerLista(accionesRecibidas)
      setAcciones(accionesLista)
      setAccionSeleccionadaId(accionesLista.length > 0 ? String(accionesLista[0].id) : '')
      setFormularioAccion({
        ...FORM_ACCION_INICIAL,
      })
      setAccionEditandoId('')
      setMensaje(accionEditandoId ? 'Acción de mejora actualizada correctamente.' : 'Acción de mejora registrada correctamente.')
    } catch (errorRecibido) {
      setErrorFormularioAccion(errorRecibido.message)
    } finally {
      setGuardandoAccion(false)
    }
  }

  const editarAccion = (accion) => {
    setAccionEditandoId(String(accion.id))
    setFormularioAccion({
      debilidad: String(accion.debilidad ?? ''),
      descripcion: accion.descripcion ?? '',
      responsable: String(accion.responsable ?? ''),
      fecha_limite: accion.fecha_limite ?? '',
    })
    setErrorFormularioAccion('')
    setMensaje('')
  }

  const cancelarEdicionAccion = () => {
    setAccionEditandoId('')
    setFormularioAccion(FORM_ACCION_INICIAL)
  }

  const eliminarAccion = async (accion) => {
    if (!cicloAbierto) {
      setErrorFormularioAccion('El ciclo seleccionado está cerrado; no se pueden eliminar acciones.')
      return
    }
    setErrorFormularioAccion('')
    setMensaje('')
    setEliminandoAccionId(String(accion.id))
    try {
      await peticion(`/api/acciones/${accion.id}/`, {
        method: 'DELETE',
      })
      const accionesRecibidas = await peticion(`/api/planes/${plan.id}/acciones/`)
      const accionesLista = extraerLista(accionesRecibidas)
      setAcciones(accionesLista)
      if (!accionesLista.some((registro) => String(registro.id) === String(accionSeleccionadaId))) {
        setAccionSeleccionadaId(accionesLista.length > 0 ? String(accionesLista[0].id) : '')
      }
      if (String(accionEditandoId) === String(accion.id)) {
        cancelarEdicionAccion()
      }
      setMensaje('Acción de mejora eliminada correctamente.')
    } catch (errorRecibido) {
      setErrorFormularioAccion(errorRecibido.message)
    } finally {
      setEliminandoAccionId('')
    }
  }

  const guardarPlan = async (evento) => {
    evento.preventDefault()
    setErrorPlan('')
    setMensaje('')
    if (!plan) {
      setErrorPlan('Debe existir un plan para poder editarlo.')
      return
    }
    if (!cicloAbierto) {
      setErrorPlan('El ciclo seleccionado está cerrado; no se puede editar el plan.')
      return
    }
    setGuardandoPlan(true)
    try {
      const actualizado = await peticion(`/api/planes/${plan.id}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ estado: formularioPlan.estado }),
      })
      setPlan(actualizado)
      setFormularioPlan({ estado: actualizado.estado || '' })
      setEditandoPlan(false)
      setMensaje('Plan de mejora actualizado correctamente.')
    } catch (errorRecibido) {
      setErrorPlan(errorRecibido.message)
    } finally {
      setGuardandoPlan(false)
    }
  }

  const enviarSeguimiento = async (evento) => {
    evento.preventDefault()
    setErrorFormularioSeguimiento('')
    setMensaje('')

    if (!cicloAbierto) {
      setErrorFormularioSeguimiento('El ciclo seleccionado está cerrado; no se pueden registrar seguimientos.')
      return
    }
    if (!accionSeleccionada) {
      setErrorFormularioSeguimiento('Debe seleccionar una acción de mejora.')
      return
    }
    if (formularioSeguimiento.avance === '') {
      setErrorFormularioSeguimiento('Debe indicar el porcentaje de avance.')
      return
    }
    const avance = Number(formularioSeguimiento.avance)
    if (!Number.isInteger(avance) || avance < 0 || avance > 100) {
      setErrorFormularioSeguimiento('El avance debe ser un entero entre 0 y 100.')
      return
    }

    setGuardandoSeguimiento(true)
    try {
      await peticion(`/api/acciones/${accionSeleccionada.id}/seguimientos/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          avance,
          nota: formularioSeguimiento.nota.trim(),
        }),
      })
      await cargarSeguimientos(accionSeleccionada.id)
      setFormularioSeguimiento(FORM_SEGUIMIENTO_INICIAL)
      setMensaje('Seguimiento registrado correctamente.')
    } catch (errorRecibido) {
      setErrorFormularioSeguimiento(errorRecibido.message)
    } finally {
      setGuardandoSeguimiento(false)
    }
  }

  if (cargandoBase) {
    return <Cargando texto="Cargando módulo de mejora..." />
  }

  return (
    <section className="d-flex flex-column gap-4">
      <header>
        <h1 className="h3 mb-1">Plan de mejora</h1>
        <p className="text-secondary mb-0">
          Gestión del plan del ciclo, acciones y seguimiento con comparación del plan anterior.
        </p>
      </header>

      {errorGeneral ? <Mensaje tipo="error">{errorGeneral}</Mensaje> : null}
      {mensaje ? <Mensaje tipo="success">{mensaje}</Mensaje> : null}

      <div className="card shadow-sm">
        <div className="card-body">
          <label className="form-label" htmlFor="mejora-ciclo">Ciclo</label>
          <select
            id="mejora-ciclo"
            className="form-select"
            value={cicloId}
            onChange={(evento) => setCicloId(evento.target.value)}
          >
            {ciclos.map((ciclo) => (
              <option key={ciclo.id} value={String(ciclo.id)}>
                #{ciclo.id} · {ciclo.tipo} · {ciclo.anio_base} · {ciclo.estado}
              </option>
            ))}
          </select>
          {!cicloAbierto && cicloSeleccionado ? (
            <div className="mt-2 small text-danger">
              El ciclo está cerrado. Solo se permite la consulta del plan.
            </div>
          ) : null}
        </div>
      </div>

      {cargandoDetalle ? <Cargando texto="Cargando detalle del plan..." /> : (
        <>
          <div className="row g-3">
            <div className="col-12 col-xl-6">
              <div className="card h-100 shadow-sm">
                <div className="card-body">
                  <h2 className="h5">Plan actual</h2>
                  {plan ? (
                    <>
                      <p className="mb-1">
                        <strong>ID:</strong> {plan.id}
                      </p>
                      <p className="mb-1">
                        <strong>Estado:</strong> {plan.estado}
                      </p>
                      <p className="mb-0">
                        <strong>Aprobado por:</strong> {plan.aprobado_por_nombre || plan.aprobado_por || 'Pendiente'}
                      </p>
                      {errorPlan ? <Mensaje tipo="warning">{errorPlan}</Mensaje> : null}
                      {editandoPlan ? (
                        <form className="mt-3 d-flex flex-column gap-2" onSubmit={guardarPlan}>
                          <label className="form-label mb-0" htmlFor="plan-estado">Estado del plan</label>
                          <select
                            id="plan-estado"
                            className="form-select"
                            value={formularioPlan.estado}
                            onChange={(evento) => setFormularioPlan({ estado: evento.target.value })}
                          >
                            <option value="borrador">borrador</option>
                            <option value="aprobado">aprobado</option>
                            <option value="cerrado">cerrado</option>
                          </select>
                          <div className="d-flex gap-2">
                            <button className="btn btn-sm btn-primary" type="submit" disabled={guardandoPlan || !cicloAbierto}>
                              {guardandoPlan ? 'Guardando plan...' : 'Guardar plan'}
                            </button>
                            <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => setEditandoPlan(false)}>
                              Cancelar
                            </button>
                          </div>
                        </form>
                      ) : (
                        <button
                          type="button"
                          className="btn btn-outline-primary btn-sm mt-3"
                          onClick={() => setEditandoPlan(true)}
                          disabled={!cicloAbierto}
                        >
                          Editar plan
                        </button>
                      )}
                    </>
                  ) : (
                    <>
                      {errorPlan ? <Mensaje tipo="warning">{errorPlan}</Mensaje> : null}
                      <Mensaje tipo="info">Todavía no existe un plan de mejora para este ciclo.</Mensaje>
                      <button
                        type="button"
                        className="btn btn-primary"
                        onClick={crearPlan}
                        disabled={creandoPlan || !cicloAbierto}
                      >
                        {creandoPlan ? 'Creando plan...' : 'Crear plan del ciclo'}
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
            <div className="col-12 col-xl-6">
              <div className="card h-100 shadow-sm">
                <div className="card-body">
                  <h2 className="h5">Plan del ciclo anterior</h2>
                  {planAnterior ? (
                    <>
                      <p className="mb-2">
                        <strong>Estado:</strong> {planAnterior.plan?.estado ?? 'Sin estado'}
                      </p>
                      {extraerLista(planAnterior.acciones).length === 0 ? (
                        <p className="text-secondary mb-0">Sin acciones registradas.</p>
                      ) : (
                        <ul className="list-group list-group-flush">
                          {extraerLista(planAnterior.acciones).map((accion) => (
                            <li key={accion.id} className="list-group-item px-0">
                              {accion.descripcion}
                              <span className="badge text-bg-secondary ms-2">{accion.estado}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </>
                  ) : (
                    <Mensaje tipo="info">No hay plan anterior disponible para comparar.</Mensaje>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="card shadow-sm">
            <div className="card-body">
              <h2 className="h5">Acciones del plan</h2>
              {!plan ? (
                <Mensaje tipo="info">Cree primero el plan para registrar y gestionar acciones.</Mensaje>
              ) : acciones.length === 0 ? (
                <Mensaje tipo="info">No hay acciones registradas en este plan.</Mensaje>
              ) : (
                <div className="table-responsive">
                  <table className="table align-middle">
                    <thead>
                      <tr>
                        <th>Descripción</th>
                        <th>Responsable</th>
                        <th>Fecha límite</th>
                        <th>Estado</th>
                        <th />
                      </tr>
                    </thead>
                    <tbody>
                      {acciones.map((accion) => {
                        const vencida = esAccionVencida(accion)
                        return (
                          <tr key={accion.id} className={vencida ? 'table-danger' : ''}>
                            <td>{accion.descripcion}</td>
                            <td>{nombreResponsable(accion)}</td>
                            <td>
                              {accion.fecha_limite}
                              {vencida ? <span className="badge text-bg-danger ms-2">Vencida</span> : null}
                            </td>
                            <td>{accion.estado}</td>
                            <td className="text-end">
                              <div className="d-flex justify-content-end gap-2">
                                <button
                                  type="button"
                                  className="btn btn-sm btn-outline-primary"
                                  onClick={() => setAccionSeleccionadaId(String(accion.id))}
                                >
                                  Ver seguimiento
                                </button>
                                <button
                                  type="button"
                                  className="btn btn-sm btn-outline-secondary"
                                  onClick={() => editarAccion(accion)}
                                  disabled={!cicloAbierto}
                                >
                                  Editar
                                </button>
                                <button
                                  type="button"
                                  className="btn btn-sm btn-outline-danger"
                                  onClick={() => eliminarAccion(accion)}
                                  disabled={!cicloAbierto || eliminandoAccionId === String(accion.id)}
                                >
                                  {eliminandoAccionId === String(accion.id) ? 'Eliminando...' : 'Eliminar'}
                                </button>
                              </div>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          <div className="row g-3">
            <div className="col-12 col-xl-6">
              <form className="card h-100 shadow-sm" onSubmit={enviarAccion}>
                <div className="card-body d-flex flex-column gap-3">
                  <h2 className="h5 mb-0">{accionEditandoId ? 'Editar acción' : 'Registrar acción'}</h2>
                  {errorFormularioAccion ? <Mensaje tipo="error">{errorFormularioAccion}</Mensaje> : null}

                  <div>
                    <label className="form-label" htmlFor="accion-debilidad">Debilidad de origen</label>
                    <select
                      id="accion-debilidad"
                      className="form-select"
                      value={formularioAccion.debilidad}
                      onChange={(evento) => setFormularioAccion((previo) => ({ ...previo, debilidad: evento.target.value }))}
                    >
                      <option value="">Seleccione</option>
                      {debilidades.map((debilidad) => (
                        <option key={debilidad.id} value={String(debilidad.id)}>
                          #{debilidad.id} · {debilidad.texto}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="form-label" htmlFor="accion-descripcion">Descripción</label>
                    <textarea
                      id="accion-descripcion"
                      className="form-control"
                      rows={3}
                      value={formularioAccion.descripcion}
                      onChange={(evento) => setFormularioAccion((previo) => ({ ...previo, descripcion: evento.target.value }))}
                    />
                  </div>

                  <div className="row g-2">
                    <div className="col-12 col-md-6">
                      <label className="form-label" htmlFor="accion-responsable">Responsable</label>
                      <select
                        id="accion-responsable"
                        className="form-select"
                        value={formularioAccion.responsable}
                        onChange={(evento) => setFormularioAccion((previo) => ({ ...previo, responsable: evento.target.value }))}
                      >
                        <option value="">Seleccione</option>
                        {usuarios.map((registro) => (
                          <option key={registro.id} value={String(registro.id)}>
                            {[registro.nombre, registro.apellidos].filter(Boolean).join(' ') || registro.username}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="col-12 col-md-6">
                      <label className="form-label" htmlFor="accion-fecha">Fecha límite</label>
                      <input
                        id="accion-fecha"
                        className="form-control"
                        type="date"
                        value={formularioAccion.fecha_limite}
                        onChange={(evento) => setFormularioAccion((previo) => ({ ...previo, fecha_limite: evento.target.value }))}
                      />
                    </div>
                  </div>

                  <button
                    className="btn btn-primary"
                    type="submit"
                    disabled={
                      guardandoAccion
                      || !plan
                      || !cicloAbierto
                      || !formularioAccion.debilidad
                      || !formularioAccion.descripcion.trim()
                      || !formularioAccion.responsable
                      || !formularioAccion.fecha_limite
                    }
                  >
                    {guardandoAccion ? 'Guardando...' : accionEditandoId ? 'Guardar cambios' : 'Registrar acción'}
                  </button>
                  {accionEditandoId ? (
                    <button
                      className="btn btn-outline-secondary"
                      type="button"
                      onClick={cancelarEdicionAccion}
                      disabled={guardandoAccion}
                    >
                      Cancelar edición
                    </button>
                  ) : null}
                </div>
              </form>
            </div>

            <div className="col-12 col-xl-6">
              <div className="card h-100 shadow-sm">
                <div className="card-body d-flex flex-column gap-3">
                  <h2 className="h5 mb-0">Seguimiento de la acción</h2>
                  {errorFormularioSeguimiento ? <Mensaje tipo="error">{errorFormularioSeguimiento}</Mensaje> : null}
                  {accionSeleccionada ? (
                    <>
                      <div>
                        <strong>Acción seleccionada:</strong> {accionSeleccionada.descripcion}
                      </div>
                      <form className="d-flex flex-column gap-2" onSubmit={enviarSeguimiento}>
                        <div>
                          <label className="form-label" htmlFor="seguimiento-avance">Avance (%)</label>
                          <input
                            id="seguimiento-avance"
                            className="form-control"
                            type="number"
                            min="0"
                            max="100"
                            step="1"
                            value={formularioSeguimiento.avance}
                            onChange={(evento) => setFormularioSeguimiento((previo) => ({ ...previo, avance: evento.target.value }))}
                          />
                        </div>
                        <div>
                          <label className="form-label" htmlFor="seguimiento-nota">Nota</label>
                          <textarea
                            id="seguimiento-nota"
                            className="form-control"
                            rows={2}
                            value={formularioSeguimiento.nota}
                            onChange={(evento) => setFormularioSeguimiento((previo) => ({ ...previo, nota: evento.target.value }))}
                          />
                        </div>
                        <button
                          className="btn btn-outline-primary"
                          type="submit"
                          disabled={guardandoSeguimiento || !cicloAbierto}
                        >
                          {guardandoSeguimiento ? 'Guardando seguimiento...' : 'Registrar seguimiento'}
                        </button>
                      </form>

                      <div>
                        <h3 className="h6">Historial</h3>
                        {seguimientos.length === 0 ? (
                          <p className="text-secondary mb-0">Sin seguimientos registrados.</p>
                        ) : (
                          <ul className="list-group list-group-flush">
                            {seguimientos.map((seguimiento) => (
                              <li key={seguimiento.id} className="list-group-item px-0">
                                {seguimiento.avance}% · {seguimiento.nota || 'Sin nota'} · usuario {seguimiento.registrado_por}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </>
                  ) : (
                    <Mensaje tipo="info">Seleccione una acción para consultar o registrar seguimiento.</Mensaje>
                  )}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </section>
  )
}

export default Mejora
