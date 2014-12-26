from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Creates the mapping in the index.'

    def handle(self, *args, **options):
        #TODO: cretate mapping using elasticutils
        pass
