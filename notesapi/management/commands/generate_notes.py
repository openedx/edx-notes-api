import os
from lxml import etree
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
        note_number = 1
        paragraph_number = 1
        text_file = os.path.dirname(__file__) + "/Latin-Lipsum.html"
        paragraphs = etree.parse(text_file).getroot().getchildren()
        for paragraph in paragraphs:
            for word in self.words(paragraph.text):

                note["text"] = "Text number: {}".format(note_number)
                note["quote"] = word
                end_offset = start_offset + len(word)
                note["ranges"][0]["startOffset"] = start_offset
                note["ranges"][0]["endOffset"] = end_offset
                ranges =  "/div[1]/div[1]/p[{}]".format(paragraph_number)
                note["ranges"][0]["start"] = note["ranges"][0]["end"] = ranges
                annotation = Annotation(note)
                annotation.save(refresh=False)
                start_offset = end_offset + 1
                note_number += 1

            paragraph_number +=1

        es.conn.indices.refresh(es.index)

    def words(self, text):
            for word in text.split():
                yield word

