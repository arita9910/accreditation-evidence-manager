import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Cargando, Mensaje } from '../componentes'
import peticion from '../api/cliente'

const CATEGORIAS = {
  calificada: 'Calificada',
  certificada: 'Certificada',
  excelencia: 'Excelencia',
  unica: 'Única',
}

const TIPOS_DATO = {
  cuantitativo: 'Cuantitativo',
  cualitativo: 'Cualitativo',
}

function FichaCriterio() {
  const { codigo } = useParams()
  const [resultado, setResultado] = useState(null)

  useEffect(() => {
    let vigente = true

    peticion(`/api/catalogo/criterios/${encodeURIComponent(codigo)}/`)
      .then((datos) => {
        if (vigente) {
          setResultado({ codigo, criterio: datos, error: null })
        }
      })
      .catch((errorRecibido) => {
        if (vigente) {
          setResultado({
            codigo,
            criterio: null,
            error: errorRecibido.message,
          })
        }
      })

    return () => {
      vigente = false
    }
  }, [codigo])

  if (!resultado || resultado.codigo !== codigo) {
    return <Cargando texto="Cargando ficha de criterio..." />
  }

  if (resultado.error) {
    return (
      <>
        <p><Link to="/">Volver al catálogo</Link></p>
        <Mensaje tipo="error" titulo="No se pudo cargar el criterio">
          {resultado.error}
        </Mensaje>
      </>
    )
  }

  const criterio = resultado.criterio
  if (!criterio) {
    return (
      <>
        <p><Link to="/">Volver al catálogo</Link></p>
        <Mensaje tipo="error">No se encontró el criterio solicitado.</Mensaje>
      </>
    )
  }

  return (
    <article aria-labelledby="titulo-criterio">
      <p><Link to="/">Volver al catálogo</Link></p>
      <header className="mb-4">
        <h1 id="titulo-criterio">
          Criterio {criterio.codigo}
        </h1>
        <p>{criterio.texto}</p>
        <div className="d-flex flex-wrap gap-2">
          <span className="badge text-bg-secondary">
            {TIPOS_DATO[criterio.tipo_dato] ?? criterio.tipo_dato}
          </span>
          {criterio.solo_en_guia ? (
            <span className="badge text-bg-warning">Solo en la Guía</span>
          ) : null}
        </div>
      </header>

      <section className="mb-4">
        <h2 className="h4">Códigos normativos</h2>
        <dl className="row">
          <dt className="col-sm-3">Manual</dt>
          <dd className="col-sm-9">{criterio.codigo_manual || 'No registrado'}</dd>
          <dt className="col-sm-3">Guía</dt>
          <dd className="col-sm-9">{criterio.codigo_guia || 'No registrado'}</dd>
        </dl>
      </section>

      <section className="mb-4">
        <h2 className="h4">Evidencias sugeridas</h2>
        {criterio.evidencias?.length ? (
          <ul>
            {criterio.evidencias.map((evidencia, indice) => (
              <li key={`${evidencia.orden}-${indice}`}>
                {evidencia.texto}
                {evidencia.es_verificacion_externa ? (
                  <span className="badge text-bg-light ms-2">Verificación externa</span>
                ) : null}
              </li>
            ))}
          </ul>
        ) : <p>No hay evidencias registradas.</p>}
      </section>

      <section className="mb-4">
        <h2 className="h4">Requisitos por categoría</h2>
        <Mensaje tipo="info">
          Los requisitos se presentan como referencia; el sistema no calcula la categoría
          de acreditación.
        </Mensaje>
        {criterio.requisitos_por_categoria?.length ? (
          <ul>
            {criterio.requisitos_por_categoria.map((requisito) => (
              <li key={requisito.categoria}>
                <strong>
                  {CATEGORIAS[requisito.categoria] ?? requisito.categoria}:
                </strong>{' '}
                {requisito.texto}
              </li>
            ))}
          </ul>
        ) : <p>No hay requisitos por categoría registrados.</p>}
      </section>

      <section className="mb-4">
        <h2 className="h4">Nota normativa</h2>
        <p>{criterio.nota_normativa || 'No hay una nota normativa registrada.'}</p>
      </section>

      <section>
        <h2 className="h4">Modelos relacionados</h2>
        {criterio.modelos?.length ? (
          <ul>
            {criterio.modelos.map((modelo) => (
              <li key={`${modelo.numero}-${modelo.numero_rm36 ?? ''}`}>
                Modelo {modelo.numero}
                {modelo.numero_rm36 ? ` (RM 36: ${modelo.numero_rm36})` : ''}
                {modelo.nombre ? ` — ${modelo.nombre}` : ''}
              </li>
            ))}
          </ul>
        ) : <p>No hay modelos relacionados registrados.</p>}
      </section>
    </article>
  )
}

export default FichaCriterio
