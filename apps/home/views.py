from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView
from .models import Project, TeamMember, Testimonial, Program, Partner, Client, HomeStat, ServicePillar

ARTICLE_PAGE_SIZE = 5

PRACTICE_TILES = [
    {"num": "01", "slug": "food-systems-health-practice", "title": "FOOD SYSTEMS PRACTICE"},
    {"num": "02", "slug": "sustainability-practice", "title": "HEALTH"},
    {"num": "03", "slug": "community-public-service-delivery", "title": "environment"},
    {"num": "04", "slug": "responsible-sovereign-ai", "title": "Responsible / Sovereign AI"},
    {"num": "05", "slug": "governance-public-service-delivery", "title": "Governance & Public Service Delivery"},
    {"num": "06", "slug": "venture-building-innovation-ecosystems", "title": "Venture Building & Innovation Ecosystems"},
]


def article_page(page_number):
    """A page of published articles (Projects), newest first."""
    qs = Project.objects.filter(is_active=True).order_by('order', '-created_at')
    return Paginator(qs, ARTICLE_PAGE_SIZE).get_page(page_number)


def articles(request):
    """HTMX endpoint: return one page of article cards."""
    return render(request, 'home/partials/_article_cards.html',
                  {'page': article_page(request.GET.get('page', 1))})

# Create your views here.
def home(request):
    # Optimize queries with select_related and prefetch_related
    team_members = TeamMember.objects.select_related().all()[:6]
    projects = Project.objects.filter(is_active=True).select_related()[:6]
    article_first_page = article_page(1)
    home_stats = HomeStat.objects.filter(is_active=True)
    service_pillars = ServicePillar.objects.filter(is_active=True)
    testimonials = Testimonial.objects.filter(is_active=True).select_related()
    partners = Partner.objects.filter(is_active=True, is_featured=True).select_related().order_by('order')
    clients = Client.objects.filter(is_active=True, is_featured=True).select_related().order_by('order')
    
    # SEO metadata
    context = {
        'team_members': team_members,
        'projects': projects,
        'article_first_page': article_first_page,
        'home_stats': home_stats,
        'service_pillars': service_pillars,
        'practices': PRACTICE_TILES,
        'testimonials': testimonials,
        'partners': partners,
        'clients': clients,
        'page_title': 'Home',
        'page_description': 'IDI Africa pioneers Decision Intelligence Design in Africa, transforming complexity into actionable solutions through our innovative fellowship programs and impactful initiatives.',
        'page_keywords': 'Decision Intelligence, Design Thinking, AI, Innovation, Fellowship, Africa, Kenya',
    }
    return render(request, "home/index.html", context)



def academy(request):
    # Get featured programs for the current year with optimized query
    featured_programs = Program.objects.filter(
        is_active=True, 
        is_featured=True, 
        year=2025
    ).select_related().order_by('order')
    
    # Get partners and clients for the academy page
    partners = Partner.objects.filter(is_active=True, is_featured=True).select_related().order_by('order')
    clients = Client.objects.filter(is_active=True, is_featured=True).select_related().order_by('order')
    
    # SEO metadata
    context = {
        'featured_programs': featured_programs,
        'partners': partners,
        'clients': clients,
        'page_title': 'Decision Intelligence Design Academy',
        'page_description': 'Develop critical skills in decision intelligence design through our comprehensive academy programs for professionals, executives, and organizations.',
        'page_keywords': 'Academy, Decision Intelligence Design, Training, Professional Development, Executive Education, Africa, Kenya',
    }
    return render(request, "home/fellowship/academy.html", context)


def civic_innovation_fellowship(request):
    """
    View for the Democratic Futures Civic Innovation Fellowship page.
    """
    context = {
        'page_title': 'Democratic Futures Civic Innovation Fellowship 2026',
        'page_description': "Building Kenya's Next Generation of Public Innovators. A fellowship to cultivate professionals who bridge technology, governance, and civic responsibility.",
        'page_keywords': 'Civic Innovation, Fellowship, Kenya, Public Innovators, Digital Governance, Decision Intelligence',
    }
    return render(request, 'home/fellowship/civic_innovation.html', context)


def project_detail(request, slug):
    if slug in ['power-to-youth', 'be-green']:
        from django.shortcuts import redirect
        return redirect('home:case_study_detail', slug=slug)

    if slug in ['kenyas-ai-opportunities-plan-action-lab', 'transboundary-data-flows-unep-giz-action-lab', 'national-ai-and-emerging-tech-policy-moicde-kictanet-action-lab']:
        detail = CASE_STUDY_DETAIL_DATA.get(slug)
        if detail is None:
            card = next((c for c in CASE_STUDIES if c["slug"] == slug), None)
            if card:
                detail = _build_default_detail(**card)
        if detail:
            context = {
                'cs': detail,
                'page_title': detail['title'],
                'page_description': detail['overview'][:160],
                'page_keywords': f"{detail['title']}, Project, Decision Intelligence Design, Africa, IDI",
            }
            return render(request, 'home/case_studies_detail.html', context)

    project = get_object_or_404(Project, slug=slug, is_active=True)
    
    # SEO metadata
    context = {
        'project': project,
        'page_title': project.title,
        'page_description': project.challenge or f'{project.title} - A decision intelligence design project by IDI Africa.',
        'page_keywords': f'{project.tags+", " if project.tags else ""}Decision Intelligence Design, {project.title}, Innovation, Africa, Kenya',
        'page_image': project.thumbnail,
        'og_type': 'article',
    }
    if slug == 'the-mombasa-county-plastics-prize':
        return render(request, 'home/projects/mombasa_plastics.html', context)
    elif slug == 'space-ai':
        return render(request, 'home/projects/space_ai.html', context)
        
    return render(request, 'home/projects/project_detail.html', context)


def program_detail(request, slug):
    program = get_object_or_404(Program, slug=slug, is_active=True)
    
    # SEO metadata
    context = {
        'program': program,
        'page_title': program.title,
        'page_description': program.meta_description if program.meta_description else program.short_description,
        'page_keywords': program.meta_keywords if program.meta_keywords else f'{program.title}, Decision Intelligence Design, Academy, Africa, Kenya',
        'page_image': program.image,
    }
    return render(request, 'home/programs/program_detail.html', context)

# New view for Projects list page (Our Work)
def projects_list(request):
    projects = Project.objects.filter(is_active=True).select_related().order_by('-created_at')
    
    mock_articles = [
        {
            "category": "Policy",
            "title": "The Future of Public Service Delivery",
            "excerpt": "How decision intelligence design is transforming public service delivery across Africa.",
            "tags": ["Governance", "Public Service Delivery"],
            "date": "January 2026",
        },
        {
            "category": "AI",
            "title": "Building Inclusive AI Governance Frameworks",
            "excerpt": "Designing AI architectures that are trusted, context-aware, and built for long-term public value.",
            "tags": ["AI", "Governance", "Design"],
            "date": "December 2025",
        },
        {
            "category": "Toolkit",
            "title": "Sustainability Toolkit: Measurement Frameworks",
            "excerpt": "Practical tools for tracking and measuring sustainability impacts across public initiatives.",
            "tags": ["Sustainability", "Measurement", "Toolkit"],
            "date": "December 2025",
        },
        {
            "category": "Ecosystems",
            "title": "Venture Ecosystem Rapid Assessment",
            "excerpt": "A comprehensive framework for evaluating and developing local venture building ecosystems.",
            "tags": ["Venture", "Ecosystem", "Innovation"],
            "date": "November 2025",
        },
        {
            "category": "Health",
            "title": "The Role of Design in Health Systems",
            "excerpt": "Why service design is critical to building resilient, responsive, and patient-centric healthcare systems.",
            "tags": ["Health", "Design", "Systems"],
            "date": "November 2025",
        },
        {
            "category": "Playbook",
            "title": "Innovation Challenges: Implementation Playbook",
            "excerpt": "A step-by-step guide to designing, launching, and managing public sector innovation challenges.",
            "tags": ["Innovation", "Design", "Implementation"],
            "date": "October 2025",
        }
    ]
    
    # SEO metadata
    context = {
        'projects': projects,
        'mock_articles': mock_articles,
        'page_title': 'Insights',
        'page_description': 'Research, thought leadership, and tools. Bringing context, representation, and deep decision intelligence to structural transitions.',
        'page_keywords': 'Insights, Decision Intelligence Design, Research, Whitepapers, Africa, Innovation',
    }
    return render(request, 'home/projects/projects_list.html', context)


CASE_STUDIES = [
    {
        "slug": "power-to-youth",
        "title": "Power to Youth",
        "category": "GENDER RIGHTS",
        "challenge": "Harmful traditions like FGM are practiced by 84% of the Kuria community in Migori County, Kenya.",
        "stat_value": "84%",
        "stat_label": "FGM PREVALENCE RATE",
        "tags": ["Gender Rights", "Youth", "Tradition"],
        "image": "images/power_to_youth/img1.png",
        "bg_color": "bg-white",
        "overview": "In Migori’s Kuria community, a new approach is challenging harmful traditions by engaging men and boys as allies for women’s rights. Among the Kuria people of Migori County, Kenya, female genital mutilation (FGM) is a deeply rooted tradition, practiced by 84% of the community. It marks a girl’s transition into womanhood and often leads to early marriage.",
        "our_role": "IDI designed and facilitated the community engagement and design sprint process—training the local teams in empathy-led human-centered design, structuring field research, gathering qualitative feedback across generations, and co-creating actionable interventions (dialogues, mentorship, and campaigns) directly with community leaders and youth.",
        "approach_text": "We combined desk research, field interviews, and community co-design sprints to engage men and boys as allies, leading to locally owned and sustainable interventions.",
        "outcome_text": "Today, small but powerful shifts are happening in Kuria community, including changing perspectives among men, youth leadership roles, and community-driven solutions to end FGM.",
        "subtitle": "Reimagining Tradition",
        "timeline": "2023 – 2025",
        "sector": "Gender Rights",
        "client": "Community Stakeholders",
        "hero_image": "images/power_to_youth/img1.png",
        "hero_image2": "images/power_to_youth/img2.png",
        "measuring_image": "images/power_to_youth/img1.png",
        "partners": [
            {"name": "IDI", "logo": "images/partners/regional-center.webp"}
        ]
    },
    {
        "slug": "transboundary-data-flows-unep-giz-action-lab",
        "title": "Transboundary Data Flows - UNEP, GIZ, Action Lab",
        "category": "DATA GOVERNANCE",
        "challenge": "Architecting and operationalizing a regional framework for environmental data exchange across East Africa.",
        "stat_value": "5",
        "stat_label": "COUNTRIES PARTICIPATING",
        "tags": ["Data Flows", "UNEP", "GIZ"],
        "image": "images/case-studies/data_flows_main.webp",
        "bg_color": "bg-white",
        "overview": "Architect and operationalize a regional framework for seamless, secure, and interoperable exchange of environmental intelligence across East Africa—breaking down legal, political, and institutional silos so that critical hydro-met and agricultural risk data can move across borders fast enough to support proactive, evidence-based regional climate resilience. This includes standardising 119+ priority datasets and aligning 16 national legislative contexts to enable trusted cross-border data sharing.",
        "our_role": "IDI served as the systems-design and governance partner—convening multi-country stakeholders, translating complex technical and legal realities into shared problem definitions, and co-designing the disciplined backbone for regional data exchange. IDI led end-to-end process design and facilitation, supported development of interoperability and data standardisation requirements, structured governance instruments, synthesised evidence into decision-ready outputs.",
        "approach_text": "A systemic Evidence-to-Action cycle: deep systems mapping (technical infrastructure audits + legal feasibility reviews) to identify choke points; strategic prototyping through co-creation design labs to develop politically viable, technically feasible governance and operating instruments (including fast-track disaster alert clauses); and embedded capacity building to institutionalise adoption through trained subnational officers and implementers.",
        "outcome_text": "A replicable model for transboundary environmental data governance that strengthens regional trust and coordination, contributes to broader African data sovereignty efforts, and improves readiness for climate shocks by enabling faster, more reliable cross-border information flows designed to compress emergency response timelines (e.g., toward <15 minutes for alerts) while protecting livelihoods and supporting cooperative management of shared natural resources.",
        "subtitle": "Cross-Border Environmental Data Interoperability",
        "timeline": "2024 – 2025",
        "sector": "Data Governance",
        "client": "UNEP, GIZ, Action Lab",
        "hero_image": "images/case-studies/data_flows_main.webp",
        "hero_image2": "images/case-studies/data_flows_detail.webp",
        "measuring_image": "images/case-studies/data_flows_detail.webp",
        "partners": [
            {"name": "UNEP", "logo": "images/partners/unep.webp"},
            {"name": "GIZ", "logo": "images/partners/challenge-works.webp"}
        ]
    },
    {
        "slug": "ai-powered-negotiation-tool-for-diplomacy-mfa-action-lab",
        "title": "AI Powered Negotiation Tool For Diplomacy - MFA, Action Lab",
        "category": "DIPLOMACY",
        "challenge": "Enabling diplomatic teams to access real-time decision support during bilateral and multilateral negotiations.",
        "stat_value": "3.5x",
        "stat_label": "FASTER DOCUMENT RETRIEVAL",
        "tags": ["AI", "Diplomacy", "MFA"],
        "image": "images/case-studies/diplomacy_main.webp",
        "bg_color": "bg-[#f5f1ea]",
        "overview": "Enable diplomatic teams to access real-time decision support during bilateral and multilateral negotiations by reducing reliance on manual research and fragmented data—improving speed of response and strengthening strategic leverage.",
        "our_role": "IDI served as the design and technical co-creation partner—mapping user needs with foreign-service officers, facilitating co-design to define the core use case, and leading development of an AI-enabled prototype that supports negotiators with synthesized briefs, modeled counterpart positions, and strategic talking points.",
        "approach_text": "We combined stakeholder interviews and co-design workshops with rapid prototyping—building an AI-driven assistant integrated with secure country-policy databases and trained on historical negotiation transcripts.",
        "outcome_text": "Secured commitment from the Ministry of Foreign and Diaspora Affairs to integrate the tool into the School of AI Diplomacy, an initiative led by the Foreign Services Academy and the Office of the Special Envoy on Technology, in partnership with IDI.",
        "subtitle": "AI-Enabled Decision Support for Negotiators",
        "timeline": "2025",
        "sector": "Diplomacy",
        "client": "MFA, Action Lab",
        "hero_image": "images/case-studies/diplomacy_main.webp",
        "hero_image2": "images/case-studies/diplomacy_detail.webp",
        "measuring_image": "images/case-studies/diplomacy_detail.webp",
        "partners": [
            {"name": "MFA Kenya", "logo": "images/partners/regional-center.webp"},
            {"name": "Action Lab", "logo": "images/partners/action-lab.webp"}
        ]
    },
    {
        "slug": "access-to-justice-judiciary-of-kenya-kenya-law-action-lab",
        "title": "Access To Justice - Judiciary of Kenya, Kenya Law, Action Lab",
        "category": "JUSTICE",
        "challenge": "Designing and deploying ethical, locally governed AI solutions to improve efficiency and equity in Kenya's justice system.",
        "stat_value": "91%",
        "stat_label": "CASE SEARCH RETRIEVAL SPEED",
        "tags": ["Justice", "Judiciary", "Kenya Law"],
        "image": "images/case-studies/justice_main.webp",
        "bg_color": "bg-white",
        "overview": "Design, pilot, and deploy ethical, locally governed AI solutions that improve access, efficiency, and equity in Kenya’s justice system—expanding access to legal information, reducing backlogs, enabling multilingual participation through transcription/translation, and supporting responsible AI adoption aligned with national and judiciary frameworks.",
        "our_role": "Under Action Lab, IDI provides technical and design leadership—leading user-centred co-creation, supporting development and testing of locally relevant AI models, strengthening governance and ethical safeguards, coordinating cross-sector partners, and supporting capacity building plus monitoring and learning for sustainable scale.",
        "approach_text": "A phased, collaborative model anchored in the AI Policy Framework: assess judicial workflows and user needs, co-design and pilot tools (e.g., AI legal research assistants and multilingual transcription), strengthen governance/data protection/oversight, train users, and iterate from pilot learning toward responsible scale-up.",
        "outcome_text": "More accessible legal information and more efficient, inclusive court processes—helping reduce case backlogs, support multilingual participation, and improve justice experience for all, especially underserved and vulnerable groups.",
        "subtitle": "Ethical and Locally Governed AI for Justice",
        "timeline": "2025 – Ongoing",
        "sector": "Justice & Legal Tech",
        "client": "Judiciary of Kenya, Kenya Law, Action Lab",
        "hero_image": "images/case-studies/justice_main.webp",
        "hero_image2": "images/case-studies/justice_detail.webp",
        "measuring_image": "images/case-studies/justice_detail.webp",
        "partners": [
            {"name": "Judiciary of Kenya", "logo": "images/partners/regional-center.webp"},
            {"name": "Kenya Law", "logo": "images/partners/challenge-works.webp"}
        ]
    },
    {
        "slug": "hack-for-the-environment-unep-giz-action-lab",
        "title": "Hack for the Environment - UNEP, GIZ, Action Lab",
        "category": "ENVIRONMENT",
        "challenge": "Mobilizing and empowering youth to design digital and data-driven solutions to the triple planetary crisis.",
        "stat_value": "120+",
        "stat_label": "DEVELOPERS ENGAGED",
        "tags": ["Environment", "Hackathon", "UNEP"],
        "image": "images/case-studies/eco_hack_main.webp",
        "bg_color": "bg-white",
        "overview": "Mobilize and empower Kenyan youth to develop practical, scalable digital and data-driven solutions to the triple planetary crisis—climate change, biodiversity loss, and pollution—while strengthening skills in AI, GIS, and human-centred design and identifying solutions that could feed into UNEP’s Digital Accelerator Lab for broader scalability.",
        "our_role": "IDI provided technical and advisory leadership by refining locally grounded problem statements, leading the Design Thinking for Environmental Solutions masterclass (human-centred design, stakeholder mapping, storytelling), mobilizing mentors and compiling datasets, and offering hands-on mentorship to help teams refine prototypes and strengthen team balance.",
        "approach_text": "A structured end-to-end participant journey from planning to execution, combining phased delivery (launch to UN showcase), targeted capacity building through partner masterclasses (e.g., design thinking, AI for sustainability, pitching), and iterative development via design sprints and mentor feedback—delivered in a hybrid format with ecosystem partners (academia and tech institutions) to recruit diverse and inclusive talent.",
        "outcome_text": "Over 1,000 applicants participated in the pipeline, with 157 innovators selected into 38 teams; 7 finalist teams showcased at the UN Office in Nairobi, and 3 winning solutions were selected—Msitu Guard (tree survival improvement from 30% to 93%), Earthwise Insights (community impact simulator for recyclers), and Marina AI (mangrove health prediction)—with top solutions positioned for integration into UNEP’s global digital innovation pipeline toward UNEA-7 goals.",
        "subtitle": "Empowering Youth for Eco-Innovation",
        "timeline": "2024 – 2025",
        "sector": "Sustainability & Youth",
        "client": "UNEP, GIZ, Action Lab",
        "hero_image": "images/case-studies/eco_hack_main.webp",
        "hero_image2": "images/case-studies/eco_hack_detail.webp",
        "measuring_image": "images/case-studies/eco_hack_detail.webp",
        "partners": [
            {"name": "UNEP", "logo": "images/partners/unep.webp"},
            {"name": "GIZ", "logo": "images/partners/challenge-works.webp"}
        ]
    },
    {
        "slug": "spaceai-dairy-digitisation-cooperative-enablement",
        "title": "SpaceAI (Dairy Digitisation & Cooperative Enablement)",
        "category": "AGRITECH",
        "challenge": "Strengthening dairy value chains through WhatsApp onboarding, milk data capture, and AI-enabled ERP systems.",
        "stat_value": "48%",
        "stat_label": "REDUCTION IN COLLECTION COSTS",
        "tags": ["SpaceAI", "Dairy", "Cooperative"],
        "image": "images/case-studies/dairy_digitisation_main.webp",
        "bg_color": "bg-[#f5f1ea]",
        "overview": "Support SpaceAI to strengthen Kenya’s dairy value chain by improving the reliability and quality of milk supply, enhancing cooperative governance and farmer payments, and enabling more sustainable smallholder livelihoods—responding to constraints like inconsistent supply, low prices, and quality challenges, as demand grows toward 2030.",
        "our_role": "IDI served as the design and innovation partner—applying our holistic, human-centred and systems-led practice (behavioural insights, systemic thinking, and service design) to help translate the challenge into a clear solution pathway, usable workflows, and decision-ready narratives for partners and stakeholders.",
        "approach_text": "Our methodology supported solution design around SpaceAI’s Advanced Digital Agent Network (ADAN)—a WhatsApp-based interface for onboarding, daily milk data capture and verification—backed by an AI-enabled ERP to manage cooperative governance (payments and payroll), and complemented by modules such as receivables gap financing, marketplace/check-off services, data-driven extension support, and aggregation linkages.",
        "outcome_text": "SpaceAI’s digitised operations strengthen efficiency, improving trust and productivity, with agents able to handle 100+ conversations per day; partners also reported higher agent satisfaction, improved cooperative resilience (including climate-shock coping support), and the work was backed by an independent impact study conducted with a professional firm.",
        "subtitle": "Value Chain and Cooperative Digitisation",
        "timeline": "2024 – 2025",
        "sector": "AgriTech",
        "client": "SpaceAI",
        "hero_image": "images/case-studies/dairy_digitisation_main.webp",
        "hero_image2": "images/case-studies/dairy_digitisation_detail.webp",
        "measuring_image": "images/case-studies/dairy_digitisation_detail.webp",
        "partners": [
            {"name": "SpaceAI", "logo": "images/partners/space-ai.webp"},
            {"name": "IDI", "logo": "images/partners/regional-center.webp"}
        ]
    },
    {
        "slug": "decision-intelligence-fellowships",
        "title": "Decision Intelligence Fellowships",
        "category": "EDUCATION",
        "challenge": "Training students and leaders to apply decision intelligence to create the National AI Opportunity Action Plan.",
        "stat_value": "45%",
        "stat_label": "INCREASE IN PROJECT COMPLETION",
        "tags": ["Fellowship", "Education", "DI"],
        "image": "images/case-studies/ai_opp_detail.webp",
        "bg_color": "bg-white",
        "overview": "This IDI capacity development program trains a cohort of individuals (students, professionals and teams) to apply decision intelligence and systemic thinking to produce field-grounded evidence and decision-ready insights. Our 2025-2026 program focuses on designing and developing the National AI Opportunity Action Plan across Food Systems, Health, Environment, Data, Compute, Talent and Sociotech sectors.",
        "our_role": "IDI led end-to-end program design and delivery as a research, design, and innovation institute grounded in human-centred principles, behavioural insights, systemic thinking, and service design—developing the methodology and research tools, training and coaching fellows, ensuring ethical integrity and data quality, convening cross-disciplinary support, and synthesising evidence into action-oriented insights and prioritised opportunity pathways for decision-makers.",
        "approach_text": "A DID Academy learn-as-you-do model where fellows learned decision intelligence (transdisciplinary design, data and AI) and applied it directly through desk research, field interviews, and nationwide Kobo-enabled data collection, supported by flexible learning modules (masterclasses, use-case clinics, design sprints, peer clinics, webinars, mentorship streams, field excursions, apprenticeships).",
        "outcome_text": "In Phase 1, we trained decision intelligence cohort of 20+ fellows, and a robust nationwide on-ground researchers of 100+ talent who gathered evidence feeding into the National AI Opportunities Plan design and development, with a sequenced publication plan beginning with the Health AI Opportunity Plan report and followed by the remaining thematic reports.",
        "subtitle": "Training the Next Generation of Public Sector Innovators",
        "timeline": "2025 – 2026",
        "sector": "Capability Development",
        "client": "IDI Academy",
        "hero_image": "images/case-studies/ai_opp_detail.webp",
        "hero_image2": "images/case-studies/ai_opp_main.webp",
        "measuring_image": "images/case-studies/ai_opp_main.webp",
        "partners": [
            {"name": "IDI Academy", "logo": "images/partners/unicef.webp"}
        ]
    },
    {
        "slug": "public-sector-and-executive-trainings-action-lab",
        "title": "Public Sector and Executive Trainings - Action Lab",
        "category": "TRAINING",
        "challenge": "Equipping senior public servants with leadership tools, use-case prioritisation, and roadmaps to steer AI adoption.",
        "stat_value": "500+",
        "stat_label": "EXECUTIVES TRAINED",
        "tags": ["Public Sector", "Training", "Action Lab"],
        "image": "images/case-studies/diplomacy_detail.webp",
        "bg_color": "bg-white",
        "overview": "Equip senior public servants and public-sector executives with the practical literacy and leadership tools to steer AI adoption in government—linking national development priorities to actionable AI governance, portfolio strategy, procurement readiness, and institutional change management.",
        "our_role": "Grounded in human- and life-centred design, behavioural insights, systems thinking, and decision intelligence, IDI curates the learning pathway, developing applied government-ready tools (decision canvases, risk registers, use-case prioritisation frameworks), facilitating sessions, coaching teams, and synthesising outputs into implementable roadmaps and leadership commitments.",
        "approach_text": "Short-cycle learning models blending strategic briefings with applied clinics: participants map their institutional mandates, surface constraints and risks, prioritise high-value AI use cases, and produce decision-ready artifacts through guided sessions (workshops, use-case clinic, risk and ethics clinic, implementation readiness clinic), supported by pre-reads, real public-sector cases, peer exchange, and rapid coaching.",
        "outcome_text": "A leadership and public-sector cohort able to articulate AI opportunity pathways for their institutions, with prioritised use-case portfolios, minimum governance requirements, and a sequenced next-steps plan covering policy alignment, capability gaps, data readiness, procurement considerations, and delivery partnerships. Key participating institutions include Kenya School of Government, Ministry- and State Department of Foreign and Diaspora Affairs, Council of Governors, Kenya Defence Forces, and Ministry of Energy and Petroleum.",
        "subtitle": "AI Literacy and Governance for Senior Officials",
        "timeline": "2024 – 2025",
        "sector": "Executive Education",
        "client": "Kenya School of Govt, Council of Governors, KDF",
        "hero_image": "images/case-studies/diplomacy_detail.webp",
        "hero_image2": "images/case-studies/diplomacy_main.webp",
        "measuring_image": "images/case-studies/diplomacy_main.webp",
        "partners": [
            {"name": "KSG", "logo": "images/partners/challenge-works.webp"},
            {"name": "Action Lab", "logo": "images/partners/action-lab.webp"}
        ]
    },
    {
        "slug": "action-lab-public-value-innovation-hub-for-ai-and-emerging-technologies",
        "title": "Action Lab- Public-Value Innovation Hub for AI and Emerging Technologies",
        "category": "INNOVATION",
        "challenge": "Collaborating to turn complex public sector priorities into working, trusted, and scaled systems.",
        "stat_value": "12",
        "stat_label": "ACTIVE PROTOTYPES",
        "tags": ["Action Lab", "Public Value", "Innovation"],
        "image": "images/case-studies/justice_detail.webp",
        "bg_color": "bg-[#f5f1ea]",
        "overview": "As a core founding and strategic partner, we collaborate with Action Lab partners to turn complex priorities across sectors into working systems that deliver measurable impact in public service delivery and goods—moving from ideas and pilots to solutions that are used, trusted, and scaled.",
        "our_role": "IDI serves as Action Lab’s research, design, and innovation partner—bringing a holistic practice grounded in human-centred principles, behavioural insights, systemic thinking, and service design to shape opportunities, translate evidence into action-oriented insights, and co-create solutions that can be implemented responsibly.",
        "approach_text": "We align IDI’s Learn → Create → Empower model with Action Lab’s cyclical delivery approach—Identify → Design → Build → Deploy → Scale—combining research and ecosystem mapping, co-design, prototyping, and implementation support, guided by Action Lab’s principles of safety, security, trustworthiness, inclusivity, and sustainability in AI and emerging technologies.",
        "outcome_text": "Sector priorities translate into durable, implementation-ready systems—validated for real-world adoption, deployed with partners, and positioned for scaling across communities, institutions, and markets. Together, we co-convene and co-deliver public-value innovation programs which attracted over 30 projects cutting across public and private sector, and academia.",
        "subtitle": "Co-Creating Trusted Civic Infrastructure",
        "timeline": "2024 – 2026",
        "sector": "Public Tech & Infrastructure",
        "client": "Action Lab Partners",
        "hero_image": "images/case-studies/justice_detail.webp",
        "hero_image2": "images/case-studies/justice_main.webp",
        "measuring_image": "images/case-studies/justice_main.webp",
        "partners": [
            {"name": "Action Lab", "logo": "images/partners/action-lab.webp"}
        ]
    },
    {
        "slug": "national-ai-and-emerging-tech-policy-moicde-kictanet-action-lab",
        "title": "National AI and Emerging Tech Policy- MoICDE, KictaNET, Action Lab",
        "category": "POLICY",
        "challenge": "Supporting a multi-stakeholder government-led journey to draft a National AI Policy framework for Kenya.",
        "stat_value": "100%",
        "stat_label": "STAKEHOLDER ALIGNMENT",
        "tags": ["AI Policy", "MoICDE", "KictaNET"],
        "image": "images/case-studies/diplomacy_main.webp",
        "bg_color": "bg-white",
        "overview": "Support the development of a coherent, inclusive, and future-oriented National AI and Emerging Tech Policy that enables Kenya to harness AI for socio-economic transformation while upholding constitutional values, public interest, and national sovereignty—balancing innovation with risk management, strengthening local capacity, and positioning Kenya within regional and global AI ecosystems.",
        "our_role": "IDI serves as a technical partner and process facilitator—designing and guiding a government-led, multi-stakeholder policy journey. IDI convenes diverse actors, structures participation, synthesises evidence and stakeholder inputs, and translates perspectives into clear, policy-relevant outputs.",
        "approach_text": "IDI applies a participatory, evidence-based, sovereignty-first approach that combines international benchmarking with deep contextualisation to Kenya’s socio-economic realities and institutional capacity. Through structured facilitation, thematic working groups, and rapid drafting, IDI helps move discussions from principles to actionable policy components, systematically integrating cross-cutting issues such as inclusion, ethics, data governance, capacity development, and environmental sustainability.",
        "outcome_text": "A nationally owned and implementable National AI Policy framework that aims to provide clear strategic direction, defines governance and coordination mechanisms, identifies priority areas for AI adoption, and establishes a strong foundation for responsible, inclusive, and sustainable AI use—strengthening public trust, institutional readiness, and policy coherence to support effective AI adoption across Kenya’s economy and public sector.",
        "subtitle": "Multi-Stakeholder Policy Design Journey",
        "timeline": "2025 – Ongoing",
        "sector": "AI Policy & Governance",
        "client": "MoICDE, KictaNET, Action Lab",
        "hero_image": "images/case-studies/diplomacy_main.webp",
        "hero_image2": "images/case-studies/diplomacy_detail.webp",
        "measuring_image": "images/case-studies/diplomacy_detail.webp",
        "partners": [
            {"name": "MoICDE", "logo": "images/partners/regional-center.webp"},
            {"name": "KictaNET", "logo": "images/partners/challenge-works.webp"}
        ]
    },
    {
        "slug": "innovation-challenges",
        "title": "Innovation Challenges",
        "category": "CHALLENGES",
        "challenge": "Designing prize-based challenges targeting community waste management and plastic reduction.",
        "stat_value": "12,400",
        "stat_label": "TONS OF PLASTIC COLLECTED",
        "tags": ["Innovation", "Challenges", "Prizes"],
        "image": "images/case-studies/eco_hack_detail.webp",
        "bg_color": "bg-white",
        "overview": "Build the capabilities of innovators and organizations to design context-relevant solutions and move from idea to market/pilot readiness through custom-designed Innovation Challenges.",
        "our_role": "IDI serves as the design and innovation lead—facilitating the sprint process, providing tools/templates and coaching, convening cross-disciplinary expertise, and strengthening business strategy, storytelling, and (where relevant) technical readiness.",
        "approach_text": "We apply IDI’s holistic, human-centred and systems-led methodology—grounded in behavioural insights and service design—delivered through “learning-by-doing” sprints that combine research and ecosystem understanding, problem framing, ideation, rapid prototyping, user testing, and business/pitch refinement supported by ongoing mentorship, clinics, and feedback loops.",
        "outcome_text": "Across programs, teams leave with clearer value propositions, stronger business models, and more investable outputs—such as refined prototypes and pitches, entrepreneur growth and funding readiness through programs like Afri-Plastics Challenge & Mombasa Plastics Prize Challenge (USAID, Challenge Works, Proportion Global), BeGreen Africa (UNICEF, Tony Elumelu Foundation), and Founders Factory Africa Academy, and structured technical assistance culminating in demo-ready MVPs and investor materials.",
        "subtitle": "Ecosystem Capacity Building and Sprint Frameworks",
        "timeline": "2023 – 2025",
        "sector": "Incubators & Sprints",
        "client": "USAID, UNICEF, TEF, Founders Factory",
        "hero_image": "images/case-studies/eco_hack_detail.webp",
        "hero_image2": "images/case-studies/eco_hack_main.webp",
        "measuring_image": "images/case-studies/eco_hack_main.webp",
        "partners": [
            {"name": "USAID", "logo": "images/partners/unicef.webp"},
            {"name": "UNICEF", "logo": "images/partners/unicef.webp"}
        ]
    },
    {
        "slug": "startups-business-design-and-innovation",
        "title": "Startups Business Design and Innovation",
        "category": "VENTURES",
        "challenge": "Providing early-stage startups with hands-on business modeling and sovereign tech architectures.",
        "stat_value": "30+",
        "stat_label": "STARTUPS ACCELERATED",
        "tags": ["Startups", "Business Design", "Ventures"],
        "image": "images/case-studies/dairy_digitisation_detail.webp",
        "bg_color": "bg-[#f5f1ea]",
        "overview": "Strengthen startup and ecosystem actors’ capabilities to design context-relevant solutions and progress from early ideas to pilot and market readiness.",
        "our_role": "IDI has been serving as the design and innovation lead—structuring and facilitating the capacity-building journey, equipping teams with practical tools and coaching, convening cross-disciplinary expertise, and strengthening business strategy, storytelling, and (where relevant) technical readiness.",
        "approach_text": "We applied IDI’s holistic, human-centred and systems-led methodology—grounded in behavioural insights and service design—through “learning-by-doing” sprints that combined ecosystem and user research, problem framing, ideation, rapid prototyping, user testing, and pitch/business model refinement, reinforced with mentorship clinics and continuous feedback loops.",
        "outcome_text": "Startups and innovators emerged with clearer value propositions, stronger business models, and more investable outputs—ranging from refined prototypes and pitches (MPP, BeGreen), to entrepreneur growth and funding readiness (FFA), and structured Phase 2 technical assistance for AI teams resulting in demo-ready MVPs and investor materials.",
        "subtitle": "Venture Acceleration & Innovation Sprints",
        "timeline": "2024 – 2025",
        "sector": "Venture Building",
        "client": "Startups & Accelerators",
        "hero_image": "images/case-studies/dairy_digitisation_detail.webp",
        "hero_image2": "images/case-studies/dairy_digitisation_main.webp",
        "measuring_image": "images/case-studies/dairy_digitisation_main.webp",
        "partners": [
            {"name": "IDI", "logo": "images/partners/regional-center.webp"},
            {"name": "FFA", "logo": "images/partners/founders-factory.webp"}
        ]
    },
    {
        "slug": "be-green",
        "title": "Be Green",
        "category": "SUSTAINABILITY",
        "challenge": "Empowering young entrepreneurs through life-centered design, collaboration, and sustainable innovation.",
        "stat_value": "18",
        "stat_label": "VENTURES LAUNCHED",
        "tags": ["Sustainability", "Ventures", "Sprint"],
        "image": "images/be_green/img1.webp",
        "bg_color": "bg-white",
        "overview": "Across Kenya, young innovators are transforming bold, sustainable ideas into real businesses. Yet without access to funding, mentorship, and practical tools, many promising ventures struggle to grow. To close this gap, the Institute of Design and Innovation (IDI), UNICEF, and the Kenya Girl Guides Association launched the BeGreen Africa Design Sprint, a program helping young entrepreneurs move from early concepts to market-ready solutions.",
        "our_role": "IDI served as the design and innovation partner—applying our design sprint methodology, mentoring co-creation, and integrating foundational financial literacy.",
        "approach_text": "Learning by Doing: Entrepreneurs engaged in collective problem-solving, testing assumptions, sharing peer critiques, and co-evolving stronger solutions together.",
        "outcome_text": "From Mombasa to Nairobi, participants from over 10 counties joined the BeGreen Africa sprint, launching 18 ventures in 24 months across sustainable agriculture, renewable energy, eco-manufacturing, and green packaging.",
        "subtitle": "Designing Change: How Innovation Sprints Are Fueling Green Businesses in Kenya",
        "timeline": "2023 – 2025",
        "sector": "Sustainability & Ventures",
        "client": "UNICEF, KGGA, IDI",
        "hero_image": "images/be_green/img1.webp",
        "hero_image2": "images/be_green/img2.webp",
        "measuring_image": "images/be_green/img1.webp",
        "partners": [
            {"name": "UNICEF", "logo": "images/partners/unicef.webp"},
            {"name": "IDI", "logo": "images/partners/regional-center.webp"}
        ]
    }
]

# New view for Case Studies page
def case_studies_list(request):
    page_number = request.GET.get('page', 1)
    paginator = Paginator(CASE_STUDIES, 6)
    page_obj = paginator.get_page(page_number)

    # SEO metadata
    context = {
        'case_studies': page_obj.object_list,
        'page_obj': page_obj,
        'page_title': 'Case Studies',
        'page_description': 'We start where systems fall short. By focusing on underserved communities and overlooked realities, we design toward equitable, inclusive outcomes that scale across diverse African contexts.',
        'page_keywords': 'Case Studies, Decision Intelligence Design, Solutions, Outcomes, Africa',
    }
    return render(request, 'home/case_studies_list.html', context)


# Shared case study detail data (slug-keyed)
CASE_STUDY_DETAIL_DATA = {
    "power-to-youth": {
        "slug": "power-to-youth",
        "title": "Power to Youth",
        "subtitle": "Reimagining Tradition: How Men and Boys Are Driving Change in Migori County",
        "category": "GENDER RIGHTS",
        "sector": "Gender Rights",
        "client": "Community Stakeholders",
        "timeline": "2023 – 2025",
        "tags": ["Gender Rights", "Youth", "Tradition"],
        "hero_image": "images/power_to_youth/img1.png",
        "hero_image2": "images/power_to_youth/img2.png",
        "portrait_image": "images/governance/program_team.webp",
        "overview": (
            "In Migori’s Kuria community, a new approach is challenging harmful traditions by engaging men and boys as allies for women’s rights. Among the Kuria people of Migori County, Kenya, female genital mutilation (FGM) is a deeply rooted tradition, practiced by 84% of the community. It marks a girl’s transition into womanhood and often leads to early marriage."
        ),
        "our_role": (
            "IDI designed and facilitated the community engagement and design sprint process—training the local teams in empathy-led human-centered design, structuring field research, gathering qualitative feedback across generations, and co-creating actionable interventions (dialogues, mentorship, and campaigns) directly with community leaders and youth."
        ),
        "key_insight": (
            "Our journey began with introspection. We trained our team in human-centered design, grounding our work in empathy and collaboration to co-create solutions directly with the community."
        ),
        "problems": [
            {
                "icon": "chart",
                "title": "Exclusion of Men & Boys",
                "description": "For generations, efforts to protect girls from harmful traditions focused mainly on women, leaving out the primary cultural gatekeepers — men and boys."
            },
            {
                "icon": "user",
                "title": "High Prevalence & Child Marriage",
                "description": "Female genital mutilation (FGM) is practiced by 84% of the community, marking a girl's transition to womanhood and leading to early marriage."
            },
            {
                "icon": "alert",
                "title": "Normalized Traditional Status",
                "description": "Many men and boys in the community had never questioned the consequences of practices like FGM, seeing it simply as traditional protocol."
            }
        ],
        "approach_steps": [
            {"number": "01", "title": "Community Listening", "description": "Conversations with religious leaders, elders, young women, and men to understand historical perspectives."},
            {"number": "02", "title": "Field Research", "description": "Three weeks of immersive research speaking with 40 community members across generations."},
            {"number": "03", "title": "Design Sprints", "description": "Iterative prototyping sessions to co-create community-driven ideas and campaigns."},
            {"number": "04", "title": "Men-Led Dialogues", "description": "Establishing safe spaces where men and boys openly question traditional gender expectations."},
            {"number": "05", "title": "Mentorship & Campaigns", "description": "Launching school mentorship programs and media campaigns to promote positive masculinity."}
        ],
        "output_stats": [
            {"value": "40+", "label": "Community members interviewed across generations", "image": "images/power_to_youth/img2.png"},
            {"value": "84%", "label": "Community FGM prevalence rate challenged", "image": "images/power_to_youth/img3.png"},
            {"value": "3", "label": "Intervention channels designed & launched", "image": "images/power_to_youth/img4.png"}
        ],
        "measurable_improvements": [
            {"value": "40+", "label": "Community Interviews"},
            {"value": "84%", "label": "Prevalence Challenged"},
            {"value": "3", "label": "Intervention Channels"}
        ],
        "measuring_success": (
            "We measured success by the shift in perspectives and active youth leadership. "
            "More men and boys are questioning harmful practices, and new community-driven "
            "dialogues have been established to sustain the impact."
        ),
        "partners": [
            {"name": "IDI", "logo": "images/partners/regional-center.webp"}
        ],
        "related": [
            {
                "slug": "transboundary-data-flows-unep-giz-action-lab",
                "title": "Transboundary Data Flows - UNEP, GIZ, Action Lab",
                "category": "DATA GOVERNANCE",
                "image": "images/case-studies/data_flows_main.webp",
            },
            {
                "slug": "spaceai-dairy-digitisation-cooperative-enablement",
                "title": "SpaceAI (Dairy Digitisation & Cooperative Enablement)",
                "category": "AGRITECH",
                "image": "images/case-studies/dairy_digitisation_main.webp",
            }
        ]
    },
    "kenyas-ai-opportunities-plan-action-lab": {
        "slug": "kenyas-ai-opportunities-plan-action-lab",
        "title": "Kenya’s AI Opportunities Plan - Action Lab",
        "subtitle": "Objective & Strategy",
        "category": "AI & POLICY",
        "sector": "AI & Policy",
        "client": "Action Lab",
        "timeline": "2025 – 2026",
        "tags": ["AI", "Policy", "Action Lab"],
        "hero_image": "images/case-studies/ai_opp_main.webp",
        "hero_image2": "images/case-studies/ai_opp_detail.webp",
        "measuring_image": "images/case-studies/ai_opp_detail.webp",
        "overview": (
            "Develop a set of actionable AI Opportunity Plans for Kenya that identify and prioritise high-impact, context-relevant AI use cases—and the enabling conditions needed to implement them responsibly—across seven thematic areas: AI in Health, AI in Food Systems, AI in Environment, Socio-Tech Mis- and Disinformation, Talent, Values of Data, Infrastructure."
        ),
        "our_role": (
            "IDI led the research and design process through the Decision Intelligence Innovation Fellowship—structuring the methodology, developing tools, guiding fieldwork and quality assurance, synthesising findings, and translating insights into clear, decision-ready opportunities and recommendations that can be adopted by multiple stakeholders across Kenya, and regionally."
        ),
        "key_insight": (
            "By establishing a nationwide, county-level distributed research network, we grounded policy recommendations in actual county infrastructure capabilities rather than urban assumptions."
        ),
        "problems": [
            {
                "icon": "chart",
                "title": "Uncoordinated AI Use Cases",
                "description": "Fragmented pilots and lack of alignment on high-priority AI use cases tailored to local contexts."
            },
            {
                "icon": "user",
                "title": "Capacities & Talent Deficits",
                "description": "Shortage of technical, ethical, and implementation skills across community and county systems."
            },
            {
                "icon": "alert",
                "title": "Data Governance Silos",
                "description": "Absence of responsible data exchange, infrastructure frameworks, and ethical guidelines."
            }
        ],
        "approach_steps": [
            {"number": "01", "title": "Desk Research", "description": "Analyzing international benchmarks and aligning with regional policy guidelines."},
            {"number": "02", "title": "Field Interviews", "description": "Engaging stakeholders across counties to capture grassroots requirements."},
            {"number": "03", "title": "Data Collection", "description": "Utilizing Kobo-enabled tools with 100+ on-ground researchers across Kenya."},
            {"number": "04", "title": "Synthesis & Prioritization", "description": "Using human-centred and systems-led lenses to identify top opportunities."},
            {"number": "05", "title": "Thematic Rollout", "description": "Formulating structured recommendations starting with the Health AI report."}
        ],
        "output_stats": [
            {"value": "20+", "label": "Strategic initiatives identified", "image": "images/case-studies/ai_opp_main.webp"},
            {"value": "100+", "label": "On-ground researchers deployed", "image": "images/case-studies/ai_opp_detail.webp"},
            {"value": "7", "label": "Thematic areas analyzed", "image": "images/case-studies/ai_opp_detail.webp"}
        ],
        "measurable_improvements": [
            {"value": "20+", "label": "Strategic Plans"},
            {"value": "100+", "label": "Researchers Trained"},
            {"value": "7", "label": "Thematic Sectors Covered"}
        ],
        "measuring_success": (
            "We measured success by stakeholder alignment and implementation readiness. "
            "Our draft recommendations were validated across public, private, and academic "
            "sectors before publication."
        ),
        "partners": [
            {"name": "Action Lab", "logo": "images/partners/action-lab.webp"},
            {"name": "Kenya", "logo": "images/partners/regional-center.webp"}
        ],
        "related": [
            {
                "slug": "transboundary-data-flows-unep-giz-action-lab",
                "title": "Transboundary Data Flows - UNEP, GIZ, Action Lab",
                "category": "DATA GOVERNANCE",
                "image": "images/case-studies/data_flows_main.webp",
            },
            {
                "slug": "spaceai-dairy-digitisation-cooperative-enablement",
                "title": "SpaceAI (Dairy Digitisation & Cooperative Enablement)",
                "category": "AGRITECH",
                "image": "images/case-studies/dairy_digitisation_main.webp",
            }
        ]
    },
    "digitizing-maternal-care": {
        "slug": "digitizing-maternal-care",
        "title": "Digitizing Maternal Care",
        "subtitle": "Keeping Mothers Connected Across Every Point of Care",
        "category": "HEALTH",
        "sector": "Public Health",
        "client": "Ministry of Health",
        "timeline": "2022 – 2024",
        "tags": ["Health", "Digital Identity", "CHW Systems"],
        "hero_image": "images/mamaDigital.webp",
        "hero_image2": "images/community/case2.webp",
        "portrait_image": "images/governance/program_team.webp",
        "overview": (
            "The Digitizing Maternal Care project tackled one of Kenya's most persistent health-system "
            "failures: fragmented, paper-based maternal records that followed no single mother from "
            "antenatal booking through postnatal follow-up. Community Health Workers (CHWs) operated "
            "with paper registers that were lost, damaged, or simply never transferred when mothers "
            "moved clinics or gave birth outside a facility. The result was a dangerous gap in continuity "
            "of care that cost lives."
        ),
        "key_insight": (
            "When mothers move between clinics, their records don't follow them — this single "
            "failure accounts for 30% of missed postnatal follow-ups in peri-urban areas. "
            "Designing a lightweight, offline-capable digital identity for maternal records "
            "closes this gap without requiring hospitals to upgrade infrastructure."
        ),
        "problems": [
            {
                "icon": "chart",
                "title": "Fragmented Records",
                "description": "Each facility maintained siloed paper registers with no shared identifier, making continuity impossible when mothers transferred between clinics."
            },
            {
                "icon": "user",
                "title": "Lost Postnatal Follow-Ups",
                "description": "30% of postnatal visits were missed because CHWs had no way to know which mothers had already delivered or received care elsewhere."
            },
            {
                "icon": "alert",
                "title": "Invisible Complications",
                "description": "High-risk pregnancies flagged at one facility were invisible to the next, preventing timely intervention and increasing maternal mortality risk."
            },
        ],
        "approach_steps": [
            {"number": "01", "title": "Community Listening", "description": "Deep ethnographic research with 120 CHWs across 6 counties to map paper-based workflows."},
            {"number": "02", "title": "Co-Design Sprints", "description": "Iterative prototyping sessions with frontline CHWs to design a tool they could own."},
            {"number": "03", "title": "Pilot & Learn", "description": "3-month pilots in 2 counties with weekly feedback loops before broader rollout."},
            {"number": "04", "title": "Platform Architecture", "description": "Offline-first mobile platform with a unique maternal ID that persisted across facilities."},
            {"number": "05", "title": "System Integration", "description": "Connected to existing DHIS2 national health database for Ministry of Health reporting."},
        ],
        "output_stats": [
            {"value": "27,535", "unit": "kilograms", "label": "of paper records digitized in pilot counties", "image": "images/governance/case1.webp"},
            {"value": "57", "label": "young innovators trained as digital health CHWs", "image": "images/community/team1.webp"},
            {"value": "100%", "label": "of innovators completed the 6-month programme", "image": "images/governance/case2.webp"},
            {"value": "67%", "label": "of innovators secured employment within 3 months", "image": "images/community/case1.webp"},
            {"value": "51%", "label": "of innovators are women and girls", "image": "images/community/team2.webp"},
            {"value": "730+", "label": "volunteer hours contributed to community clinics", "image": "images/governance/case3.webp"},
        ],
        "measurable_improvements": [
            {"value": "91%", "label": "Record Continuity Rate"},
            {"value": "3×", "label": "Faster Record Retrieval"},
            {"value": "Better", "label": "Data Quality Score"},
            {"value": "100%", "label": "Reduced Paper Cost"},
            {"value": "Reduced", "label": "Missed Follow-Ups"},
            {"value": "Improved", "label": "Maternal Outcomes"},
        ],
        "measuring_success": (
            "Success was defined not by technology adoption but by health outcomes. "
            "We tracked postnatal follow-up completion rates, record integrity across "
            "facility transfers, and CHW confidence scores before and after deployment. "
            "Every metric was co-designed with the Ministry of Health to ensure alignment "
            "with national health system KPIs."
        ),
        "measuring_image": "images/community/case3.webp",
        "partners": [
            {"name": "USAID", "logo": "images/partners/unicef.webp"},
            {"name": "Canada", "logo": "images/partners/challenge-works.webp"},
            {"name": "Kenya MoH", "logo": "images/partners/regional-center.webp"},
        ],
        "related": [
            {
                "slug": "power-to-youth",
                "title": "Power to Youth",
                "category": "GENDER RIGHTS",
                "image": "images/power_to_youth/img1.png",
            },
            {
                "slug": "transboundary-data-flows-unep-giz-action-lab",
                "title": "Transboundary Data Flows - UNEP, GIZ, Action Lab",
                "category": "DATA GOVERNANCE",
                "image": "images/governance/case2.webp",
            },
            {
                "slug": "spaceai-dairy-digitisation-cooperative-enablement",
                "title": "SpaceAI (Dairy Digitisation & Cooperative Enablement)",
                "category": "AGRITECH",
                "image": "images/community/case2.webp",
            },
        ],
    },
    "be-green": {
        "slug": "be-green",
        "title": "Be Green",
        "subtitle": "Designing Change: How Innovation Sprints Are Fueling Green Businesses in Kenya",
        "category": "SUSTAINABILITY",
        "sector": "Sustainability & Ventures",
        "client": "UNICEF, KGGA, IDI",
        "timeline": "2023 – 2025",
        "tags": ["Sustainability", "Ventures", "Sprint"],
        "hero_image": "images/be_green/img1.webp",
        "hero_image2": "images/be_green/img2.webp",
        "portrait_image": "images/home/hero-portrait.webp",
        "overview": (
            "Across Kenya, young innovators are transforming bold, sustainable ideas into real businesses. "
            "Yet without access to funding, mentorship, and practical tools, many promising ventures struggle to grow. "
            "To close this gap, the Institute of Design and Innovation (IDI), UNICEF, and the Kenya Girl Guides "
            "Association launched the BeGreen Africa Design Sprint, a program helping young entrepreneurs move from "
            "early concepts to market-ready solutions."
        ),
        "our_role": (
            "IDI served as the design and innovation partner—applying our design sprint methodology, mentoring "
            "co-creation, and integrating foundational financial literacy."
        ),
        "key_insight": (
            "Rather than relying on theory, entrepreneurs engaged in collective problem-solving, testing assumptions, "
            "sharing peer critiques, and co-evolving stronger solutions together."
        ),
        "problems": [
            {
                "icon": "user",
                "title": "Learning by Doing",
                "description": "Entrepreneurs advanced faster through hands-on sessions and real-world case studies than with theory alone. This experiential learning ensured skills were internalized through action."
            },
            {
                "icon": "chart",
                "title": "Financial Literacy",
                "description": "By integrating early training in financial modeling and budgeting, we reinforced building from the bottom up—ensuring every business had a strong financial backbone."
            },
            {
                "icon": "alert",
                "title": "Collaboration",
                "description": "Regular pitching sessions and peer reviews embedded the principle of co-creation. These moments sharpened ideas, boosted confidence, and highlighted collective intelligence."
            }
        ],
        "approach_steps": [
            {"number": "01", "title": "Scouting & Mobilization", "description": "Identifying and onboarding youth green innovators from 10+ counties across Kenya."},
            {"number": "02", "title": "Experiential Workshops", "description": "Immersive 'learning-by-doing' sessions using real-world green business cases."},
            {"number": "03", "title": "Financial Design", "description": "Co-designing financial models and budgeting frameworks for early-stage ventures."},
            {"number": "04", "title": "Peer Review & Sprints", "description": "Collective pitching, critique loops, and iterations of prototypes."},
            {"number": "05", "title": "Market Connection", "description": "Preparing ventures for ecosystem linkages, funding, and launch."}
        ],
        "output_stats": [
            {"value": "18", "label": "Green ventures launched within 24 months", "image": "images/be_green/img2.webp"},
            {"value": "10+", "label": "Counties represented across Kenya", "image": "images/be_green/img3.webp"},
            {"value": "3", "label": "Core design principles shaped success", "image": "images/be_green/img5.webp"}
        ],
        "measurable_improvements": [
            {"value": "18", "label": "Ventures Launched"},
            {"value": "10+", "label": "Counties Covered"},
            {"value": "3", "label": "Design Principles"}
        ],
        "measuring_success": (
            "With the right tools, collaboration, and design-driven thinking, this new generation "
            "is proving that sustainable business is not just possible, it's already taking shape. "
            "These aren't just good ideas on paper. They're real ventures, built by young people "
            "who understand their communities and are creating solutions that work."
        ),
        "measuring_image": "images/be_green/img1.webp",
        "partners": [
            {"name": "UNICEF", "logo": "images/partners/unicef.webp"},
            {"name": "IDI", "logo": "images/partners/regional-center.webp"}
        ],
        "related": [
            {
                "slug": "transboundary-data-flows-unep-giz-action-lab",
                "title": "Transboundary Data Flows - UNEP, GIZ, Action Lab",
                "category": "DATA GOVERNANCE",
                "image": "images/case-studies/data_flows_main.webp",
            },
            {
                "slug": "spaceai-dairy-digitisation-cooperative-enablement",
                "title": "SpaceAI (Dairy Digitisation & Cooperative Enablement)",
                "category": "AGRITECH",
                "image": "images/case-studies/dairy_digitisation_main.webp",
            }
        ]
    },
}


def _build_default_detail(slug, title, category, challenge, stat_value, stat_label, tags, image, bg_color=None, **kwargs):
    """Build a generic detail page for any slug not in CASE_STUDY_DETAIL_DATA."""
    detail = {
        "slug": slug,
        "title": title,
        "subtitle": f"How IDI Africa tackled {title.lower()} through decision intelligence design",
        "category": category,
        "sector": category.title(),
        "client": "Partner Organisation",
        "timeline": "2023 – 2024",
        "tags": tags,
        "hero_image": image,
        "hero_image2": "images/governance/case2.webp",
        "portrait_image": "images/governance/program_team.webp",
        "overview": (
            f"This case study explores how IDI Africa partnered with local stakeholders to address "
            f"the challenge: {challenge} Through rigorous research, co-design, and "
            "iterative prototyping, we developed a scalable solution that delivered measurable impact "
            "for communities across the region."
        ),
        "key_insight": (
            "The most powerful interventions happen when communities are treated as co-designers, "
            "not beneficiaries. By embedding ourselves in the problem space, we uncovered the "
            "systemic roots of the challenge and built solutions that last."
        ),
        "problems": [
            {"icon": "chart", "title": "Systemic Gap", "description": challenge},
            {"icon": "user", "title": "Limited Access", "description": "Communities lacked access to tools and infrastructure to address the underlying challenge."},
            {"icon": "alert", "title": "Coordination Failure", "description": "Multiple actors worked in silos, preventing coordinated responses that could have amplified impact."},
        ],
        "approach_steps": [
            {"number": "01", "title": "Research & Discovery", "description": "Immersive community research to understand the lived experience of the challenge."},
            {"number": "02", "title": "Co-Design", "description": "Participatory design sessions with community members and key stakeholders."},
            {"number": "03", "title": "Prototype & Test", "description": "Rapid prototyping with real users to validate assumptions before scaling."},
            {"number": "04", "title": "Implementation", "description": "Structured rollout with continuous feedback loops and adaptation."},
            {"number": "05", "title": "Scale & Sustain", "description": "Building local capacity to own, operate, and iterate on the solution independently."},
        ],
        "output_stats": [
            {"value": stat_value, "label": stat_label, "image": image},
            {"value": "3×", "label": "Improvement in service delivery efficiency", "image": "images/governance/case2.webp"},
            {"value": "500+", "label": "Community members directly impacted", "image": "images/governance/case3.webp"},
            {"value": "12", "label": "Partner organisations engaged", "image": "images/community/case1.webp"},
            {"value": "85%", "label": "Satisfaction rate among beneficiaries", "image": "images/community/case2.webp"},
            {"value": "2 yrs", "label": "Sustained operation post-project", "image": "images/community/case3.webp"},
        ],
        "measurable_improvements": [
            {"value": stat_value, "label": stat_label},
            {"value": "3×", "label": "Efficiency Gain"},
            {"value": "Better", "label": "Data Quality"},
            {"value": "100%", "label": "Partner Retention"},
            {"value": "Reduced", "label": "Service Gaps"},
            {"value": "Improved", "label": "Outcomes"},
        ],
        "measuring_success": (
            "Impact was measured through a combination of quantitative metrics—service uptake, "
            "retention rates, and outcome data—and qualitative feedback from community members "
            "and frontline workers. All indicators were defined collaboratively with partners "
            "at the outset of the project."
        ),
        "measuring_image": "images/governance/board2.webp",
        "partners": [
            {"name": "Partner A", "logo": "images/partners/unicef.webp"},
            {"name": "Partner B", "logo": "images/partners/challenge-works.webp"},
            {"name": "Partner C", "logo": "images/partners/regional-center.webp"},
        ],
        "related": [
            {"slug": "power-to-youth", "title": "Power to Youth", "category": "GENDER RIGHTS", "image": "images/power_to_youth/img1.png"},
            {"slug": "transboundary-data-flows-unep-giz-action-lab", "title": "Transboundary Data Flows - UNEP, GIZ, Action Lab", "category": "DATA GOVERNANCE", "image": "images/governance/case2.webp"},
            {"slug": "spaceai-dairy-digitisation-cooperative-enablement", "title": "SpaceAI (Dairy Digitisation & Cooperative Enablement)", "category": "AGRITECH", "image": "images/community/case2.webp"},
        ],
    }
    detail.update(kwargs)
    return detail


def case_study_detail(request, slug):
    if slug == 'kenyas-ai-opportunities-plan-action-lab':
        from django.shortcuts import redirect
        return redirect('home:project_detail', slug='kenyas-ai-opportunities-plan-action-lab')

    detail = CASE_STUDY_DETAIL_DATA.get(slug)

    if detail is None:
        card = next((c for c in CASE_STUDIES if c["slug"] == slug), None)
        if card:
            detail = _build_default_detail(**card)
        else:
            from django.http import Http404
            raise Http404("Case study not found")

    context = {
        'cs': detail,
        'page_title': detail['title'],
        'page_description': detail['overview'][:160],
        'page_keywords': f'{detail["title"]}, Case Study, Decision Intelligence Design, Africa, IDI',
    }
    return render(request, 'home/case_studies_detail.html', context)


# New view for Team page
def team_list(request):
    team_members = TeamMember.objects.select_related().all()
    
    # SEO metadata
    context = {
        'team_members': team_members,
        'page_title': 'Our Team',
        'page_description': 'Meet the passionate innovators, designers, and researchers behind IDI Africa who are driving decision intelligence design across the continent.',
        'page_keywords': 'Team, Decision Intelligence Design, Experts, Leadership, Innovators, Africa, Kenya',
    }
    return render(request, 'home/team/team_list.html', context)
    

class TeamMemberDetailView(DetailView):
    model = TeamMember
    template_name = 'home/team/team_member_detail.html'
    context_object_name = 'member'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = self.get_object()
        
        # Always set single_member to True
        context['single_member'] = True
        
        # SEO metadata
        context['page_title'] = member.name
        context['page_description'] = f'{member.name} - {member.position} at IDI Africa. Learn more about their work in decision intelligence design.'
        context['page_keywords'] = f'Team Member, {member.name}, {member.position}, Decision Intelligence Design, Innovation, Africa, Kenya'
        context['page_image'] = member.image
        
        return context
    



def llms_txt(request):
    """LLM-readable site summary (GEO). Served as text/plain at /llms.txt."""
    return render(request, 'seo/llms.txt',
                  {'base': request.build_absolute_uri('/').rstrip('/')},
                  content_type='text/plain; charset=utf-8')


def custom_page_not_found(request, exception):
    """
    Custom 404 page handler
    """
    context = {
        'page_title': '404 - Page Not Found',
        'page_description': 'The page you were looking for could not be found on IDI Africa.',
        'page_keywords': 'error, 404, page not found, IDI Africa',
    }
    return render(request, '404.html', context, status=404)


def custom_server_error(request):
    """
    Custom 500 page handler
    """
    context = {
        'page_title': '500 - Server Error',
        'page_description': 'We apologize, but something went wrong on our end at IDI Africa.',
        'page_keywords': 'error, 500, server error, IDI Africa',
    }
    return render(request, '404.html', context, status=500)


def custom_permission_denied(request, exception):
    """
    Custom 403 page handler
    """
    context = {
        'page_title': '403 - Permission Denied',
        'page_description': 'You do not have permission to access this page on IDI Africa.',
        'page_keywords': 'error, 403, permission denied, IDI Africa',
    }
    return render(request, '404.html', context, status=403)


def custom_bad_request(request, exception):
    """
    Custom 400 page handler
    """
    context = {
        'page_title': '400 - Bad Request',
        'page_description': 'The request sent to the IDI Africa server was invalid.',
        'page_keywords': 'error, 400, bad request, IDI Africa',
    }
    return render(request, '404.html', context, status=400)


def governance_public_service_delivery(request):
    """
    View for the Governance & Public Service Delivery practice page.
    """
    context = {
        'page_title': 'Governance & Public Service Delivery',
        'page_description': 'Designing systems that govern effectively—and deliver where it matters. IDI Africa works at the intersection of decision intelligence and public service delivery.',
        'page_keywords': 'Governance, Public Service Delivery, Decision Intelligence, System Design, Africa, Innovation',
    }
    return render(request, 'home/governance_public_service_delivery.html', context)


def responsible_sovereign_ai(request):
    """
    View for the Responsible / Sovereign AI practice page.
    """
    context = {
        'page_title': 'Responsible & Sovereign AI',
        'page_description': 'Designing AI systems that are trusted, context-aware, and built for long-term public value. IDI Africa pioneers representational and ethical AI architectures.',
        'page_keywords': 'Sovereign AI, Responsible AI, AI Ethics, Civic Tech, Machine Learning, Africa, Innovation',
    }
    return render(request, 'home/responsible_sovereign_ai.html', context)


def community_public_service_delivery(request):
    """
    View for the Community & Public Service Delivery practice page.
    """
    context = {
        'page_title': 'Community & Public Service Delivery',
        'page_description': 'Designing for relevance. We build frameworks, strategy, and products that respect and reflect community context, knowledge, and sovereignty.',
        'page_keywords': 'Community Service, Public Service Delivery, Participatory Design, Civic Trust, Decision Intelligence, Africa, Innovation',
    }
    return render(request, 'home/community_public_service_delivery.html', context)


def food_systems_health_practice(request):
    """
    View for the Food Systems & Health Practice practice page.
    """
    context = {
        'page_title': 'Food Systems & Health Practice',
        'page_description': 'Designing for relevance. We build frameworks, strategy, and products that respect and reflect community context, knowledge, and sovereignty within food systems.',
        'page_keywords': 'Food Systems, Health Practice, Nutrition, Agricultural Decision Systems, Public Health, Decision Intelligence, Africa, Innovation',
    }
    return render(request, 'home/food_systems_health_practice.html', context)


def reimagining_youth(request):
    """
    View for the Reimagining Youth Opportunity Systems case study page.
    """
    context = {
        'page_title': 'Reimagining Youth Opportunity Systems',
        'page_description': 'A case study on digitizing knowledge economies and civic engagement within government frameworks.',
        'page_keywords': 'Youth Opportunity, Government, Civic Literacy, Decision Intelligence, Case Study',
    }
    return render(request, 'home/projects/reimagining_youth.html', context)


def services(request):
    """
    View for the dedicated Services page.
    """
    service_pillars = ServicePillar.objects.filter(is_active=True)
    
    # SEO metadata
    context = {
        'service_pillars': service_pillars,
        'page_title': 'Services',
        'page_description': 'Decision Intelligence Design for modern structural transitions. Discover our service pillars across Strategy & Design, Insights & Data, and Implementation & Scale.',
        'page_keywords': 'Services, Strategy, Design, Insights, Data, Implementation, Scale, Decision Intelligence, Africa, Innovation',
    }
    return render(request, 'home/services.html', context)


def sustainability_practice(request):
    """
    View for the Health (formerly Sustainability) practice page.
    """
    context = {
        'page_title': 'Health',
        'page_description': 'Designing for health and resilience. We build custom decision intelligence frameworks for healthcare systems across Africa.',
        'page_keywords': 'Health, Decision Intelligence, Healthcare, Africa, Innovation',
    }
    return render(request, 'home/sustainability_practice.html', context)


def venture_building(request):
    """
    View for the Venture Building & Innovation Ecosystems practice page.
    """
    context = {
        'page_title': 'Venture Building & Innovation Ecosystems',
        'page_description': 'Accelerating growth and building robust innovation ecosystems across the African continent.',
        'page_keywords': 'Venture Building, Innovation, Ecosystems, Startups, Scale, Africa',
    }
    return render(request, 'home/venture_building.html', context)


def contact(request):
    """
    View for the dedicated Contact Us page.
    """
    success = False
    if request.method == "POST":
        # Process visual inquiry submission
        success = True
        
    context = {
        'success': success,
        'page_title': 'Contact Us',
        'page_description': 'Get in touch with IDI Africa. Whether you want to partner with us, join our fellowship, or initiate an inquiry, we would love to hear from you.',
        'page_keywords': 'Contact, Inquiry, Partnership, Decision Intelligence, Africa, Kenya, Nairobi',
    }
    return render(request, "home/contact.html", context)