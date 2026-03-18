from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import Evaluation, Round, Submission, Team, TeamMember, Tournament, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    ordering = ('id',)
    list_display = ('id', 'email', 'nickname', 'role', 'is_staff')
    search_fields = ('email', 'nickname')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Profile', {'fields': ('nickname', 'role', 'profile_image')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nickname', 'password1', 'password2', 'role', 'is_staff', 'is_superuser'),
        }),
    )


admin.site.register(Tournament)
admin.site.register(Team)
admin.site.register(TeamMember)
admin.site.register(Round)
admin.site.register(Submission)
admin.site.register(Evaluation)
