from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import (
    Evaluation, Round, Submission, Team, TeamMember, Tournament, 
    TournamentFile, User, JuryTournamentRegistration
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    ordering = ('id',)
    list_display = ('id', 'email', 'nickname', 'role', 'is_staff', 'assigned_tournaments')
    search_fields = ('email', 'nickname')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Profile', {'fields': ('nickname', 'role', 'profile_image')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Assigned Tournaments', {'fields': ('jury_tournaments',)}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nickname', 'password1', 'password2', 'role', 'is_staff', 'is_superuser'),
        }),
    )

    def assigned_tournaments(self, obj):
        """Display the tournaments assigned to the jury member."""
        tournaments = obj.jury_tournaments.all()
        if not tournaments:
            return '—'
        tournament_list = ', '.join([t.title for t in tournaments])
        return tournament_list
    assigned_tournaments.short_description = 'Assigned Tournaments'


admin.site.register(Team)
admin.site.register(TeamMember)
admin.site.register(Round)
admin.site.register(Submission)
admin.site.register(Evaluation)

admin.site.register(TournamentFile)


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'created_at', 'jury_approval_link')
    
    def jury_approval_link(self, obj):
        """Display link to jury approval page for this tournament."""
        url = reverse('admin:tournaments_jurytournamentregistration_changelist')
        return format_html(
            '<a class="button" href="{}?tournament__id__exact={}">👥 Manage Jury</a>',
            url,
            obj.id
        )
    jury_approval_link.short_description = 'Manage Jury'


@admin.register(JuryTournamentRegistration)
class JuryTournamentRegistrationAdmin(admin.ModelAdmin):
    model = JuryTournamentRegistration
    list_display = ('id', 'jury_email', 'tournament_title', 'status', 'created_at', 'reviewed_at')
    list_filter = ('status', 'created_at', 'tournament')
    search_fields = ('jury__email', 'jury__nickname', 'tournament__title')
    readonly_fields = ('jury', 'tournament', 'created_at', 'updated_at', 'reviewed_by', 'reviewed_at')
    fieldsets = (
        ('Request Information', {
            'fields': ('jury', 'tournament', 'status', 'created_at', 'updated_at')
        }),
        ('Review Information', {
            'fields': ('reviewed_by', 'reviewed_at')
        }),
    )
    actions = ['approve_jury', 'reject_jury']

    def jury_email(self, obj):
        """Display jury email."""
        return obj.jury.email
    jury_email.short_description = 'Jury Email'
    jury_email.admin_order_field = 'jury__email'

    def tournament_title(self, obj):
        """Display tournament title."""
        return obj.tournament.title
    tournament_title.short_description = 'Tournament'
    tournament_title.admin_order_field = 'tournament__title'

    def approve_jury(self, request, queryset):
        """Admin action to approve jury applications."""
        from .models import JuryRegistrationStatus
        
        # Filter only pending requests
        pending_requests = queryset.filter(status=JuryRegistrationStatus.PENDING)
        updated_count = 0
        
        for registration in pending_requests:
            registration.status = JuryRegistrationStatus.APPROVED
            registration.reviewed_by = request.user
            registration.reviewed_at = timezone.now()
            registration.save()
            
            # Add jury to the tournament's jury_members
            registration.jury.jury_tournaments.add(registration.tournament)
            updated_count += 1
        
        self.message_user(request, f'{updated_count} jury registration(s) approved successfully.')
    approve_jury.short_description = '✓ Approve selected jury registrations'

    def reject_jury(self, request, queryset):
        """Admin action to reject jury applications."""
        from .models import JuryRegistrationStatus
        
        # Filter only pending requests
        pending_requests = queryset.filter(status=JuryRegistrationStatus.PENDING)
        updated_count = 0
        
        for registration in pending_requests:
            registration.status = JuryRegistrationStatus.REJECTED
            registration.reviewed_by = request.user
            registration.reviewed_at = timezone.now()
            registration.save()
            updated_count += 1
        
        self.message_user(request, f'{updated_count} jury registration(s) rejected.')
    reject_jury.short_description = '✗ Reject selected jury registrations'
