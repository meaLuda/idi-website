from django.core.management.base import BaseCommand
from apps.home.models import Project


class Command(BaseCommand):
    help = 'Fix hero project cards to show exactly the specified projects'

    def handle(self, *args, **options):
        # Deactivate unwanted projects
        for title in ['Sovereign Data Infrastructure', 'Community Public-Service Redesign', 'Power to Youth', 'AI Ethics & Governance Toolkit', 'E4Impact Accelerator Program', 'Be Green']:
            n = Project.objects.filter(title=title).update(is_active=False)
            self.stdout.write(f'Deactivated {n} x "{title}"')

        # Deactivate the extra E4Impact at order=3
        n = Project.objects.filter(title='E4Impact Accelerator Program', order=3).update(is_active=False)
        self.stdout.write(f'Deactivated {n} x extra E4Impact (order=3)')

        # Ensure Kenya’s AI Opportunities Plan exists and is active/featured
        ai_title = 'Kenya’s AI Opportunities Plan - Action Lab'
        ai_slug = 'kenyas-ai-opportunities-plan-action-lab'
        ai_project, created = Project.objects.get_or_create(
            slug=ai_slug,
            defaults={
                'title': ai_title,
                'thumbnail': 'uploads/projects/thumbnails/ai_opp_main.webp',
                'tags': 'AI, Policy, Action Lab',
                'challenge': 'Challenge: Assessing and prioritising high-impact, context-relevant AI use cases and enabling conditions needed to implement them responsibly in Kenya.',
                'headline_stat': '20+ strategic initiatives identified',
                'is_featured': True,
                'is_active': True,
                'order': 0,
                'content': (
                    '<h2 class="text-2xl font-bold mb-4">Kenya’s AI Opportunities Plan: Objective & Strategy</h2>'
                    '<p class="mb-4">Develop a set of actionable AI Opportunity Plans for Kenya that identify and '
                    'prioritise high-impact, context-relevant AI use cases—and the enabling conditions needed to '
                    'implement them responsibly—across seven thematic areas: AI in Health, AI in Food Systems, '
                    'AI in Environment, Socio-Tech Mis- and Disinformation, Talent, Values of Data, Infrastructure.</p>'
                    '<p class="mb-4">IDI led the research and design process through the Decision Intelligence '
                    'Innovation Fellowship—structuring the methodology, developing tools, guiding fieldwork and '
                    'quality assurance, synthesising findings, and translating insights into clear, decision-ready '
                    'opportunities and recommendations that can be adopted by multiple stakeholders across Kenya, and regionally.</p>'
                )
            }
        )
        if not created:
            ai_project.title = ai_title
            ai_project.is_active = True
            ai_project.is_featured = True
            ai_project.order = 0
            ai_project.thumbnail = 'uploads/projects/thumbnails/ai_opp_main.webp'
            ai_project.tags = 'AI, Policy, Action Lab'
            ai_project.challenge = 'Challenge: Assessing and prioritising high-impact, context-relevant AI use cases and enabling conditions needed to implement them responsibly in Kenya.'
            ai_project.headline_stat = '20+ strategic initiatives identified'
            ai_project.save()
            self.stdout.write(f'Updated existing project "{ai_title}"')
        else:
            self.stdout.write(f'Created new project "{ai_title}"')

        # Ensure Transboundary Data Flows exists and is active/featured
        df_title = 'Transboundary Data Flows - UNEP, GIZ, Action Lab'
        df_slug = 'transboundary-data-flows-unep-giz-action-lab'
        df_project, created = Project.objects.get_or_create(
            slug=df_slug,
            defaults={
                'title': df_title,
                'thumbnail': 'uploads/projects/thumbnails/data_flows_main.webp',
                'tags': 'Data Flows, UNEP, GIZ',
                'challenge': 'Challenge: Architecting and operationalizing a regional framework for environmental data exchange across East Africa.',
                'headline_stat': '5 countries participating',
                'is_featured': True,
                'is_active': True,
                'order': 1,
                'content': (
                    '<h2 class="text-2xl font-bold mb-4">Transboundary Data Flows: Cross-Border Environmental Data Interoperability</h2>'
                    '<p class="mb-4">Architect and operationalize a regional framework for seamless, secure, and interoperable '
                    'exchange of environmental intelligence across East Africa—breaking down legal, political, and institutional silos '
                    'so that critical hydro-met and agricultural risk data can move across borders fast enough to support proactive, '
                    'evidence-based regional climate resilience.</p>'
                    '<p class="mb-4">IDI served as the systems-design and governance partner—convening multi-country stakeholders, '
                    'translating complex technical and legal realities into shared problem definitions, and co-designing the '
                    'disciplined backbone for regional data exchange.</p>'
                )
            }
        )
        if not created:
            df_project.title = df_title
            df_project.is_active = True
            df_project.is_featured = True
            df_project.order = 1
            df_project.thumbnail = 'uploads/projects/thumbnails/data_flows_main.webp'
            df_project.tags = 'Data Flows, UNEP, GIZ'
            df_project.challenge = 'Challenge: Architecting and operationalizing a regional framework for environmental data exchange across East Africa.'
            df_project.headline_stat = '5 countries participating'
            df_project.save()
            self.stdout.write(f'Updated existing project "{df_title}"')
        else:
            self.stdout.write(f'Created new project "{df_title}"')

        # Ensure National AI Policy exists and is active/featured
        policy_title = 'National AI and Emerging Tech Policy- MoICDE, KictaNET, Action Lab'
        policy_slug = 'national-ai-and-emerging-tech-policy-moicde-kictanet-action-lab'
        policy_project, created = Project.objects.get_or_create(
            slug=policy_slug,
            defaults={
                'title': policy_title,
                'thumbnail': 'uploads/projects/thumbnails/diplomacy_main.webp',
                'tags': 'AI Policy, MoICDE, KictaNET',
                'challenge': 'Challenge: Supporting a multi-stakeholder government-led journey to draft a National AI Policy framework for Kenya.',
                'headline_stat': '100% stakeholder alignment',
                'is_featured': True,
                'is_active': True,
                'order': 2,
                'content': (
                    '<h2 class="text-2xl font-bold mb-4">National AI and Emerging Tech Policy: Objective & Strategy</h2>'
                    '<p class="mb-4">Support the development of a coherent, inclusive, and future-oriented National AI '
                    'and Emerging Tech Policy that enables Kenya to harness AI for socio-economic transformation while '
                    'upholding constitutional values, public interest, and national sovereignty.</p>'
                    '<p class="mb-4">IDI serves as a technical partner and process facilitator—designing and guiding '
                    'a government-led, multi-stakeholder policy journey. IDI convenes diverse actors, structures participation, '
                    'synthesises evidence and stakeholder inputs, and translates perspectives into clear, policy-relevant outputs.</p>'
                )
            }
        )
        if not created:
            policy_project.title = policy_title
            policy_project.is_active = True
            policy_project.is_featured = True
            policy_project.order = 2
            policy_project.thumbnail = 'uploads/projects/thumbnails/diplomacy_main.webp'
            policy_project.tags = 'AI Policy, MoICDE, KictaNET'
            policy_project.challenge = 'Challenge: Supporting a multi-stakeholder government-led journey to draft a National AI Policy framework for Kenya.'
            policy_project.headline_stat = '100% stakeholder alignment'
            policy_project.save()
            self.stdout.write(f'Updated existing project "{policy_title}"')
        else:
            self.stdout.write(f'Created new project "{policy_title}"')

        # Set display order for the keepers
        Project.objects.filter(title='Kenya’s AI Opportunities Plan - Action Lab').update(order=0)
        Project.objects.filter(title='Transboundary Data Flows - UNEP, GIZ, Action Lab').update(order=1)
        Project.objects.filter(title='National AI and Emerging Tech Policy- MoICDE, KictaNET, Action Lab').update(order=2)
        Project.objects.filter(title='The Mombasa County Plastics Prize').update(order=3)

        # Update Space AI card headline stat
        Project.objects.filter(slug='space-ai').update(headline_stat='48% reduction in collection costs')

        self.stdout.write('\n--- Active projects in display order ---')
        for p in Project.objects.filter(is_active=True).order_by('order', '-created_at'):
            self.stdout.write(f'  order={p.order} | {p.title}')

        self.stdout.write(self.style.SUCCESS('\nDone!'))

