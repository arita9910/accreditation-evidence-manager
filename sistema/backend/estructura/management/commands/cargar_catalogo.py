from django.core.management.base import BaseCommand, CommandError

from estructura.servicios import ErrorCatalogo, cargar_catalogo


class Command(BaseCommand):
    help = "Valida y carga el catálogo normativo SEA-CU de forma repetible."

    def add_arguments(self, parser):
        parser.add_argument("--catalogo", help="Ruta al JSON del catálogo.")
        parser.add_argument("--modelos", help="Ruta al JSON de resumen de modelos.")

    def handle(self, *args, **options):
        try:
            resultado = cargar_catalogo(
                ruta=options["catalogo"],
                ruta_modelos=options["modelos"],
            )
        except ErrorCatalogo as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            self.style.SUCCESS(
                "Catálogo cargado: "
                f"{resultado['dimensiones']}/{resultado['indicadores']}/"
                f"{resultado['criterios']} dimensiones/indicadores/criterios; "
                f"{resultado['modelos']} modelos y "
                f"{resultado['asociaciones']} asociaciones."
            )
        )
