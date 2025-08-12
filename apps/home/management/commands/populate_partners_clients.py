from django.core.management.base import BaseCommand
from apps.home.models import Partner, Client


class Command(BaseCommand):
    help = 'Populate database with sample partners and clients data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample partners and clients...')
        
        # Sample partners data
        partners_data = [
            {
                'name': 'Microsoft Africa Development Centre',
                'partnership_type': 'technology',
                'website': 'https://www.microsoft.com/africa',
                'description': 'Strategic technology partnership focused on cloud computing and AI solutions for African markets.',
                'is_featured': True,
                'is_active': True,
                'order': 1
            },
            {
                'name': 'African Development Bank',
                'partnership_type': 'funding',
                'website': 'https://www.afdb.org',
                'description': 'Funding partnership supporting digital transformation initiatives across Africa.',
                'is_featured': True,
                'is_active': True,
                'order': 2
            },
            {
                'name': 'University of Cape Town',
                'partnership_type': 'academic',
                'website': 'https://www.uct.ac.za',
                'description': 'Academic collaboration on research and development of innovative digital solutions.',
                'is_featured': True,
                'is_active': True,
                'order': 3
            },
            {
                'name': 'Google for Startups Africa',
                'partnership_type': 'technology',
                'website': 'https://startup.google.com/africa',
                'description': 'Technology partnership providing cloud credits and technical expertise to startups.',
                'is_featured': True,
                'is_active': True,
                'order': 4
            },
            {
                'name': 'World Bank Group',
                'partnership_type': 'funding',
                'website': 'https://www.worldbank.org',
                'description': 'Global partnership for sustainable development and digital transformation.',
                'is_featured': True,
                'is_active': True,
                'order': 5
            },
            {
                'name': 'Accenture Africa',
                'partnership_type': 'implementation',
                'website': 'https://www.accenture.com',
                'description': 'Implementation partnership for enterprise digital transformation projects.',
                'is_featured': False,
                'is_active': True,
                'order': 6
            },
            {
                'name': 'TechCrunch Africa',
                'partnership_type': 'media',
                'website': 'https://techcrunch.com',
                'description': 'Media partnership for technology news and startup ecosystem coverage.',
                'is_featured': False,
                'is_active': True,
                'order': 7
            }
        ]
        
        # Sample clients data
        clients_data = [
            {
                'name': 'Flutterwave',
                'industry': 'fintech',
                'website': 'https://flutterwave.com',
                'project_description': 'Digital payments infrastructure modernization and expansion across 30+ African countries.',
                'collaboration_year': 2024,
                'is_featured': True,
                'is_active': True,
                'order': 1
            },
            {
                'name': 'Helium Health',
                'industry': 'healthcare',
                'website': 'https://heliumhealth.com',
                'project_description': 'Healthcare management system digitization serving over 5,000+ healthcare facilities.',
                'collaboration_year': 2024,
                'is_featured': True,
                'is_active': True,
                'order': 2
            },
            {
                'name': 'uLesson Education',
                'industry': 'education',
                'website': 'https://ulesson.com',
                'project_description': 'EdTech platform development reaching over 1 million students across Africa.',
                'collaboration_year': 2023,
                'is_featured': True,
                'is_active': True,
                'order': 3
            },
            {
                'name': 'Twiga Foods',
                'industry': 'agriculture',
                'website': 'https://twiga.ke',
                'project_description': 'Agricultural supply chain digitization connecting 35,000+ farmers to markets.',
                'collaboration_year': 2024,
                'is_featured': True,
                'is_active': True,
                'order': 4
            },
            {
                'name': 'Kobo360',
                'industry': 'logistics',
                'website': 'https://kobo360.com',
                'project_description': 'Logistics platform optimization serving 10,000+ trucks and 2,000+ businesses.',
                'collaboration_year': 2023,
                'is_featured': True,
                'is_active': True,
                'order': 5
            },
            {
                'name': 'Kenya Ministry of ICT',
                'industry': 'government',
                'website': 'https://www.ict.go.ke',
                'project_description': 'National digital transformation strategy implementation and e-government services.',
                'collaboration_year': 2024,
                'is_featured': False,
                'is_active': True,
                'order': 6
            },
            {
                'name': 'Jumia Technologies',
                'industry': 'retail',
                'website': 'https://group.jumia.com',
                'project_description': 'E-commerce platform enhancement and logistics optimization across 11 African countries.',
                'collaboration_year': 2023,
                'is_featured': False,
                'is_active': True,
                'order': 7
            },
            {
                'name': 'GiveDirectly',
                'industry': 'ngo',
                'website': 'https://www.givedirectly.org',
                'project_description': 'Digital cash transfer platform serving 500,000+ recipients in Kenya and Uganda.',
                'collaboration_year': 2024,
                'is_featured': True,
                'is_active': True,
                'order': 8
            }
        ]
        
        # Create partners
        partners_created = 0
        for partner_data in partners_data:
            partner, created = Partner.objects.get_or_create(
                name=partner_data['name'],
                defaults=partner_data
            )
            
            if created:
                partners_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created partner: {partner.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Partner already exists: {partner.name}')
                )
        
        # Create clients
        clients_created = 0
        for client_data in clients_data:
            client, created = Client.objects.get_or_create(
                name=client_data['name'],
                defaults=client_data
            )
            
            if created:
                clients_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created client: {client.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Client already exists: {client.name}')
                )
        
        # Summary
        featured_partners = Partner.objects.filter(is_featured=True).count()
        featured_clients = Client.objects.filter(is_featured=True).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created {partners_created} new partners and {clients_created} new clients.\n'
                f'Featured partners: {featured_partners}\n'
                f'Featured clients: {featured_clients}'
            )
        )