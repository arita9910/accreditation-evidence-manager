class AtribucionUsuarioMixin:
    campos_autoria = ("creado_por", "modificado_por")

    def get_fields(self):
        fields = super().get_fields()
        for field_name in self.campos_autoria:
            if field_name in fields:
                fields[field_name].read_only = True
        return fields

    def save(self, **kwargs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            if self.instance is None:
                kwargs["creado_por"] = user
            kwargs["modificado_por"] = user
        return super().save(**kwargs)
