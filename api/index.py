import os
import sys
from pathlib import Path

# Add petfood_warehouse to sys.path so config and apps can be imported
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent / 'petfood_warehouse'

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application

django_app = get_wsgi_application()


class VercelPathFixMiddleware:
    """
    แก้ไข PATH_INFO เมื่อรันบน Vercel Serverless Function
    เนื่องจาก Vercel rewrite จะส่ง PATH_INFO เป็นชื่อฟังก์ชัน (/api/index)
    ทำให้ Django หา path ใน urls.py ไม่เจอ (Not Found 404)
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # ดึง original path จาก Vercel headers หรือ REQUEST_URI
        request_uri = (
            environ.get('HTTP_X_NOW_PATHNAME')
            or environ.get('REQUEST_URI')
            or environ.get('RAW_URI')
            or ''
        )
        if request_uri:
            clean_path = request_uri.split('?')[0]
            if clean_path:
                environ['PATH_INFO'] = clean_path
        elif environ.get('PATH_INFO', '').startswith('/api/index'):
            environ['PATH_INFO'] = '/'

        return self.wsgi_app(environ, start_response)


app = VercelPathFixMiddleware(django_app)
handler = app
