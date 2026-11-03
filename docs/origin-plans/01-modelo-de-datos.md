# Plan 01 — Modelo de datos (32 entidades, por oleadas)

## Objetivo
Implementar el modelo de datos del dominio de forma coherente en todos los módulos: convenciones, restricciones de integridad y orden de migraciones. Este plan es la referencia transversal; **cada plan de módulo repite las entidades que implementa**, y este documento fija lo común y lo que cruza módulos.

## Contexto
- Django 5.2 + SQLite (desarrollo) / PostgreSQL (producción). **Sin SQL propio de un gestor** (D-14); las restricciones y migraciones deben funcionar en ambos.
- Nombres de entidades y campos en español, como el código (PEP 8 con nombres de dominio en español). Terminología: **Indicador** = 2.º nivel (24); **Criterio** = 3.er nivel (65).
- Todas las entidades heredan del modelo base del núcleo: `creado_en`, `modificado_en`, `creado_por`, `modificado_por` (FK a `settings.AUTH_USER_MODEL`, nulas).

## Convenciones
1. `on_delete=PROTECT` por defecto; `CASCADE` solo en hijos que no tienen sentido sin el padre (p. ej. EvidenciaSugerida de un Criterio).
2. Claves primarias automáticas (BigAutoField). Los nombres internos de fichero usan UUID.
3. Choices como `TextChoices` en español. Textos largos: `TextField`.
4. Restricciones con `UniqueConstraint`, `CheckConstraint` y condiciones (`condition=Q(...)`), soportadas por SQLite y PostgreSQL.
5. Cada modelo tiene `__str__` útil y `Meta.verbose_name` en español.
6. Cada restricción de la lista de abajo lleva una prueba que intenta violarla y comprueba que falla.
7. Migraciones: una por oleada y app; nunca editar migraciones ya aplicadas.

## Oleadas
| Oleada | Incremento | Entidades |
| :- | :- | :- |
| A | 0 | Modelo base (nucleo); **Usuario** (cuentas, primera migración); estructura: VersionNormativa, Dimension, Indicador, Criterio, EvidenciaSugerida, RequisitoCategoria, TipoEvidencia, ModeloDefinicion, ModeloCampo, CriterioModelo |
| B | 1 | Facultad, Carrera, Ciclo, AsignacionRol, AsignacionDimension, RegistroAuditoria |
| C | 2 | Evidencia, FicheroEvidencia, Clasificacion, Valoracion, ValoracionCriterio, ValoracionEvidencia |
| D | 3 | ValorModelo, ValorCriterio, VinculoDato, PlanMejora, AccionMejora, SeguimientoAccion, AccionEvidencia |
| E | 4 | TextoInforme, VersionInforme |

Total: 32 entidades (cinco son tablas de unión N:M: CriterioModelo, Clasificacion, ValoracionCriterio, ValoracionEvidencia, AccionEvidencia).

## Entidades (referencia completa)

### Estructura (solo lectura para los usuarios del proceso)
- **VersionNormativa:** nombre, fecha_aprobacion, fuentes, activa. Un ciclo apunta a una versión y la conserva aunque se cargue otra.
- **Dimension:** version (FK), codigo, nombre, orden. 6 por versión. Único (version, codigo).
- **Indicador:** dimension (FK), codigo («1.1»), texto. 24 por versión.
- **Criterio:** indicador (FK), codigo, codigo_manual (nulo), codigo_guia, solo_en_guia, texto, tipo_dato (cuantitativo/cualitativo), valoracion_por_categoria, nota_normativa. 65 por versión; el 3.2.4 tiene codigo_manual nulo y solo_en_guia verdadero.
- **EvidenciaSugerida:** criterio (FK), texto, orden, es_verificacion_externa. Las entrevistas y visitas se marcan como verificación externa.
- **RequisitoCategoria:** criterio (FK), categoria (calificada, certificada, excelencia, única), texto. Solo lectura.
- **TipoEvidencia:** dimension (FK), nombre, naturaleza (documento/actividad de verificación), soporte_exigido (papel firmado, digital, ambos).
- **ModeloDefinicion:** version (FK), numero, numero_rm36 (nulo), nombre. 11 por versión.
- **ModeloCampo:** modelo (FK), fila, columna, tipo_valor (entero, decimal, porcentaje, texto), orden.
- **CriterioModelo:** criterio (FK), modelo (FK). 20 criterios con modelo (propuesta a validar).

### Ciclos y cuentas
- **Facultad:** nombre. **Carrera:** facultad (FK), nombre, activa.
- **Ciclo:** carrera (FK), version_normativa (FK), tipo (autoevaluación, acreditación, reacreditación), anio_base, curso_inicial, curso_final, estado (abierto/cerrado), ciclo_anterior (FK nula), categoria_obtenida (nula), vigencia_anios (5, 7, 9 o nula), fecha_apertura, fecha_cierre.
- **Usuario** (modelo propio, D-01): username, nombre, apellidos, email, activo; contraseña con el almacenamiento seguro de Django.
- **AsignacionRol:** usuario (FK), rol, carrera/facultad/ciclo (FK nulas), vigente_desde, vigente_hasta (nula).
- **AsignacionDimension:** ciclo (FK), usuario (FK), dimension (FK). Único (ciclo, usuario, dimension).

### Evidencias y valoración
- **Evidencia:** ciclo (FK), tipo_evidencia (FK), titulo, descripcion, curso_academico, periodo_desde, periodo_hasta, soporte (digital/papel), custodia_original.
- **FicheroEvidencia:** evidencia (FK), version, nombre_original, nombre_interno (UUID), tamano, tipo_mime, sha256, vigente, subido_por. Nunca se sobrescribe (D-11).
- **Clasificacion:** evidencia (FK), criterio (FK), clasificada_por, fecha. Único (evidencia, criterio).
- **Valoracion:** ciclo (FK), dimension (FK), tipo (fortaleza/debilidad), texto, redactada_por.
- **ValoracionCriterio / ValoracionEvidencia:** valoracion (FK) + criterio (FK) o evidencia (FK).

### Datos cuantitativos y mejora
- **ValorModelo:** ciclo (FK), campo (FK a ModeloCampo), curso, valor, numerador, denominador. Único (ciclo, campo, curso).
- **ValorCriterio:** ciclo (FK), criterio (FK), curso (nulo), valor, numerador, denominador, unidad, observacion. Para los 20 criterios cuantitativos sin modelo.
- **VinculoDato:** evidencia (FK), valor_modelo (FK nulo), valor_criterio (FK nulo).
- **PlanMejora:** ciclo (FK), estado, aprobado_por. Uno por ciclo.
- **AccionMejora:** plan (FK), debilidad (FK a Valoracion tipo debilidad), descripcion, responsable (FK), fecha_limite, estado (propuesta, aprobada, en curso, cumplida, no cumplida), valoracion_resultado.
- **SeguimientoAccion:** accion (FK), fecha, avance, nota, registrado_por. Solo inserción.
- **AccionEvidencia:** accion (FK), evidencia (FK).

### Informes y auditoría
- **TextoInforme:** ciclo (FK), seccion, contenido, editado_por.
- **VersionInforme:** ciclo (FK), numero, fichero (nombre interno), sha256, paginas, metodo_conteo (LibreOffice/estimado), avisos.
- **RegistroAuditoria:** usuario (FK nulo), fecha_hora, accion, objeto_tipo, objeto_id, detalle, ip, resultado (correcto/denegado). Solo inserción.

## Restricciones de integridad que deben existir (con prueba cada una)
1. Único (version, codigo) en Dimension; códigos únicos por nivel dentro de una versión.
2. **VinculoDato:** `CheckConstraint` — exactamente uno de `valor_modelo` / `valor_criterio` no nulo.
3. **Ciclo:** un solo ciclo con `estado='abierto'` por carrera (`UniqueConstraint(fields=['carrera'], condition=Q(estado='abierto'))`).
4. **AsignacionRol:** exactamente el ámbito que corresponde al rol (miembro/director → carrera; decano → facultad; rector → ninguno; administrador técnico → ninguno; par evaluador → ciclo con `vigente_hasta` obligatorio). `CheckConstraint` o validación en `clean()` con prueba.
5. **Evidencia en papel:** `custodia_original` obligatoria; sin FicheroEvidencia.
6. **FicheroEvidencia:** único (evidencia, version); a lo sumo uno `vigente` por evidencia.
7. **AccionMejora:** `debilidad` obligatoria y de tipo debilidad (validación en servicio y `clean()`).
8. **Solo inserción** (RegistroAuditoria, SeguimientoAccion): `save()` en instancia existente y `delete()` lanzan error; el manager no expone `update`/`delete` masivos. Prueba incluida.
9. Único (ciclo, campo, curso) en ValorModelo; único (evidencia, criterio) en Clasificacion; único (ciclo, usuario, dimension).
10. **Ciclo cerrado = solo lectura:** los servicios de escritura de módulos posteriores lo comprueban (se prueba en cada módulo).

## Tareas
- **T1 (oleada A):** modelo base abstracto en `nucleo`; modelo `Usuario`; modelos de estructura; migraciones iniciales; pruebas de restricciones 1 y de `__str__`.
- **T2 (oleada B):** modelos de ciclos, cuentas (asignaciones) y auditoría; restricciones 3, 4, 8; pruebas.
- **T3 (oleada C):** evidencias y valoración; restricciones 5, 6, 9; pruebas.
- **T4 (oleada D):** cuantitativos y mejora; restricciones 2, 7, 8, 9; pruebas.
- **T5 (oleada E):** informes.
- **T6:** tras cada oleada, regenerar `docs/modelo-de-datos/` (diagramas Mermaid ER y de clases; fuentes en las Condiciones, anexos A y B) y ejecutar las migraciones y pruebas **también sobre PostgreSQL** antes de cerrar el incremento.

## Fuera de alcance
Lógica de negocio, API y pantallas (planes 02 a 12). Datos del catálogo (plan 03).

## Definición de terminado (por oleada)
Modelos y migraciones aplicadas en SQLite y PostgreSQL; pruebas de cada restricción en verde; diagrama actualizado; avance en `docs/avance/01-modelo-de-datos.md`.
