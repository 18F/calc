from textwrap import dedent, fill
from django.core.management.base import BaseCommand

from contracts.reports import dupes


class Command(BaseCommand):
    help = '''
    Generate a report on the quality of CALC's data.
    '''

    def report(self, msg: str):
        self.stdout.write(fill(dedent(msg)))

    def handle(self, *args, **kwargs):
        self.report(f'''\
            There are {dupes.count_duplicates()} labor rates
            that share the same core fields
            ({', '.join(dupes.CORE_FIELDS)}) but
            differ along other axes.
        ''')
