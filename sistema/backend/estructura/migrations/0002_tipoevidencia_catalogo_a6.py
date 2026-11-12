from django.db import migrations, models


def poblar_tipos_evidencia_a6(apps, schema_editor):
    VersionNormativa = apps.get_model("estructura", "VersionNormativa")
    Dimension = apps.get_model("estructura", "Dimension")
    TipoEvidencia = apps.get_model("estructura", "TipoEvidencia")

    version_activa = (
        VersionNormativa.objects.filter(activa=True)
        .order_by("-fecha_aprobacion", "-pk")
        .first()
    )
    if version_activa is None:
        return

    dimensiones = {
        dimension.codigo: dimension
        for dimension in Dimension.objects.filter(version=version_activa)
    }
    dimension_por_defecto = next(iter(dimensiones.values()), None)
    if dimension_por_defecto is None:
        return

    catalogo = [
        {
            "dimension_codigo": "1",
            "nombre": "Estrategia de la carrera",
            "soporte_exigido": "digital",
            "descripcion": "Documento rector de planificación y mejora de la carrera.",
        },
        {
            "dimension_codigo": "1",
            "nombre": "Acta de reuniones",
            "soporte_exigido": "papel_firmado",
            "descripcion": "Actas firmadas de reuniones de colectivos y órganos de dirección.",
        },
        {
            "dimension_codigo": "3",
            "nombre": "CV de profesores",
            "soporte_exigido": "digital",
            "descripcion": "Currículos del claustro vinculados a la evaluación del ciclo.",
        },
        {
            "dimension_codigo": "2",
            "nombre": "Trabajo de diploma",
            "soporte_exigido": "ambos",
            "descripcion": "Expediente y producto final del trabajo de diploma del estudiante.",
        },
        {
            "dimension_codigo": "2",
            "nombre": "Plan de Proceso Docente",
            "soporte_exigido": "digital",
            "descripcion": "Planificación docente aprobada para asignaturas y periodos académicos.",
        },
        {
            "dimension_codigo": "6",
            "nombre": "Avales",
            "soporte_exigido": "papel_firmado",
            "descripcion": "Avales institucionales o externos con firma oficial.",
        },
    ]

    for item in catalogo:
        dimension = dimensiones.get(item["dimension_codigo"], dimension_por_defecto)
        TipoEvidencia.objects.update_or_create(
            dimension=dimension,
            nombre=item["nombre"],
            defaults={
                "naturaleza": "documento",
                "soporte_exigido": item["soporte_exigido"],
                "descripcion": item["descripcion"],
            },
        )


def revertir_tipos_evidencia_a6(apps, schema_editor):
    TipoEvidencia = apps.get_model("estructura", "TipoEvidencia")
    nombres = [
        "Estrategia de la carrera",
        "Acta de reuniones",
        "CV de profesores",
        "Trabajo de diploma",
        "Plan de Proceso Docente",
        "Avales",
    ]
    TipoEvidencia.objects.filter(nombre__in=nombres).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("estructura", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="tipoevidencia",
            name="descripcion",
            field=models.TextField(blank=True, verbose_name="descripción"),
        ),
        migrations.RunPython(
            poblar_tipos_evidencia_a6,
            reverse_code=revertir_tipos_evidencia_a6,
        ),
    ]
