"""Seed homepage content (stats, service pillars, article cards).

Idempotent: safe to run repeatedly — uses get_or_create / update_or_create and
only attaches a seed image when the article has none, so it never clobbers
content edited in the admin.

    python manage.py seed_homepage
"""
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from apps.home.models import HomeStat, ServicePillar, Project

SEED_DIR = Path(__file__).resolve().parent.parent.parent / "seed_data"

STATS = [
    ("120+", "Projects Delivered"),
    ("14", "Countries"),
    ("35+", "Institutional Partners"),
    ("8", "Focus Practices"),
]

PILLARS = [
    ("Insights & Data", "insights-data",
     "We uncover what is true, what matters, and what works.", "Diagnostic", "Synthesis"),
    ("Strategy & Design", "strategy-design",
     "We design systems, services, and pathways that enable meaningful progress.", "Systems", "Blueprint"),
    ("Implementation & Scale", "implementation-scale",
     "We turn strategy into action, adoption, and long-term capability.", "Enablement", "Toolkit"),
]

# slug, title, tags, challenge, headline_stat
ARTICLES = [
    ("national-digital-identity-framework", "National Digital Identity Framework", "Governance, AI",
     "Challenge: Fragmented citizen services across 12 ministries necessitating a unified architectural backbone.",
     "40% reduction in service delivery time"),
    ("ai-ethics-governance-toolkit", "AI Ethics & Governance Toolkit", "Sustainability, Ventures",
     "Challenge: No scalable venture pipeline in sustainability.",
     "18 ventures launched in 24 months"),
    ("e4impact-accelerator-program", "E4Impact Accelerator Program", "Sustainability, Ventures",
     "Challenge: No scalable venture pipeline in sustainability.",
     "18 ventures launched in 24 months"),
    ("sovereign-data-infrastructure", "Sovereign Data Infrastructure", "Sustainability, Ventures",
     "Challenge: No scalable venture pipeline in sustainability.",
     "18 ventures launched in 24 months"),
    ("the-mombasa-county-plastics-prize", "The Mombasa County Plastics Prize", "Climate & Circular Economy",
     "Challenge: Unregulated AI deployment in public health.",
     "Adopted by 6 national health authorities"),
    ("community-public-service-redesign", "Community Public-Service Redesign", "Governance, Public Service",
     "Challenge: Service delivery bottlenecks across rural health posts.",
     "2.1M citizens reached in year one"),
]


class Command(BaseCommand):
    help = "Seed homepage content: stats, service pillars, and article cards."

    def handle(self, *args, **options):
        self._seed_stats()
        self._seed_pillars()
        self._seed_articles()
        self.stdout.write(self.style.SUCCESS("Homepage seed complete."))

    def _seed_stats(self):
        for i, (value, label) in enumerate(STATS):
            HomeStat.objects.update_or_create(
                value=value, defaults={"label": label, "order": i, "is_active": True})
        self.stdout.write(f"  stats: {HomeStat.objects.count()}")

    def _seed_pillars(self):
        for i, (title, slug, desc, type_label, output_label) in enumerate(PILLARS):
            ServicePillar.objects.update_or_create(slug=slug, defaults={
                "title": title, "description": desc, "type_label": type_label,
                "output_label": output_label, "order": i, "is_active": True})
        self.stdout.write(f"  pillars: {ServicePillar.objects.count()}")

    def _seed_articles(self):
        for i, (slug, title, tags, challenge, stat) in enumerate(ARTICLES):
            obj, _ = Project.objects.get_or_create(slug=slug, defaults={"title": title, "content": title})
            obj.title = title
            obj.tags = tags
            obj.challenge = challenge
            obj.headline_stat = stat
            obj.is_active = True
            obj.is_featured = True
            obj.order = i
            img = SEED_DIR / "articles" / f"{slug}.webp"
            if img.exists() and not obj.thumbnail:
                with img.open("rb") as fh:
                    obj.thumbnail.save(f"{slug}.webp", File(fh), save=False)
            obj.save()
        self.stdout.write(f"  articles: {Project.objects.filter(is_featured=True).count()}")
