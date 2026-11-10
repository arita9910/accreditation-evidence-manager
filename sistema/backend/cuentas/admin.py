from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .modelos import Usuario


class UsuarioCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ("username", "nombre", "apellidos", "email")


class UsuarioChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Usuario
        fields = "__all__"


@admin.register(Usuario)
class UsuarioAdmin(DjangoUserAdmin):
    add_form = UsuarioCreationForm
    form = UsuarioChangeForm
    list_display = ("username", "nombre", "apellidos", "email", "activo", "is_staff")
    list_filter = ("activo", "is_staff", "is_superuser", "groups")
    ordering = ("username",)
    search_fields = ("username", "nombre", "apellidos", "email")
    filter_horizontal = ("groups", "user_permissions")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Información personal", {"fields": ("nombre", "apellidos", "email")}),
        (
            "Permisos",
            {
                "fields": (
                    "activo",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Fechas importantes", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "nombre",
                    "apellidos",
                    "email",
                    "password1",
                    "password2",
                    "activo",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )
