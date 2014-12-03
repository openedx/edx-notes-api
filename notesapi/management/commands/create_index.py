from django.core.management.base import BaseCommand
from annotator.annotation import Annotation


class Command(BaseCommand):
    help = 'Creates the mapping in the index.'

    def handle(self, *args, **options):
        Annotation.create_all()
