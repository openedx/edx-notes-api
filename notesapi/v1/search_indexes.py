from haystack import indexes

from .models import Note


class NoteIndex(indexes.SearchIndex, indexes.Indexable):
    user = indexes.CharField(model_attr='user_id', indexed=False)
    course_id = indexes.CharField(model_attr='course_id', indexed=False)
    usage_id = indexes.CharField(model_attr='usage_id', indexed=False)
    quote = indexes.CharField(model_attr='quote')
    text = indexes.CharField(document=True, model_attr='text')
    ranges = indexes.CharField(model_attr='ranges', indexed=False)
    created = indexes.DateTimeField(model_attr='created')
    updated = indexes.DateTimeField(model_attr='updated')
    tags = indexes.CharField(model_attr='tags')
    data = indexes.CharField(use_template=True)

    def get_model(self):
        return Note

    def index_queryset(self, using=None):
        """
        Used when the entire index for model is updated.
        """
        return self.get_model().objects.all()

    def get_updated_field(self):
        """
        Get the field name that represents the updated date for the Note model.

        This is used by the reindex command to filter out results from the QuerySet, enabling to reindex only
        recent records. This method returns a string of the Note's field name that contains the date that the model
        was updated.
        """
        return 'updated'
