from django import template

register = template.Library()


@register.filter
def to_thai_date(dt):
    """แปลง datetime เป็น วันที่ เดือน ปีพ.ศ."""
    if not dt:
        return ''
    months_th = [
        '', 'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
        'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'
    ]
    year_be = dt.year + 543
    return f'{dt.day} {months_th[dt.month]} {year_be}'
