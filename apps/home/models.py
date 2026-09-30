import io
import os

from django.core.files.base import ContentFile
from django.db import models
from django.utils.text import slugify
from ckeditor_uploader.fields import RichTextUploadingField


def downscale_image_field(image_field, max_edge=1280, quality=82):
    """Downscale a freshly-uploaded ImageField in place so the longest edge is at most
    `max_edge` px. Caps oversized CMS uploads (e.g. 2560px) that would otherwise be served
    at full resolution into small cards. Only runs on not-yet-committed files so re-saving
    an unchanged model doesn't re-download/re-process the stored image.
    """
    if not image_field:
        return
    # `_committed` is False only when a new file has been assigned but not yet saved.
    if getattr(image_field, '_committed', True):
        return

    try:
        from PIL import Image
    except ImportError:
        return

    try:
        image_field.open()
        img = Image.open(image_field)
        img.load()
    except Exception:
        return

    if max(img.size) <= max_edge:
        return

    fmt = (img.format or '').upper()
    ext = os.path.splitext(image_field.name)[1].lower()
    if fmt not in {'JPEG', 'PNG', 'WEBP'}:
        fmt = 'WEBP' if ext == '.webp' else 'JPEG'

    if fmt == 'JPEG' and img.mode not in ('RGB', 'L'):
        img = img.convert('RGB')

    img.thumbnail((max_edge, max_edge), Image.LANCZOS)

    buffer = io.BytesIO()
    save_kwargs = {'format': fmt}
    if fmt in {'JPEG', 'WEBP'}:
        save_kwargs['quality'] = quality
        save_kwargs['optimize'] = True
    img.save(buffer, **save_kwargs)

    # Replace the field's content without committing yet — the subsequent super().save()
    # persists it. save=False avoids triggering an extra model save.
    image_field.save(os.path.basename(image_field.name), ContentFile(buffer.getvalue()), save=False)

class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    image = models.ImageField(upload_to='uploads/team/')
    background_shape = models.ImageField(upload_to='uploads/team/shapes/', blank=True, null=True)
    bio = RichTextUploadingField('bio', config_name='extends')  
    linkedin = models.URLField(blank=True)
    slug = models.SlugField(unique=True, blank=True)
    # Renamed from `create_at`: the field is auto_now, so despite the old name it
    # always recorded the last modification, not creation. The sitemap used it as
    # <lastmod>, which meant an unrelated edit looked like a content change.
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    # Display position, matching the convention used by Project, ServicePillar,
    # HomeStat, Partner and Client. TeamMember was the only content model without
    # one, so the team page was stuck in alphabetical order with no way to put
    # leadership first. Lower numbers appear first; ties fall back to name.
    order = models.PositiveSmallIntegerField(
        default=0,
        help_text='Lower numbers appear first. Equal numbers sort alphabetically.',
    )

    class Meta:
        # An explicit ordering also matters because `TeamMember.objects.all()[:6]`
        # would otherwise be a LIMIT with no ORDER BY, which returns an arbitrary
        # six rows on PostgreSQL, and the sitemap paginates an unordered queryset.
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        downscale_image_field(self.image)
        super().save(*args, **kwargs)

    @property
    def background_shape_url(self):
        if self.background_shape:
            return self.background_shape.url
        return None

    def get_absolute_url(self):
        """Return the URL for this team member"""
        from django.urls import reverse
        return reverse('home:team_member_detail', kwargs={'slug': self.slug})
    
    def __str__(self):
        return self.name
    
    
class Project(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    thumbnail = models.ImageField(upload_to='uploads/projects/thumbnails/', help_text="Main image shown in grid")
    content = RichTextUploadingField('Content', config_name='extends')
    # Homepage article-card fields
    tags = models.CharField(max_length=120, blank=True,
                            help_text="Comma-separated topic tags shown as pills, e.g. 'Governance, AI'")
    challenge = models.CharField(max_length=240, blank=True,
                                 help_text="One-line challenge summary shown on the card")
    headline_stat = models.CharField(max_length=120, blank=True,
                                     help_text="Highlighted outcome stat, e.g. '40% reduction in service delivery time'")
    is_featured = models.BooleanField(default=False, help_text="Show in the homepage hero card row")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)  # Add this if you want to maintain order

    class Meta:
        ordering = ['-created_at']  # Changed to only use created_at for ordering

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        downscale_image_field(self.thumbnail)
        super().save(*args, **kwargs)

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('home:project_detail', kwargs={'slug': self.slug})

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
    
class Program(models.Model):
    PROGRAM_TYPES = [
        ('fellowship', 'Fellowship'),
        ('executive', 'Executive Program'),
        ('bootcamp', 'Bootcamp'),
        ('course', 'Course'),
        ('workshop', 'Workshop'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    program_type = models.CharField(max_length=20, choices=PROGRAM_TYPES, default='fellowship')
    short_description = models.TextField(help_text="Brief description for card display")
    full_description = RichTextUploadingField('Full Description', config_name='extends', blank=True)
    image = models.ImageField(upload_to='uploads/programs/', help_text="Program card image")
    
    # Program Details
    duration = models.CharField(max_length=100, blank=True, help_text="e.g., '12 weeks', '3 months'")
    format = models.CharField(max_length=100, blank=True, help_text="e.g., 'Online', 'Hybrid', 'In-person'")
    target_audience = models.TextField(blank=True, help_text="Who this program is for")
    
    # Application & Links
    application_url = models.URLField(blank=True, help_text="Apply Now link")
    learn_more_url = models.URLField(blank=True, help_text="Learn More link")
    brochure = models.FileField(upload_to='uploads/programs/brochures/', blank=True, null=True)
    
    # Status & Display
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Show in featured programs section")
    application_open = models.BooleanField(default=True)
    application_deadline = models.DateTimeField(blank=True, null=True)
    
    # Program Year
    year = models.IntegerField(default=2025)
    
    # SEO & Meta
    meta_description = models.TextField(blank=True, max_length=160)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order = models.IntegerField(default=0, help_text="Display order")

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Program'
        verbose_name_plural = 'Programs'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        downscale_image_field(self.image)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('home:program_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return f"{self.title} ({self.year})"


class ServicePillar(models.Model):
    """A 'WHAT WE DO' pillar. Illustration is a static brand asset resolved by slug
    at static/images/home/services/{slug}.webp; copy fields are CMS-editable."""
    title = models.CharField(max_length=80, help_text="e.g. 'Insights & Data'")
    slug = models.SlugField(unique=True, blank=True,
                            help_text="Drives the illustration filename: services/{slug}.webp")
    description = models.CharField(max_length=200)
    type_label = models.CharField(max_length=40, blank=True, help_text="e.g. 'Diagnostic'")
    output_label = models.CharField(max_length=40, blank=True, help_text="e.g. 'Synthesis'")
    cta_url = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Service Pillar'
        verbose_name_plural = 'Service Pillars'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class HomeStat(models.Model):
    """A single metric in the homepage stats strip (e.g. '120+' / 'Projects Delivered')."""
    value = models.CharField(max_length=16, help_text="e.g. '120+', '14', '35+'")
    label = models.CharField(max_length=80, help_text="e.g. 'Projects Delivered'")
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Home Stat'
        verbose_name_plural = 'Home Stats'

    def __str__(self):
        return f"{self.value} {self.label}"


class Partner(models.Model):
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='uploads/partners/')
    website = models.URLField(blank=True, help_text="Partner's website URL")
    description = models.TextField(blank=True, help_text="Brief description of the partnership")
    partnership_type = models.CharField(
        max_length=50,
        choices=[
            ('strategic', 'Strategic Partner'),
            ('technology', 'Technology Partner'),
            ('funding', 'Funding Partner'),
            ('academic', 'Academic Partner'),
            ('implementation', 'Implementation Partner'),
            ('media', 'Media Partner'),
        ],
        default='strategic'
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Show in featured partners section")
    order = models.IntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Partner'
        verbose_name_plural = 'Partners'

    def save(self, *args, **kwargs):
        downscale_image_field(self.logo, max_edge=600)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Client(models.Model):
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='uploads/clients/')
    website = models.URLField(blank=True, help_text="Client's website URL")
    industry = models.CharField(
        max_length=100,
        choices=[
            ('fintech', 'FinTech'),
            ('healthcare', 'Healthcare'),
            ('education', 'Education'),
            ('agriculture', 'Agriculture'),
            ('logistics', 'Logistics'),
            ('manufacturing', 'Manufacturing'),
            ('retail', 'Retail'),
            ('government', 'Government'),
            ('ngo', 'NGO/Non-Profit'),
            ('other', 'Other'),
        ],
        default='other'
    )
    project_description = models.TextField(blank=True, help_text="Brief description of the project/engagement")
    collaboration_year = models.IntegerField(default=2025, help_text="Year of collaboration")
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Show in featured clients section")
    order = models.IntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __str__(self):
        return self.name


class ContactMessage(models.Model):
    """An enquiry submitted through the contact form.

    Added because the contact view previously discarded every submission: its POST
    branch set ``success = True`` and returned, so visitors saw "Message Sent!"
    while the enquiry went nowhere. Real business enquiries were lost.
    """

    INQUIRY_TYPES = [
        ('strategic-partnership', 'Strategic Partnership'),
        ('academy-fellowship', 'DID Academy / Fellowship'),
        ('research-data', 'Insights & Data Collaborations'),
        ('careers', 'Career Opportunities'),
        ('general', 'General Inquiry'),
    ]

    name = models.CharField(max_length=120)
    organization = models.CharField(max_length=160, blank=True)
    email = models.EmailField()
    inquiry_type = models.CharField(max_length=32, choices=INQUIRY_TYPES, default='general')
    message = models.TextField()

    is_handled = models.BooleanField(default=False, help_text='Tick once someone has replied.')
    handled_note = models.TextField(blank=True)

    # Delivery is best-effort: a failed send must never lose the enquiry, since
    # the database row is the durable record.
    notification_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact message'
        verbose_name_plural = 'Contact messages'
        indexes = [
            models.Index(fields=['is_handled', '-created_at'], name='contact_handled_idx'),
        ]

    def __str__(self):
        return f'{self.name} <{self.email}> - {self.get_inquiry_type_display()}'


class NewsletterSubscriber(models.Model):
    """An email address collected by the newsletter forms.

    The two newsletter forms (on /projects/ and /case-studies/) previously had no
    action and no handler: their submit listeners called preventDefault() and then
    showed a success message or an alert(). Every address entered was discarded
    while the visitor was told they had subscribed.
    """

    email = models.EmailField(unique=True)
    source = models.CharField(
        max_length=40, blank=True,
        help_text='Which page the subscription came from.',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Newsletter subscriber'
        verbose_name_plural = 'Newsletter subscribers'

    def __str__(self):
        return self.email



class CaseStudy(models.Model):
    """A case study, editable in the admin.

    These previously lived as Python dictionaries in apps/home/views.py
    (CASE_STUDIES and CASE_STUDY_DETAIL_DATA), which meant the only case studies
    anyone could edit were the three backed by the Project model. Everything else
    required a code change and a deploy to correct a typo.

    Field names deliberately mirror the keys the existing templates already read,
    so the templates needed almost no change.
    """

    slug = models.SlugField(unique=True, max_length=120)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(
        max_length=250, blank=True,
        help_text='Short line under the title on the detail page.',
    )
    teaser = models.TextField(
        blank=True,
        help_text='Short description for the listing card. 1-2 sentences.',
    )
    category = models.CharField(
        max_length=80, blank=True,
        help_text="Shown as the card label, e.g. 'GENDER RIGHTS'.",
    )
    sector = models.CharField(max_length=80, blank=True)
    client = models.CharField(max_length=200, blank=True)
    partners_text = models.CharField(
        max_length=250, blank=True,
        help_text="Partner names for the card, e.g. 'UNEP · GIZ · Action Lab'.",
    )
    timeline = models.CharField(max_length=100, blank=True, help_text="e.g. '2023 - 2024'")

    challenge = models.CharField(
        max_length=300, blank=True,
        help_text='One-line problem summary shown on the card.',
    )
    overview = models.TextField(blank=True)
    our_role = models.TextField(blank=True)
    key_insight = models.TextField(blank=True)
    approach_text = models.TextField(blank=True)
    outcome_text = models.TextField(blank=True)
    measuring_success = models.TextField(blank=True)

    hero_image = models.ImageField(upload_to='uploads/case_studies/', blank=True, null=True)
    hero_image_static = models.CharField(
        max_length=200, blank=True,
        help_text='Path under static/ for legacy imported imagery. Ignored if an image is uploaded.',
    )

    tags = models.CharField(
        max_length=200, blank=True,
        help_text="Comma-separated, e.g. 'Health, Digitisation, Youth'",
    )
    bg_color = models.CharField(
        max_length=40, blank=True,
        help_text="Tailwind class for the card background, e.g. 'bg-[#f5f1ea]'",
    )

    is_published = models.BooleanField(
        default=True,
        help_text='Untick to hide from the site without deleting it.',
    )
    order = models.PositiveSmallIntegerField(
        default=0, help_text='Lower numbers appear first.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Case study'
        verbose_name_plural = 'Case studies'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        downscale_image_field(self.hero_image, max_edge=1600)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('home:case_study_detail', kwargs={'slug': self.slug})

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    @property
    def hero(self):
        """Uploaded image if present, else the legacy static path."""
        if self.hero_image:
            return self.hero_image.url
        return None

    @property
    def headline_stats(self):
        """Measured outcomes only — the numbers safe to lead with."""
        return self.stats.filter(kind=CaseStudyStat.Kind.OUTCOME)


class CaseStudyStat(models.Model):
    """A single figure shown on a case study.

    `kind` exists because not every number on a case study is something IDI
    achieved. Prevalence figures describe the problem being addressed, and
    presenting them as results would overclaim. Only OUTCOME stats are used as
    headline figures.
    """

    class Kind(models.TextChoices):
        OUTCOME = 'outcome', 'Outcome (something we achieved)'
        CONTEXT = 'context', 'Context (describes the problem, not our result)'

    case_study = models.ForeignKey(
        CaseStudy, on_delete=models.CASCADE, related_name='stats',
    )
    value = models.CharField(max_length=40, help_text="e.g. '91%', '5', '<15 min'")
    label = models.CharField(max_length=160, help_text="e.g. 'faster case research'")
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.OUTCOME)
    note = models.CharField(
        max_length=200, blank=True,
        help_text='Optional qualifier shown with the figure, e.g. the source or scope.',
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Statistic'
        verbose_name_plural = 'Statistics'

    def __str__(self):
        return f'{self.value} {self.label}'
