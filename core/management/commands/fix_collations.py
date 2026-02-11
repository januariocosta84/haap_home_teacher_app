from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = (
        "Detect tables/columns with non-matching collations and convert them."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            default=False,
            help="Print ALTER statements without executing them",
        )
        parser.add_argument(
            "--collation",
            dest="collation",
            default="utf8mb4_general_ci",
            help="Target collation (default: utf8mb4_general_ci)",
        )
        parser.add_argument(
            "--charset",
            dest="charset",
            default="utf8mb4",
            help="Target character set (default: utf8mb4)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        target_collation = options["collation"]
        target_charset = options["charset"]

        db_name = settings.DATABASES["default"]["NAME"]

        self.stdout.write(
            f"Searching schema '{db_name}' for tables/columns not using {target_collation}..."
        )

        with connection.cursor() as cursor:
            # Find tables with a different collation
            cursor.execute(
                """
                SELECT TABLE_NAME, TABLE_COLLATION
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_TYPE = 'BASE TABLE'
                  AND (TABLE_COLLATION IS NULL OR TABLE_COLLATION != %s)
                """,
                [db_name, target_collation],
            )
            tables = cursor.fetchall()

            if not tables:
                self.stdout.write(self.style.SUCCESS("All tables already use the target collation."))
            else:
                for table_name, table_collation in tables:
                    stmt = (
                        f"ALTER TABLE `{table_name}` CONVERT TO CHARACTER SET {target_charset} "
                        f"COLLATE {target_collation};"
                    )
                    if dry_run:
                        self.stdout.write(f"DRY RUN: {stmt}")
                    else:
                        self.stdout.write(f"Executing: {stmt}")
                        try:
                            cursor.execute(stmt)
                        except Exception as exc:
                            self.stderr.write(f"Failed to alter {table_name}: {exc}")

            # Also list character/collation of columns that differ (for visibility)
            cursor.execute(
                """
                SELECT TABLE_NAME, COLUMN_NAME, COLLATION_NAME
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s
                  AND COLLATION_NAME IS NOT NULL
                  AND COLLATION_NAME != %s
                ORDER BY TABLE_NAME
                """,
                [db_name, target_collation],
            )
            cols = cursor.fetchall()

            if cols:
                self.stdout.write("Columns with non-matching collations:")
                for table_name, column_name, coll_name in cols:
                    self.stdout.write(f" - {table_name}.{column_name}: {coll_name}")

        self.stdout.write(self.style.SUCCESS("Done."))
