from django.core.management.base import BaseCommand
from django.db import transaction
import re

from core.models import ActivityResult

UUID_PATTERN = re.compile(r'(^[0-9a-fA-F]{32}$)|(^[0-9a-fA-F\-]{36}$)')

class Command(BaseCommand):
    help = (
        "Detect and fix malformed UUIDs stored in ActivityResult pid/sid columns.\n"
        "If a pid or sid does not match expected UUID formats it will be set to NULL."
    )

    def handle(self, *args, **options):
        bad_parent = 0
        bad_student = 0
        total = 0

        self.stdout.write("Scanning ActivityResult rows for malformed UUIDs...")

        with transaction.atomic():
            for ar in ActivityResult.objects.all():
                total += 1
                changed = False

                pid = getattr(ar, 'parent_id', None)
                sid = getattr(ar, 'student_id', None)

                if pid and not UUID_PATTERN.match(str(pid)):
                    ar.parent = None
                    bad_parent += 1
                    changed = True

                if sid and not UUID_PATTERN.match(str(sid)):
                    ar.student = None
                    bad_student += 1
                    changed = True

                if changed:
                    ar.save()

        self.stdout.write(self.style.SUCCESS(
            f"Scanned {total} rows — fixed {bad_parent} parent ids and {bad_student} student ids."))
