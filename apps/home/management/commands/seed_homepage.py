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
    ("power-to-youth", "Power to Youth", "Gender Rights, Youth",
     "Challenge: Harmful traditions like FGM are practiced by 84% of the Kuria community in Migori County, Kenya.",
     "84% FGM prevalence rate"),
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

POWER_TO_YOUTH_CONTENT = """<h2 class="text-2xl font-bold mb-4">Reimagining Tradition: How Men and Boys Are Driving Change in Migori County</h2>

<p class="mb-4">In Migori’s Kuria community, a new approach is challenging harmful traditions by engaging men and boys as allies for women’s rights.</p>

<h3 class="text-xl font-bold mt-6 mb-3">A New Question</h3>
<p class="mb-4">Among the Kuria people of Migori County, Kenya, female genital mutilation (FGM) is a deeply rooted tradition, practiced by 84% of the community. It marks a girl’s transition into womanhood and often leads to early marriage.</p>
<p class="mb-4">For generations, efforts to protect girls focused mainly on women. We asked a different question:</p>
<blockquote class="border-l-4 border-[#006377] pl-4 italic my-6 text-lg text-gray-700">
    Could men and boys — the cultural gatekeepers — be part of the solution?
</blockquote>

<h3 class="text-xl font-bold mt-6 mb-3">Listening Before Leading</h3>
<p class="mb-4">Our journey began with introspection. We trained our team in human-centered design, grounding our work in empathy and collaboration. In early engagements with religious leaders, community elders, young women, and men, one message stood out: Many men and boys had never questioned the consequences of practices like FGM.</p>
<p class="mb-4">Through three weeks of immersive field research, we spoke with 40 community members across generations. We didn’t just gather statistics — we listened to stories.</p>
<p class="mb-4">One young man shared,<br>
<span class="italic text-gray-600">“I never thought FGM was harmful; it was just what we did. Now I see how it affects my sisters and their futures.”</span></p>
<p class="mb-4">These insights reshaped our approach, guiding the solutions we co-created with the community.</p>

<h3 class="text-xl font-bold mt-6 mb-3">Turning Insights into Action</h3>
<p class="mb-4">During a design sprint, we created simple, community-driven ideas:</p>
<ul class="list-disc pl-6 mb-6 space-y-2">
    <li>Dialogues led by men to rethink tradition.</li>
    <li>School mentorship programs for boys.</li>
    <li>Media campaigns promoting positive masculinity.</li>
</ul>

<h3 class="text-xl font-bold mt-6 mb-3">Early Signs of Change</h3>
<p class="mb-4">Today, small but powerful shifts are happening:</p>
<ul class="list-disc pl-6 mb-6 space-y-2">
    <li><strong>Changing Perspectives:</strong> More men and boys are questioning harmful practices.</li>
    <li><strong>Youth Empowerment:</strong> Young women and men are stepping into leadership roles.</li>
    <li><strong>Stronger Collaboration:</strong> Communities are building solutions together.</li>
    <li><strong>Sustained Support:</strong> New funding is helping us expand and deepen our impact.</li>
</ul>

<p class="mt-8 font-medium text-lg text-[#006377]">This project is about more than ending FGM. It's about transforming tradition — and creating a future where girls thrive, and men are part of the change.</p>
"""


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
            content = POWER_TO_YOUTH_CONTENT if slug == "power-to-youth" else title
            obj, _ = Project.objects.get_or_create(slug=slug, defaults={"title": title, "content": content})
            obj.title = title
            obj.tags = tags
            obj.challenge = challenge
            obj.headline_stat = stat
            if slug == "power-to-youth":
                obj.content = content
            obj.is_active = True
            obj.is_featured = True
            obj.order = i
            img = SEED_DIR / "articles" / f"{slug}.webp"
            if img.exists() and not obj.thumbnail:
                with img.open("rb") as fh:
                    obj.thumbnail.save(f"{slug}.webp", File(fh), save=False)
            obj.save()
        self.stdout.write(f"  articles: {Project.objects.filter(is_featured=True).count()}")
