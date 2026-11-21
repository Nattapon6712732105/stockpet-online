#!/usr/bin/env python
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "ไม่สามารถ import Django ได้ ตรวจสอบว่าได้ติดตั้ง Django และ activate virtual environment แล้วหรือยัง"
        ) from exc
    execute_from_command_line(sys.argv)
