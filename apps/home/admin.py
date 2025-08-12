from django.contrib import admin

# Register your models here.
from .models import Project, TeamMember, Testimonial, Program, Partner, Client

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'create_at')
    search_fields = ('name', 'position')
    readonly_fields = ('create_at',)
    fieldsets = (
        (None, {
            'fields': ('name', 'position', 'image', 'background_shape', 'bio')
        }),
        ('Additional Information', {
            'fields': ('linkedin', 'slug', 'create_at')
        }),
    )


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}


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
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


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