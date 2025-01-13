# accounts/management/commands/init_law_data.py
from django.core.management.base import BaseCommand
from accounts.models import LawSection # type: ignore
class Command(BaseCommand):
    help = 'Initialize basic law section data'

    def handle(self, *args, **kwargs):
        # Check if the section already exists
        if not LawSection.objects.filter(section_number="302", act_name="IPC").exists():
            LawSection.objects.create(
                section_number="302",
                act_name="IPC",
                description="Punishment for murder",
                keywords="murder, kill, death, killed, intentional death",
                punishment="Punishment for murder is life imprisonment or death and fine"
            )
            self.stdout.write(self.style.SUCCESS('Successfully created initial law section'))
        else:
            self.stdout.write(self.style.SUCCESS('Law section already exists'))