from django.db import migrations


def _asignar_soporte(nombre):
    texto = nombre.lower()
    palabras_papel = (
        "acta",
        "actas",
        "avales",
        "certificacion",
        "constancia",
        "documento oficial",
        "documentos oficiales",
        "documentos que avalan",
        "documentos de los departamentos",
        "nombramiento",
        "oficial",
        "secretaria docente",
        "trabajos de curso",
    )
    if any(palabra in texto for palabra in palabras_papel):
        return "papel_firmado"
    return "digital"


def poblar_tipos_evidencia_manual(apps, schema_editor):
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

    catalogo = [
        ("1", "Estrategia de la carrera, de los años y las brigadas"),
        ("1", "Informe de cumplimiento de la estrategia educativa"),
        ("1", "Evaluación de los profesores y del personal de apoyo a la docencia en los últimos dos años"),
        ("1", "Acta de reuniones de coordinación de años"),
        ("1", "Documentos que avalan la cantidad y relevancia de los proyectos comunitarios y extensionistas"),
        ("1", "Certificaciones, reconocimientos u otros recibidos"),
        ("1", "Documentación de los proyectos de investigación donde participan los profesores y estudiantes, tareas que cumplen cada uno"),
        ("1", "Proyectos de curso y tesis de graduado"),
        ("1", "Currículo vitae (CV) de profesores"),
        ("1", "Documentación de los convenios de colaboración interinstitucional"),
        ("1", "Documentos de las modalidades de estudio que se demandan por los territorios y que oferta y se ejecutan por la carrera (CUM, CPE A Distancia)"),
        ("1", "Constancia de los cursos de superación o programas académicos de posgrado que se gestionan o imparten"),
        ("1", "Constancia de la categoría de acreditación de los programas académicos en el área del conocimiento de tenerla"),
        ("2", "Evaluaciones de los profesores"),
        ("2", "Documentos oficiales en Recursos Humanos de los profesores"),
        ("2", "Documentos de los Departamentos de los profesores y actas de examen en Secretaria Docente"),
        ("2", "Currículo vitae (CV) de profesores"),
        ("2", "Documento oficial de la estrategia de formación doctoral, consolidación del claustro y cultura de la profesión y su seguimiento. Informe o registro del cumplimiento de las tareas diseñadas en las estrategias anteriores"),
        ("2", "Evaluación de alumnos ayudantes"),
        ("2", "Documentos de los proyectos de investigación"),
        ("2", "Certificación de participación en evento territorial, nacional e internacional"),
        ("2", "Constancia de los reconocimientos académicos, científicos y sociales relevantes en los últimos cinco años"),
        ("3", "Trabajos de curso y diploma relacionados con las tareas de impacto y comunitarias"),
        ("3", "Resultados académicos en la Secretaría docente"),
        ("3", "Resultados de los exámenes integradores aplicados a una muestra de estudiantes de al menos los últimos dos años en el proceso"),
        ("3", "Trabajo de curso y diploma u otra forma de culminación de estudios en los últimos tres años"),
        ("3", "Relación de los alumnos ayudantes y su evaluación por años en el quinquenio"),
        ("3", "Relación de estudiantes que asisten a exámenes de premio y a subir notas"),
        ("3", "Relación de estudiantes que participan en actividades de orientación profesional, la Jornada científica y eventos"),
        ("3", "Constancia del vínculo de estudiantes con el desarrollo local, social, cultural y sectores estratégicos, mediante práctica laborales, trabajos de curso y diplomas"),
        ("4", "Evidencias de la actualización y calidad de la bibliografía básica y complementaria para los diferentes cursos y en otros idiomas"),
        ("4", "Constancia del uso de los medios y recursos tecnológicos disponibles (plataformas y repositorio digital)"),
        ("4", "Presencia de medios tecnológicos que aseguran la formación"),
        ("4", "Traza del uso de los medios"),
        ("4", "Documentos que avalan el convenio con las unidades docente, entidades laborales de base y en sectores estratégicos"),
        ("4", "Presencia e inscripción de modalidad de la carrera en plataformas de teleformación y el Centro Nacional de Educación a Distancia"),
        ("5", "Plan del Proceso Docente de todas las modalidades de estudio"),
        ("5", "Actas de reuniones de disciplinas departamentos y comisión de carrera"),
        ("5", "Nombramiento oficial de los profesores principales de colectivo de años"),
        ("5", "Evaluación de los profesores"),
        ("5", "Documentos que avalan el trabajo metodológico de los colectivos pedagógicos, planes de trabajo metodológico de años y disciplinas"),
        ("5", "Actas de colectivos de carrera"),
        ("5", "Muestra de ejercicios integradores de los últimos tres años"),
        ("5", "Resultado de ejercicios integrador (ortografía, redacción e idioma inglés)"),
        ("6", "Documento que refleja las acciones y métodos utilizados para evaluar el impacto de sus resultados en las tres dimensiones"),
        ("6", "Planes de mejora donde se reflejan los resultados de las evaluaciones del impacto de manera sistemática"),
        ("6", "Avales de Consejos científicos o de la instancia correspondiente para la introducción de los resultados en el proceso de formación"),
        ("6", "Avales de las entidades correspondientes que dan fe de la introducción de los resultados de proyectos de investigación"),
        ("6", "Constancia de los premios obtenidos por los profesores del claustro y estudiantes de la carrera"),
        ("6", "Documento que avala la participación de los profesores en actividades interuniversitarias nacional e internacional"),
    ]

    TipoEvidencia.objects.all().delete()

    for dimension_codigo, nombre in catalogo:
        dimension = dimensiones.get(dimension_codigo)
        if dimension is None:
            continue
        TipoEvidencia.objects.create(
            dimension=dimension,
            nombre=nombre,
            descripcion=nombre,
            naturaleza="documento",
            soporte_exigido=_asignar_soporte(nombre),
        )


def revertir_tipos_evidencia_manual(apps, schema_editor):
    TipoEvidencia = apps.get_model("estructura", "TipoEvidencia")
    TipoEvidencia.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("estructura", "0002_tipoevidencia_catalogo_a6"),
    ]

    operations = [
        migrations.RunPython(
            poblar_tipos_evidencia_manual,
            reverse_code=revertir_tipos_evidencia_manual,
        )
    ]
