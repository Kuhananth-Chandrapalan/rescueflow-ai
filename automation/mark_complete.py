import sys
from automation.select_task import mark_complete

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python -m automation.mark_complete <task-id>')
    mark_complete(sys.argv[1])
