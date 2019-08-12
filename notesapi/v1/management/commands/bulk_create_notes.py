import itertools
import json
import os
import random
import uuid
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from notesapi.v1.models import Note


def extract_comma_separated_list(option, opt_str, value, parser):
    """Parse an option string as a comma separated list"""
    setattr(parser.values, option.dest, [course_id.strip() for course_id in value.split(',')])


class Command(BaseCommand):
    args = '<total_notes>'
    def add_arguments(self, parser):
        parser.add_argument(
        '--per_user',
            action='store',
            type='int',
            default=50,
            help='number of notes that should be attributed to each user (default 50)'
        ),
        parser.add_argument(
            '--course_ids',
            action='callback',
            callback=extract_comma_separated_list,
            type='string',
            default=['edX/DemoX/Demo_Course'],
            help='comma-separated list of course_ids for which notes should be randomly attributed'
        ),
        parser.add_argument(
            '--batch_size',
            action='store',
            type='int',
            default=1000,
            help='number of notes that should be bulk inserted at a time - useful for getting around the maximum SQL '
                 'query size'
        )
    help = 'Add N random notes to the database'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("bulk_create_notes takes the following arguments: " + self.args)

        total_notes = int(args[0])
        notes_per_user = options['per_user']
        course_ids = options['course_ids']
        batch_size = options['batch_size']

        # In production, there is a max SQL query size.  Batch the bulk inserts
        # such that we don't exceed this limit.
        for notes_chunk in grouper_it(note_iter(total_notes, notes_per_user, course_ids), batch_size):
            Note.objects.bulk_create(notes_chunk)

def note_iter(total_notes, notes_per_user, course_ids):
    """
    Return an iterable of random notes data of length `total_notes`.

    Arguments:
        total_notes (int): total number of notes models to yield
        notes_per_user (int): number of notes to attribute to any one user
        course_ids (list): list of course_id strings to which notes will be
            randomly attributed

    Returns:
        generator: An iterable of note models.
    """
    DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "data/")
    with open(os.path.join(DATA_DIRECTORY, 'basic_words.txt')) as f:
        notes_text = [word for line in f for word in line.split()]

    def weighted_get_words(weighted_num_words):
        """
        Return random words of of a length of weighted probability.
        `weighted_num_words` should look like [(word_count, weight), (word_count, weight) ...]
        """
        return random.sample(
            notes_text,
            random.choice([word_count for word_count, weight in weighted_num_words for i in range(weight)])
        )

    get_new_user_id = lambda: uuid.uuid4().hex
    user_id = get_new_user_id()

    for note_count in range(total_notes):
        if note_count % notes_per_user == 0:
            user_id = get_new_user_id()
        # Notice that quote and ranges are arbitrary
        yield Note(
            user_id=user_id,
            course_id=random.choice(course_ids),
            usage_id=uuid.uuid4().hex,
            quote='foo bar baz',
            text=' '.join(weighted_get_words([(10, 5), (25, 3), (100, 2)])),
            ranges=json.dumps([{"start": "/div[1]/p[1]", "end": "/div[1]/p[1]", "startOffset": 0, "endOffset": 6}]),
            tags=json.dumps(weighted_get_words([(1, 40), (2, 30), (5, 15), (10, 10), (15, 5)]))
        )


def grouper_it(iterable, batch_size):
    """
    Return an iterator of iterators.  Each child iterator yields the
    next `batch_size`-many elements from `iterable`.
    """
    iterator = iter(iterable)
    while True:
        chunk_it = itertools.islice(iterable, batch_size)
        try:
            first_el = next(chunk_it)
        except StopIteration:
            break
        yield itertools.chain((first_el,), chunk_it)
