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

    def get_model(self):
        return Note

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
