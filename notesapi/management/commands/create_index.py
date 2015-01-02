from optparse import make_option
from django.conf import settings
from django.core.management.base import BaseCommand
from elasticutils.contrib.django import get_es
from notesapi.v1.models import NoteMappingType


class Command(BaseCommand):
    """
    Indexing and mapping commands.
    """
    help = 'Creates index and the mapping.'
    option_list = BaseCommand.option_list + (
        make_option(
            '--drop',
            action='store_true',
            dest='drop',
            default=False,
            help='Recreate index'
        ),
    )

    def handle(self, *args, **options):
        if options['drop']:
            # drop existing
            get_es().indices.delete(index=settings.ES_INDEXES['default'])

        get_es().indices.create(
            index=settings.ES_INDEXES['default'],
            body={
                'mappings': {
                    NoteMappingType.get_mapping_type_name(): NoteMappingType.get_mapping()
                }
            },
        )
