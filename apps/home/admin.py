from django.contrib import admin

# Register your models here.
from .models import Project, TeamMember, Testimonial

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
    list_display = ('name', 'company', 'position', 'rating', 'is_active', 'order')
    list_filter = ('is_active', 'rating', 'created_at')
    search_fields = ('name', 'company', 'content')
    list_editable = ('order', 'is_active')
    fieldsets = (
        (None, {
            'fields': ('name', 'position', 'company', 'content', 'rating', 'image')
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
    )