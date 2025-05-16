from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group
from unfold.admin import ModelAdmin
from .models import CustomUser, OtpToken, Code, CompteBancaire, Transaction

# Unregister default Group admin to avoid conflicts
admin.site.unregister(Group)

# Custom Group admin
@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass

# Unregister default User admin to customize it
admin.site.register(User)

# Custom User admin
@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    pass

# Custom admin for CustomUser with personalized fields
class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = ("username", "email", "phone_number", "is_staff", "is_active")
    search_fields = ("email", "username", "phone_number")
    list_filter = ("is_staff", "is_superuser", "is_active", "mfa_enabled")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("username", "email", "phone_number", "password")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Multi-Factor Authentication", {"fields": ("mfa_secret", "mfa_enabled")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "phone_number", "password1", "password2"),
        }),
    )

# Admin for OtpToken
class OtpTokenAdmin(ModelAdmin):
    list_display = ("user", "otp_code", "otp_created_at", "otp_expires_at")
    search_fields = ("user__username", "user__email", "otp_code")
    list_filter = ("otp_created_at",)
    ordering = ("-otp_created_at",)

# Admin for Code
class CodeAdmin(ModelAdmin):
    list_display = ("user", "number")
    search_fields = ("user__username", "user__email", "number")
    list_filter = ("user",)

# Admin for CompteBancaire with custom actions
class CompteBancaireAdmin(ModelAdmin):
    list_display = ("nom", "prenom", "profession", "type_compte", "solde")
    search_fields = ("nom", "prenom", "profession", "type_compte")
    list_filter = ("type_compte",)
    ordering = ("nom", "prenom")
    actions = ["crediter_10", "debiter_10"]

    @admin.action(description="Créditer 10€ à chaque compte sélectionné")
    def crediter_10(self, request, queryset):
        for compte in queryset:
            compte.crediter(10)

    @admin.action(description="Débiter 10€ de chaque compte sélectionné")
    def debiter_10(self, request, queryset):
        for compte in queryset:
            compte.debiter(10)

# Admin for Transaction
class TransactionAdmin(ModelAdmin):
    list_display = ("compte", "montant", "type_transaction", "date")
    search_fields = ("compte__nom", "compte__prenom", "type_transaction")
    list_filter = ("type_transaction", "date")
    ordering = ("-date",)

# Register custom models in admin
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(OtpToken, OtpTokenAdmin)
admin.site.register(Code, CodeAdmin)
admin.site.register(CompteBancaire, CompteBancaireAdmin)
admin.site.register(Transaction, TransactionAdmin)
