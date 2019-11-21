import datetime
from unittest import skipIf

from django.conf import settings
from django.core.management import call_command
from django.urls import reverse
from django.db.models import signals

import factory

from .test_views import BaseAnnotationViewTests


@skipIf(settings.ES_DISABLED, "Do not test if Elasticsearch service is disabled.")
class UpdateIndexTest(BaseAnnotationViewTests):
    """
    Tests for update index command.
    """

    @factory.django.mute_signals(signals.post_save)
    def test_create(self):
        """
        Ensure we can update index with created notes within specific
        period of time.
        """
        start = datetime.datetime.now()
        self._create_annotation(text=u'First note')

        second_start = datetime.datetime.now()
        self._create_annotation(text=u'Second note')
        second_end = datetime.datetime.now()

        self._create_annotation(text=u'Third note')
        end = datetime.datetime.now()

        results = self._get_search_results(text='note')
        self.assertDictContainsSubset({'rows': [], 'total': 0}, results)

        # When second note was created.
        call_command('update_index', start_date=second_start.isoformat(), end_date=second_end.isoformat(), verbosity=0)
        results = self._get_search_results(text='note')
        self.assertEqual(results['total'], 1)
        self.assertEqual(results['rows'][0]['text'], 'Second note')

        # All notes.
        call_command('update_index', start_date=start.isoformat(), end_date=end.isoformat(), verbosity=0)
        results = self._get_search_results(text='note')
        self.assertEqual(results['total'], 3)

    @factory.django.mute_signals(signals.post_delete)
    def test_delete(self):
        """
        Ensure we can update index with deleted notes.
        """

        first_note = self._create_annotation(text=u'First note')
        second_note = self._create_annotation(text=u'Second note')
        self._create_annotation(text=u'Third note')

        results = self._get_search_results(text='note')
        self.assertEqual(results['total'], 3)

        # Delete first note.
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': first_note['id']})
        response = self.client.delete(url, self.headers)

        # Delete second note.
        second_start = datetime.datetime.now()
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': second_note['id']})
        response = self.client.delete(url, self.headers)
        second_end = datetime.datetime.now() + datetime.timedelta(minutes=10)

        # Try to update when only second note was deleted.
        call_command(
            'update_index', remove=True, start_date=second_start.isoformat(),
            end_date=second_end.isoformat(), verbosity=0
        )
        results = self._get_search_results(text='note')

        # When remove flag is provided, start and end flags do not play any role.
        self.assertEqual(results['total'], 1)
        self.assertEqual(results['rows'][0]['text'], 'Third note')
