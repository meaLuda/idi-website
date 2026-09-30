from django.contrib import admin

# Register your models here.
from .models import CaseStudy, CaseStudyStat, ContactMessage, Project, TeamMember, Testimonial, Program, Partner, Client, HomeStat, ServicePillar

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    # `order` first and list-editable so positions can be set for the whole team
    # on one screen, rather than opening each member in turn.
    list_display = ('order', 'name', 'position', 'updated_at')
    list_editable = ('order',)
    list_display_links = ('name',)
    ordering = ('order', 'name')
    search_fields = ('name', 'position')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'position', 'order', 'image', 'background_shape', 'bio')
        }),
        ('Additional Information', {
            'fields': ('linkedin', 'slug', 'created_at', 'updated_at')
        }),
    )


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'tags', 'is_featured', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'is_featured', 'created_at')
    search_fields = ('title', 'content', 'tags')
    list_editable = ('is_featured', 'is_active', 'order')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'thumbnail', 'content')
        }),
        ('Article Card', {
            'fields': ('tags', 'challenge', 'headline_stat'),
            'description': "Shown on the homepage article cards.",
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'is_active', 'order')
        }),
    )


@admin.register(HomeStat)
class HomeStatAdmin(admin.ModelAdmin):
    list_display = ('value', 'label', 'order', 'is_active')
    list_editable = ('label', 'order', 'is_active')


@admin.register(ServicePillar)
class ServicePillarAdmin(admin.ModelAdmin):
    list_display = ('title', 'type_label', 'output_label', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'cta_url'),
            'description': "Illustration is a static asset at static/images/home/services/{slug}.webp",
        }),
        ('Card pill', {'fields': ('type_label', 'output_label')}),
        ('Display', {'fields': ('order', 'is_active')}),
    )


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'position', 'is_active', 'order')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'company', 'content')
    list_editable = ('order', 'is_active')
    fieldsets = (
        (None, {
            'fields': ('name', 'position', 'company', 'content', 'image')
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
    )
    
    
@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'program_type', 'year', 'is_active', 'is_featured', 'application_open', 'order')
    list_filter = ('program_type', 'year', 'is_active', 'is_featured', 'application_open', 'created_at')
    search_fields = ('title', 'short_description', 'target_audience')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('order', 'is_active', 'is_featured', 'application_open')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'program_type', 'year', 'image')
        }),
        ('Content', {
            'fields': ('short_description', 'full_description', 'target_audience')
        }),
        ('Program Details', {
            'fields': ('duration', 'format', 'application_deadline')
        }),
        ('Links & Resources', {
            'fields': ('application_url', 'learn_more_url', 'brochure')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'is_featured', 'application_open', 'order')
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
    )
    


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'partnership_type', 'is_active', 'is_featured', 'order')
    list_filter = ('partnership_type', 'is_active', 'is_featured', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('order', 'is_active', 'is_featured')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'logo', 'website', 'partnership_type')
        }),
        ('Content', {
            'fields': ('description',)
        }),
        ('Display Settings', {
            'fields': ('is_active', 'is_featured', 'order')
        }),
    )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'collaboration_year', 'is_active', 'is_featured', 'order')
    list_filter = ('industry', 'collaboration_year', 'is_active', 'is_featured', 'created_at')
    search_fields = ('name', 'project_description')
    list_editable = ('order', 'is_active', 'is_featured')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'logo', 'website', 'industry', 'collaboration_year')
        }),
        ('Project Details', {
            'fields': ('project_description',)
        }),
        ('Display Settings', {
            'fields': ('is_active', 'is_featured', 'order')
        }),
    )


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Enquiries submitted through the contact form.

    Read-mostly: the visitor's words are a record and should not be edited. Only
    the handling fields are writable.
    """

    list_display = ('created_at', 'name', 'organization', 'inquiry_type',
                    'email', 'is_handled', 'notification_sent')
    list_filter = ('is_handled', 'inquiry_type', 'notification_sent', 'created_at')
    search_fields = ('name', 'email', 'organization', 'message')
    date_hierarchy = 'created_at'
    readonly_fields = ('name', 'organization', 'email', 'inquiry_type', 'message',
                       'notification_sent', 'created_at')
    fieldsets = (
        ('Enquiry', {'fields': ('created_at', 'name', 'organization', 'email',
                                'inquiry_type', 'message')}),
        ('Handling', {'fields': ('is_handled', 'handled_note', 'notification_sent')}),
    )

    def has_add_permission(self, request):
        return False


class CaseStudyStatInline(admin.TabularInline):
    """Statistics edited alongside the case study itself."""

    model = CaseStudyStat
    extra = 3
    fields = ('order', 'value', 'label', 'kind', 'note')
    ordering = ('order', 'id')


@admin.register(CaseStudy)
class CaseStudyAdmin(admin.ModelAdmin):
    """Case studies.

    Until now only the three Project-backed studies were editable; the rest were
    Python dictionaries in views.py, so changing a word meant a code deploy.
    """

    list_display = ('order', 'title', 'category', 'partners_text',
                    'stat_summary', 'is_published')
    list_display_links = ('title',)
    list_editable = ('order', 'is_published')
    list_filter = ('is_published', 'category')
    search_fields = ('title', 'slug', 'teaser', 'overview', 'partners_text')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('order', 'title')
    inlines = [CaseStudyStatInline]
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Card (what people see in the listing)', {
            'fields': ('title', 'slug', 'category', 'partners_text', 'teaser',
                       'challenge', 'hero_image', 'bg_color'),
            'description': 'The teaser and the statistics below are what appear '
                           'on the case-studies listing.',
        }),
        ('Detail page', {
            'fields': ('subtitle', 'sector', 'client', 'timeline', 'tags',
                       'overview', 'our_role', 'key_insight', 'approach_text',
                       'outcome_text', 'measuring_success'),
        }),
        ('Publishing', {'fields': ('is_published', 'order', 'created_at', 'updated_at')}),
        ('Legacy imagery', {
            'classes': ('collapse',),
            'fields': ('hero_image_static',),
            'description': 'Static path kept from the imported content. Upload a '
                           'hero image above to replace it.',
        }),
    )

    @admin.display(description='Stats')
    def stat_summary(self, obj):
        outcomes = obj.stats.filter(kind=CaseStudyStat.Kind.OUTCOME).count()
        context = obj.stats.filter(kind=CaseStudyStat.Kind.CONTEXT).count()
        if not outcomes and not context:
            return '—'
        parts = [f'{outcomes} outcome'] if outcomes else []
        if context:
            parts.append(f'{context} context')
        return ', '.join(parts)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('stats')

