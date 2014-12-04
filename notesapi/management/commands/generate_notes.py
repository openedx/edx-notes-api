import os
from django.core.management.base import BaseCommand
from annotator.annotation import Annotation
from annotator import es


class Command(BaseCommand):
    args = '<user usage_id course_id>'
    help = 'Creates notes in the index.'

    def handle(self, *args, **options):

        note = {
            "user": "staff",
            "usage_id": "i4x://testorg/num1/html/52aa9816425a4ce98a07625b8cb70811",
            "course_id": "testorg/num1/2014",
            "text": "Text number: 1.",
            "quote": "quote",
            "ranges": [
                {
                    "start": "/div[1]/div[1]/p[1]",
                    "end": "/div[1]/div[1]/p[1]",
                    "startOffset": 0,
                    "endOffset": 10,
                }
            ],
        }

        note.update({
            "user": args[0],
            "usage_id": args[1],
            "course_id": args[2]
        })

        start_offset = 0
        number = 1
        text_file = os.path.dirname(__file__) + "/text.txt"
        with open(text_file, 'r') as text:
            for word in self.words(text):
                note["text"] = "Text number: {}".format(number)
                note["quote"] = word
                end_offset = start_offset + len(word)
                note["ranges"][0]["startOffset"] = start_offset
                note["ranges"][0]["endOffset"] = end_offset
                annotation = Annotation(note)
                annotation.save(refresh=False)
                start_offset = end_offset + 1
                number += 1

        es.conn.indices.refresh(es.index)

    def words(self, text):
        for line in text:
            for word in line.split():
                yield word

