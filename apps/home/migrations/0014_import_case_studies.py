"""Move case studies out of views.py and into the database.

Until now CASE_STUDIES and CASE_STUDY_DETAIL_DATA were Python literals, so the
only case studies anyone could edit in the admin were the three backed by the
Project model. This imports the existing content, then layers on the reviewed
teaser copy and statistics.

Statistics are marked outcome or context. A prevalence figure describes the
problem a programme addresses and is not a result IDI produced; presenting the
two identically would overclaim.
"""

from django.db import migrations
from django.utils.text import slugify

# Reviewed copy and figures supplied by the team. Only figures traceable to the
# company profile are included; see the note on Innovation Challenges below.
CONTENT = {
    'transboundary-data-flows-unep-giz-action-lab': {
        'title': 'Transboundary Data Flows Across East Africa',
        'partners_text': 'UNEP · GIZ · Action Lab',
        'category': 'DATA GOVERNANCE',
        'teaser': 'Environmental intelligence that can move across borders. IDI helped '
                  'design the governance and systems needed for secure, interoperable '
                  'environmental data exchange across five countries.',
        'challenge': 'Environmental data could not move securely or usefully across '
                     'national borders.',
        'stats': [
            ('5', 'countries', 'outcome', ''),
            ('119', 'priority datasets standardised', 'outcome', ''),
            ('16', 'national legislative contexts aligned', 'outcome', ''),
            ('<15 min', 'target emergency alert response', 'outcome', 'Design target'),
        ],
    },
    'access-to-justice-judiciary-of-kenya-kenya-law-action-lab': {
        'title': 'Access to Justice: AI for Kenya’s Judiciary',
        'partners_text': 'Judiciary of Kenya · Kenya Law · Action Lab · Cisco',
        'category': 'JUSTICE',
        'teaser': 'AI designed around the people who use the justice system. We helped '
                  'design, test and govern locally grounded AI tools to improve legal '
                  'research, efficiency and access to justice.',
        'challenge': 'Legal research was slow, limiting access to justice.',
        'stats': [('91%', 'faster case research', 'outcome', '')],
    },
    'kenyas-ai-opportunities-plan-action-lab': {
        'title': 'Kenya’s AI Opportunities Plan',
        'partners_text': 'Action Lab · Decision Intelligence Fellowship',
        'category': 'AI POLICY',
        'teaser': 'Turning national AI ambition into actionable opportunities. Research '
                  'across all 47 counties informed a portfolio of opportunity plans '
                  'spanning health, food systems, talent, infrastructure and other '
                  'priority areas.',
        'challenge': 'National AI ambition lacked evidence-backed, sector-specific plans.',
        'stats': [
            ('7', 'thematic AI opportunity plans', 'outcome', ''),
            ('47', 'counties researched', 'outcome', ''),
            ('20+', 'fellows', 'outcome', ''),
            ('100+', 'researchers', 'outcome', ''),
        ],
    },
    'spaceai-dairy-digitisation-cooperative-enablement': {
        'title': 'SpaceAI: Dairy Digitisation & Cooperative Enablement',
        'partners_text': 'SpaceAI · Agritech',
        'category': 'AGRITECH',
        'teaser': 'From WhatsApp conversations to better-performing dairy cooperatives. '
                  'IDI helped shape a WhatsApp-based agent network and AI-enabled '
                  'cooperative system for onboarding, milk-data capture, payments and '
                  'operations.',
        'challenge': 'Dairy cooperatives lacked the data and tooling to operate efficiently.',
        'stats': [
            ('156%', 'rise in cooperative milk volume', 'outcome', ''),
            ('48%', 'reduction in milk collection costs', 'outcome', ''),
            ('50,000', 'farmers engaged and directly impacted', 'outcome', ''),
            ('100+', 'agent conversations per day', 'outcome', ''),
        ],
    },
    'power-to-youth': {
        'title': 'Power to Youth: Men & Boys as Allies for Women’s Rights',
        'partners_text': 'Migori County · Gender Rights',
        'category': 'GENDER RIGHTS',
        'teaser': 'Bringing the people often left out of gender programming into the '
                  'solution. IDI worked with men, boys, elders and religious leaders to '
                  'co-design community-led approaches to challenging FGM and early marriage.',
        'challenge': 'Gender programming often excluded the men and gatekeepers whose '
                     'participation change depends on.',
        'stats': [
            ('3', 'intervention channels launched', 'outcome', ''),
            ('40', 'community members in immersive research', 'outcome', 'Over three weeks'),
            ('84%', 'FGM prevalence in the Kuria community', 'context',
             'Describes the problem addressed, not a programme result'),
        ],
    },
    'decision-intelligence-fellowships': {
        'title': 'Decision Intelligence Fellowships',
        'partners_text': 'DID Academy',
        'category': 'CAPABILITY',
        'teaser': 'Learning by working on real decisions. Fellows are embedded in live '
                  'research and implementation, building capability while generating '
                  'evidence for national programmes.',
        'challenge': 'Classroom-only training did not build decision-making capability.',
        'stats': [
            ('45%', 'increase in project completion', 'outcome', ''),
            ('20+', 'fellows', 'outcome', ''),
            ('100+', 'on-ground researchers', 'outcome', ''),
            ('47', 'county research reach', 'outcome', ''),
        ],
    },
    'innovation-challenges': {
        'title': 'Innovation Challenges: From Idea to Pilot Readiness',
        'partners_text': 'USAID · UNICEF · Tony Elumelu Foundation · Founders Factory Africa',
        'category': 'INNOVATION',
        'teaser': 'Helping innovators move from ideas to solutions people can test, fund '
                  'and scale. IDI has designed challenge programmes combining ecosystem '
                  'research, rapid prototyping, user testing, mentorship and '
                  'business-model development.',
        'challenge': 'Promising ideas stalled before reaching pilot or market readiness.',
        # The plastics tonnage is deliberately NOT imported. The company profile
        # states 12,400t in the case study and 14t in the portfolio overview --
        # a difference too large to publish without checking the programme
        # records. Add it in the admin once the correct figure is confirmed.
        'stats': [
            ('4', 'major challenge programmes delivered', 'outcome',
             'Afri-Plastics, Mombasa Plastics Prize, BeGreen Africa, FFA Academy'),
        ],
    },
    'be-green': {
        'title': 'BeGreen Africa: Young Green Ventures, Market-Ready',
        'partners_text': 'UNICEF · Kenya Girl Guides Association',
        'category': 'GREEN ECONOMY',
        'teaser': 'From green ideas to real ventures. Young innovators across Kenya were '
                  'supported to turn early concepts into market-ready green businesses, '
                  'combining design, mentorship and financial capability.',
        'challenge': 'Young green innovators lacked the support to reach market readiness.',
        'stats': [
            ('18', 'green ventures launched', 'outcome', ''),
            ('10+', 'counties reached', 'outcome', ''),
            ('24 months', 'from programme to portfolio', 'outcome', ''),
        ],
    },
}


def import_case_studies(apps, schema_editor):
    CaseStudy = apps.get_model('home', 'CaseStudy')
    CaseStudyStat = apps.get_model('home', 'CaseStudyStat')

    # Import the legacy list first so nothing currently on the site disappears.
    from apps.home.views import CASE_STUDIES, CASE_STUDY_DETAIL_DATA

    seen = set()
    order = 0
    for card in CASE_STUDIES:
        slug = card.get('slug')
        if not slug or slug in seen:
            continue
        seen.add(slug)
        detail = CASE_STUDY_DETAIL_DATA.get(slug, {})
        extra = CONTENT.get(slug, {})

        cs, _ = CaseStudy.objects.get_or_create(
            slug=slug,
            defaults={
                'title': extra.get('title') or card.get('title') or slug,
                'category': extra.get('category') or card.get('category', ''),
                'challenge': extra.get('challenge') or card.get('challenge', ''),
                'teaser': extra.get('teaser', ''),
                'partners_text': extra.get('partners_text', ''),
                'subtitle': detail.get('subtitle', ''),
                'sector': detail.get('sector', ''),
                'client': detail.get('client', ''),
                'timeline': detail.get('timeline', ''),
                'overview': detail.get('overview', '') or card.get('challenge', ''),
                'our_role': detail.get('our_role', ''),
                'key_insight': detail.get('key_insight', ''),
                'approach_text': detail.get('approach_text', ''),
                'outcome_text': detail.get('outcome_text', ''),
                'measuring_success': detail.get('measuring_success', ''),
                'hero_image_static': card.get('image', '') or detail.get('hero_image', ''),
                'tags': ', '.join(card.get('tags', []) or detail.get('tags', []) or []),
                'bg_color': card.get('bg_color', ''),
                'order': order,
                'is_published': True,
            },
        )
        order += 10

        # Card statistic from the legacy data, when no reviewed set replaces it.
        if slug not in CONTENT and card.get('stat_value') and card.get('stat_label'):
            CaseStudyStat.objects.get_or_create(
                case_study=cs, value=card['stat_value'], label=card['stat_label'],
                defaults={'kind': 'outcome', 'order': 0},
            )

    # Layer the reviewed copy and statistics over the imported records.
    for slug, data in CONTENT.items():
        cs = CaseStudy.objects.filter(slug=slug).first()
        if cs is None:
            cs = CaseStudy.objects.create(
                slug=slug, title=data['title'], order=order, is_published=True,
            )
            order += 10
        cs.title = data['title']
        cs.category = data.get('category', cs.category)
        cs.partners_text = data.get('partners_text', '')
        cs.teaser = data.get('teaser', '')
        cs.challenge = data.get('challenge', cs.challenge)
        if not cs.slug:
            cs.slug = slugify(cs.title)
        cs.save()

        cs.stats.all().delete()
        for i, (value, label, kind, note) in enumerate(data.get('stats', [])):
            CaseStudyStat.objects.create(
                case_study=cs, value=value, label=label, kind=kind,
                note=note, order=i,
            )


def remove_case_studies(apps, schema_editor):
    apps.get_model('home', 'CaseStudy').objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [('home', '0013_casestudy')]
    operations = [migrations.RunPython(import_case_studies, remove_case_studies)]
