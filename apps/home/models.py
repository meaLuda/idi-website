from django.db import models
from django.utils.text import slugify
from ckeditor_uploader.fields import RichTextUploadingField

class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    image = models.ImageField(upload_to='uploads/team/')
    background_shape = models.ImageField(upload_to='uploads/team/shapes/', blank=True, null=True)
    bio = RichTextUploadingField('bio', config_name='extends')  
    linkedin = models.URLField(blank=True)
    slug = models.SlugField(unique=True, blank=True)
    create_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def background_shape_url(self):
        if self.background_shape:
            return self.background_shape.url
        return None

    def get_absolute_url(self):
        return f'uploads//team/{self.slug}/'
    
    def __str__(self):
        return self.name
    
    
class Project(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    thumbnail = models.ImageField(upload_to='uploads/projects/thumbnails/', help_text="Main image shown in grid")
    content = RichTextUploadingField('Content', config_name='extends')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)  # Add this if you want to maintain order

    class Meta:
        ordering = ['-created_at']  # Changed to only use created_at for ordering

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return f'uploads/projects/{self.slug}/'

    def __str__(self):
        return self.title


# New Testimonial Model
class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    content = models.TextField()
    image = models.ImageField(upload_to='uploads/testimonials/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'

    def __str__(self):
        return f"{self.name} - {self.company}"