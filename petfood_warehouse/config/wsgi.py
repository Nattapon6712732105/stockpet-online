import os
import sys
from pathlib import Path
from django.core.wsgi import get_wsgi_application

# Ensure project directory is in python path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()

# On Vercel without an external DATABASE_URL, initialize /tmp/db.sqlite3 on startup
if os.environ.get('VERCEL') and not os.environ.get('DATABASE_URL'):
    db_file = Path('/tmp/db.sqlite3')
    if not db_file.exists():
        from django.core.management import call_command
        try:
            call_command('migrate', interactive=False)
            call_command('seed_demo')
        except Exception as e:
            print("Auto-migration in /tmp error:", e)

app = application
