from django.core.management.base import BaseCommand
from apps.home.models import Project, TeamMember, Program, Partner, Client, Testimonial
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Create dummy data for testing the website'

    def handle(self, *args, **options):
        self.stdout.write("Creating dummy data...")
        
        # Create dummy projects
        projects_data = [
            {
                'title': 'Digital Innovation for African Healthcare',
                'content': '<p>A comprehensive project focused on leveraging digital technologies to improve healthcare delivery across African communities. This initiative combines design thinking with cutting-edge technology to address critical health challenges.</p><p>Key outcomes include improved patient care systems and enhanced healthcare accessibility.</p>',
                'is_active': True,
            },
            {
                'title': 'Sustainable Urban Planning Initiative',
                'content': '<p>This project explores innovative approaches to urban development that prioritize sustainability and community engagement. Through collaborative design processes, we developed solutions that balance economic growth with environmental stewardship.</p>',
                'is_active': True,
            },
            {
                'title': 'Youth Entrepreneurship Empowerment',
                'content': '<p>A transformative program designed to equip young entrepreneurs with the skills, knowledge, and networks needed to launch successful ventures. This initiative focuses on creating sustainable economic opportunities for African youth.</p>',
                'is_active': True,
            },
        ]
        
        for project_data in projects_data:
            project, created = Project.objects.get_or_create(
                title=project_data['title'],
                defaults={
                    'content': project_data['content'],
                    'is_active': project_data['is_active'],
                    'slug': slugify(project_data['title'])
                }
            )
            if created:
                self.stdout.write(f"✓ Created project: {project.title}")
            else:
                self.stdout.write(f"- Project already exists: {project.title}")
        
        # Create dummy team members
        team_data = [
            {
                'name': 'Dr. Amina Hassan',
                'position': 'Director of Innovation',
                'bio': '<p>Dr. Amina Hassan is a visionary leader in design thinking and social innovation with over 15 years of experience driving transformative change across Africa. She holds a PhD in Design Strategy from Stanford University and has led numerous successful initiatives in healthcare, education, and sustainable development.</p><p>Her work focuses on creating human-centered solutions that address complex societal challenges while building local capacity for long-term impact.</p>',
            },
            {
                'name': 'James Ochieng',
                'position': 'Senior Design Researcher',
                'bio': '<p>James brings a unique blend of anthropological insight and design expertise to our team. With a Master\'s degree in Human-Computer Interaction, he specializes in understanding user needs and translating them into innovative solutions.</p><p>His research has been instrumental in shaping community-centered approaches to technology adoption across rural and urban contexts.</p>',
            },
            {
                'name': 'Fatima Al-Zahra',
                'position': 'Data Analytics Lead',
                'bio': '<p>Fatima is our data science expert, combining advanced analytics with deep understanding of African contexts. She holds an MSc in Data Science and has extensive experience in machine learning applications for social impact.</p><p>Her work focuses on developing ethical AI solutions that empower communities and inform evidence-based decision making.</p>',
            },
            {
                'name': 'Michael Wanjiku',
                'position': 'Community Engagement Specialist',
                'bio': '<p>Michael is passionate about building bridges between communities and innovation initiatives. With a background in sociology and community development, he ensures our projects are grounded in local realities and priorities.</p><p>His collaborative approach has been key to the success of numerous participatory design processes across Kenya and beyond.</p>',
            },
        ]
        
        for member_data in team_data:
            member, created = TeamMember.objects.get_or_create(
                name=member_data['name'],
                defaults={
                    'position': member_data['position'],
                    'bio': member_data['bio'],
                    'slug': slugify(member_data['name'])
                }
            )
            if created:
                self.stdout.write(f"✓ Created team member: {member.name}")
            else:
                self.stdout.write(f"- Team member already exists: {member.name}")
        
        # Create dummy programs
        programs_data = [
            {
                'title': 'Executive Leadership in AI Governance',
                'program_type': 'executive',
                'short_description': 'A comprehensive program for senior leaders to navigate AI implementation with ethical frameworks and strategic foresight.',
                'full_description': '<p>This intensive executive program equips senior leaders with the knowledge and frameworks needed to responsibly implement AI technologies within their organizations. Through case studies, workshops, and peer learning, participants develop strategic approaches to AI governance.</p><p>Key topics include ethical AI adoption, risk management, organizational change management, and building AI-ready cultures.</p>',
                'duration': '8 weeks',
                'format': 'Hybrid',
                'target_audience': 'C-suite executives, senior managers, board members',
                'year': 2025,
                'is_active': True,
                'is_featured': True,
                'application_open': True,
            },
            {
                'title': 'Design Thinking for Social Innovation',
                'program_type': 'bootcamp',
                'short_description': 'An intensive bootcamp for emerging professionals to master human-centered design approaches for social impact.',
                'full_description': '<p>This hands-on bootcamp introduces participants to design thinking methodologies specifically adapted for social innovation challenges. Through real-world projects and mentorship, participants develop skills in user research, ideation, prototyping, and implementation.</p><p>The program emphasizes collaborative problem-solving and sustainable solution development.</p>',
                'duration': '6 weeks',
                'format': 'In-person',
                'target_audience': 'Early-career professionals, social entrepreneurs, NGO staff',
                'year': 2025,
                'is_active': True,
                'is_featured': True,
                'application_open': True,
            },
            {
                'title': 'Data-Driven Decision Making Masterclass',
                'program_type': 'course',
                'short_description': 'Learn to harness the power of data and analytics to drive informed decision-making in complex environments.',
                'full_description': '<p>This masterclass provides practical skills in data analysis, visualization, and interpretation for decision-makers across sectors. Participants learn to identify relevant data sources, apply analytical frameworks, and communicate insights effectively.</p><p>The course combines technical training with strategic thinking to enhance data literacy and decision quality.</p>',
                'duration': '4 weeks',
                'format': 'Online',
                'target_audience': 'Mid-level managers, analysts, program coordinators',
                'year': 2025,
                'is_active': True,
                'is_featured': True,
                'application_open': True,
            },
        ]
        
        for program_data in programs_data:
            program, created = Program.objects.get_or_create(
                title=program_data['title'],
                defaults={
                    'program_type': program_data['program_type'],
                    'short_description': program_data['short_description'],
                    'full_description': program_data['full_description'],
                    'duration': program_data['duration'],
                    'format': program_data['format'],
                    'target_audience': program_data['target_audience'],
                    'year': program_data['year'],
                    'is_active': program_data['is_active'],
                    'is_featured': program_data['is_featured'],
                    'application_open': program_data['application_open'],
                    'slug': slugify(program_data['title'])
                }
            )
            if created:
                self.stdout.write(f"✓ Created program: {program.title}")
            else:
                self.stdout.write(f"- Program already exists: {program.title}")
        
        # Create dummy partners
        partners_data = [
            {
                'name': 'African Development Bank',
                'partnership_type': 'funding',
                'description': 'Strategic funding partner supporting innovative development initiatives across Africa.',
                'is_active': True,
                'is_featured': True,
            },
            {
                'name': 'University of Cape Town',
                'partnership_type': 'academic',
                'description': 'Academic collaboration focused on research and knowledge sharing in design innovation.',
                'is_active': True,
                'is_featured': True,
            },
            {
                'name': 'Microsoft Africa',
                'partnership_type': 'technology',
                'description': 'Technology partner providing platforms and tools for digital innovation projects.',
                'is_active': True,
                'is_featured': True,
            },
            {
                'name': 'UNICEF Innovation Office',
                'partnership_type': 'implementation',
                'description': 'Implementation partner for youth-focused innovation and development programs.',
                'is_active': True,
                'is_featured': True,
            },
        ]
        
        for partner_data in partners_data:
            partner, created = Partner.objects.get_or_create(
                name=partner_data['name'],
                defaults={
                    'partnership_type': partner_data['partnership_type'],
                    'description': partner_data['description'],
                    'is_active': partner_data['is_active'],
                    'is_featured': partner_data['is_featured'],
                }
            )
            if created:
                self.stdout.write(f"✓ Created partner: {partner.name}")
            else:
                self.stdout.write(f"- Partner already exists: {partner.name}")
        
        # Create dummy clients
        clients_data = [
            {
                'name': 'Kenya Ministry of Health',
                'industry': 'government',
                'project_description': 'Digital health systems transformation and capacity building initiative.',
                'collaboration_year': 2024,
                'is_active': True,
                'is_featured': True,
            },
            {
                'name': 'Safaricom Foundation',
                'industry': 'fintech',
                'project_description': 'Community empowerment through digital literacy and entrepreneurship programs.',
                'collaboration_year': 2024,
                'is_active': True,
                'is_featured': True,
            },
            {
                'name': 'East African Community',
                'industry': 'government',
                'project_description': 'Regional integration through harmonized innovation policies and frameworks.',
                'collaboration_year': 2023,
                'is_active': True,
                'is_featured': True,
            },
        ]
        
        for client_data in clients_data:
            client, created = Client.objects.get_or_create(
                name=client_data['name'],
                defaults={
                    'industry': client_data['industry'],
                    'project_description': client_data['project_description'],
                    'collaboration_year': client_data['collaboration_year'],
                    'is_active': client_data['is_active'],
                    'is_featured': client_data['is_featured'],
                }
            )
            if created:
                self.stdout.write(f"✓ Created client: {client.name}")
            else:
                self.stdout.write(f"- Client already exists: {client.name}")
        
        # Create dummy testimonials
        testimonials_data = [
            {
                'name': 'Dr. Sarah Kimani',
                'position': 'Director of Innovation',
                'company': 'Kenya Medical Research Institute',
                'content': 'Working with IDI has transformed our approach to healthcare innovation. Their design thinking methodology helped us develop solutions that truly meet the needs of our communities.',
                'is_active': True,
            },
            {
                'name': 'Ahmed Hassan',
                'position': 'Social Entrepreneur',
                'company': 'EcoSolutions Kenya',
                'content': 'The executive program at IDI provided invaluable insights into responsible AI implementation. The frameworks we learned have been instrumental in scaling our environmental monitoring platform.',
                'is_active': True,
            },
        ]
        
        for testimonial_data in testimonials_data:
            testimonial, created = Testimonial.objects.get_or_create(
                name=testimonial_data['name'],
                company=testimonial_data['company'],
                defaults={
                    'position': testimonial_data['position'],
                    'content': testimonial_data['content'],
                    'is_active': testimonial_data['is_active'],
                }
            )
            if created:
                self.stdout.write(f"✓ Created testimonial: {testimonial.name}")
            else:
                self.stdout.write(f"- Testimonial already exists: {testimonial.name}")
        
        self.stdout.write("\n✅ Dummy data creation completed successfully!")
        self.stdout.write(f"Total Projects: {Project.objects.count()}")
        self.stdout.write(f"Total Team Members: {TeamMember.objects.count()}")
        self.stdout.write(f"Total Programs: {Program.objects.count()}")
        self.stdout.write(f"Total Partners: {Partner.objects.count()}")
        self.stdout.write(f"Total Clients: {Client.objects.count()}")
        self.stdout.write(f"Total Testimonials: {Testimonial.objects.count()}")