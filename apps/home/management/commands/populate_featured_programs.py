from django.core.management.base import BaseCommand
from apps.home.models import Program
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Populate database with sample featured programs data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample featured programs...')
        
        # Sample program data
        programs_data = [
            {
                'title': 'Digital Innovation Fellowship 2025',
                'program_type': 'fellowship',
                'short_description': 'An intensive 12-week program designed to accelerate digital transformation skills for emerging leaders in Africa.',
                'full_description': '<p>Join our flagship Digital Innovation Fellowship, where you\'ll work on real-world projects, learn cutting-edge technologies, and build solutions that matter. This program combines hands-on experience with mentorship from industry leaders.</p><ul><li>Weekly workshops with tech leaders</li><li>1-on-1 mentorship sessions</li><li>Capstone project presentation</li><li>Networking with alumni network</li></ul>',
                'duration': '12 weeks',
                'format': 'Hybrid (Online + In-person)',
                'target_audience': 'Early-career professionals, recent graduates, and career changers looking to enter the tech industry',
                'application_url': 'https://apply.idi.org/fellowship',
                'learn_more_url': 'https://idi.org/programs/fellowship',
                'is_featured': True,
                'application_open': True,
                'application_deadline': datetime.now() + timedelta(days=30),
                'year': 2025,
                'meta_description': 'Join the Digital Innovation Fellowship 2025 - a 12-week intensive program for emerging tech leaders in Africa.',
                'meta_keywords': 'fellowship, digital innovation, tech leadership, Africa',
                'order': 1
            },
            {
                'title': 'Executive Digital Leadership Program',
                'program_type': 'executive',
                'short_description': 'Strategic digital transformation program for senior executives and C-level leaders.',
                'full_description': '<p>Transform your organization\'s digital strategy with our Executive Digital Leadership Program. Learn from case studies, engage with peers, and develop actionable digital transformation roadmaps.</p><h3>Program Highlights:</h3><ul><li>Digital Strategy Frameworks</li><li>Change Management in Digital Age</li><li>Data-Driven Decision Making</li><li>Innovation Leadership</li></ul>',
                'duration': '6 weeks',
                'format': 'Executive Retreats + Virtual Sessions',
                'target_audience': 'C-level executives, senior managers, and business leaders driving digital transformation',
                'application_url': 'https://apply.idi.org/executive',
                'learn_more_url': 'https://idi.org/programs/executive',
                'is_featured': True,
                'application_open': True,
                'application_deadline': datetime.now() + timedelta(days=45),
                'year': 2025,
                'meta_description': 'Executive Digital Leadership Program for senior leaders driving digital transformation.',
                'meta_keywords': 'executive program, digital leadership, transformation, strategy',
                'order': 2
            },
            {
                'title': 'Data Science Bootcamp',
                'program_type': 'bootcamp',
                'short_description': 'Intensive hands-on bootcamp covering Python, machine learning, and data visualization.',
                'full_description': '<p>Master data science fundamentals in this intensive bootcamp. From Python programming to advanced machine learning, you\'ll build practical skills through real-world projects.</p><h3>Curriculum:</h3><ul><li>Python for Data Science</li><li>Statistical Analysis & Modeling</li><li>Machine Learning Algorithms</li><li>Data Visualization with Tableau & PowerBI</li><li>SQL & Database Management</li></ul>',
                'duration': '8 weeks',
                'format': 'Online with Live Sessions',
                'target_audience': 'Professionals looking to transition into data science, analysts wanting to upskill',
                'application_url': 'https://apply.idi.org/bootcamp',
                'learn_more_url': 'https://idi.org/programs/bootcamp',
                'is_featured': True,
                'application_open': True,
                'application_deadline': datetime.now() + timedelta(days=20),
                'year': 2025,
                'meta_description': 'Intensive 8-week Data Science Bootcamp covering Python, ML, and data visualization.',
                'meta_keywords': 'data science, bootcamp, python, machine learning, analytics',
                'order': 3
            },
            {
                'title': 'AI Ethics & Governance Workshop',
                'program_type': 'workshop',
                'short_description': 'Explore ethical considerations and governance frameworks for AI implementation.',
                'full_description': '<p>Navigate the complex landscape of AI ethics and governance. This workshop provides frameworks for responsible AI development and implementation in organizations.</p><h3>Key Topics:</h3><ul><li>AI Bias Detection & Mitigation</li><li>Privacy & Data Protection</li><li>Regulatory Compliance</li><li>Stakeholder Engagement</li></ul>',
                'duration': '2 days',
                'format': 'In-person Workshop',
                'target_audience': 'AI practitioners, compliance officers, business leaders implementing AI solutions',
                'application_url': 'https://apply.idi.org/ai-ethics',
                'learn_more_url': 'https://idi.org/programs/ai-ethics',
                'is_featured': True,
                'application_open': True,
                'application_deadline': datetime.now() + timedelta(days=15),
                'year': 2025,
                'meta_description': '2-day workshop on AI ethics and governance frameworks for responsible AI implementation.',
                'meta_keywords': 'AI ethics, governance, responsible AI, compliance',
                'order': 4
            },
            {
                'title': 'Cybersecurity Fundamentals Course',
                'program_type': 'course',
                'short_description': 'Comprehensive course covering cybersecurity basics for non-technical professionals.',
                'full_description': '<p>Build essential cybersecurity knowledge to protect your organization. This course covers threat landscape, risk assessment, and security best practices for business professionals.</p><h3>Learning Outcomes:</h3><ul><li>Threat Identification & Assessment</li><li>Security Policy Development</li><li>Incident Response Planning</li><li>Employee Security Training</li></ul>',
                'duration': '4 weeks',
                'format': 'Self-paced Online',
                'target_audience': 'Business professionals, managers, and non-technical staff responsible for security decisions',
                'application_url': 'https://apply.idi.org/cybersecurity',
                'learn_more_url': 'https://idi.org/programs/cybersecurity',
                'is_featured': True,
                'application_open': True,
                'application_deadline': datetime.now() + timedelta(days=60),
                'year': 2025,
                'meta_description': '4-week cybersecurity fundamentals course for business professionals.',
                'meta_keywords': 'cybersecurity, security training, risk management, business security',
                'order': 5
            },
            {
                'title': 'Blockchain for Business Leaders',
                'program_type': 'course',
                'short_description': 'Understanding blockchain technology and its business applications without the technical jargon.',
                'full_description': '<p>Demystify blockchain technology for business applications. Learn how blockchain can transform industries, from supply chain to finance, with real-world case studies and practical implementation strategies.</p><h3>Course Modules:</h3><ul><li>Blockchain Fundamentals</li><li>Cryptocurrency & Digital Assets</li><li>Smart Contracts</li><li>Industry Use Cases</li><li>Implementation Roadmap</li></ul>',
                'duration': '3 weeks',
                'format': 'Online with Q&A Sessions',
                'target_audience': 'Business leaders, entrepreneurs, and decision-makers exploring blockchain adoption',
                'application_url': 'https://apply.idi.org/blockchain',
                'learn_more_url': 'https://idi.org/programs/blockchain',
                'is_featured': False,  # This one won't be featured
                'application_open': True,
                'application_deadline': datetime.now() + timedelta(days=25),
                'year': 2025,
                'meta_description': '3-week blockchain course for business leaders and decision-makers.',
                'meta_keywords': 'blockchain, business applications, cryptocurrency, smart contracts',
                'order': 6
            }
        ]
        
        created_count = 0
        for program_data in programs_data:
            program, created = Program.objects.get_or_create(
                title=program_data['title'],
                defaults=program_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created program: {program.title}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Program already exists: {program.title}')
                )
        
        featured_count = Program.objects.filter(is_featured=True).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created {created_count} new programs. '
                f'Total featured programs: {featured_count}'
            )
        )