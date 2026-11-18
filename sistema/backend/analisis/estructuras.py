from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CriterioEstado:
    id: int
    codigo: str
    nombre: str
    evidencias_clasificadas: int = 0
    datos_cuantitativos: bool = False
    dato_con_respaldo: bool = False
    tiene_valoracion: bool = False
    tiene_accion: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "evidencias_clasificadas": self.evidencias_clasificadas,
            "datos_cuantitativos": self.datos_cuantitativos,
            "dato_con_respaldo": self.dato_con_respaldo,
            "tiene_valoracion": self.tiene_valoracion,
            "tiene_accion": self.tiene_accion,
        }


@dataclass(frozen=True)
class IndicadorEstado:
    id: int
    codigo: str
    nombre: str
    criterios: tuple[CriterioEstado, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "criterios": [criterio.to_dict() for criterio in self.criterios],
        }


@dataclass(frozen=True)
class DimensionEstado:
    id: int
    codigo: str
    nombre: str
    indicadores: tuple[IndicadorEstado, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "indicadores": [indicador.to_dict() for indicador in self.indicadores],
        }


@dataclass(frozen=True)
class EstadoCicloPayload:
    ciclo_id: int
    dimensiones: tuple[DimensionEstado, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ciclo_id": self.ciclo_id,
            "dimensiones": [dimension.to_dict() for dimension in self.dimensiones],
        }


@dataclass(frozen=True)
class CompletitudPayload:
    ciclo_id: int
    criterios_sin_evidencia: tuple[Any, ...] = ()
    criterios_cuantitativos_sin_dato: tuple[Any, ...] = ()
    datos_sin_respaldo: tuple[Any, ...] = ()
    modelos_incompletos: tuple[Any, ...] = ()
    dimensiones_sin_valoracion: tuple[Any, ...] = ()
    debilidades_sin_accion: tuple[Any, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ciclo_id": self.ciclo_id,
            "criterios_sin_evidencia": list(self.criterios_sin_evidencia),
            "criterios_cuantitativos_sin_dato": list(
                self.criterios_cuantitativos_sin_dato
            ),
            "datos_sin_respaldo": list(self.datos_sin_respaldo),
            "modelos_incompletos": list(self.modelos_incompletos),
            "dimensiones_sin_valoracion": list(self.dimensiones_sin_valoracion),
            "debilidades_sin_accion": list(self.debilidades_sin_accion),
        }


@dataclass(frozen=True)
class ComparacionPayload:
    ciclo_a_id: int
    ciclo_b_id: int
    diferencias_modelos: tuple[dict[str, Any], ...] = ()
    diferencias_criterios: tuple[dict[str, Any], ...] = ()
    diferencias_acciones: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ciclo_a_id": self.ciclo_a_id,
            "ciclo_b_id": self.ciclo_b_id,
            "diferencias_modelos": list(self.diferencias_modelos),
            "diferencias_criterios": list(self.diferencias_criterios),
            "diferencias_acciones": list(self.diferencias_acciones),
        }
