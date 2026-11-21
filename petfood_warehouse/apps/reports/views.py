from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
import csv
import io

from apps.inventory.models import StockMovement, CentralStock
from apps.requisitions.models import RequisitionRequest


def admin_required(view_func):
    from functools import wraps

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def reports_home(request):
    return render(request, 'reports/home.html')


@admin_required
def export_movements_csv(request):
    """ส่งออกประวัติสต็อกเป็น CSV"""
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="stock_movements.csv"'

    writer = csv.writer(response)
    writer.writerow(['วันที่', 'สินค้า', 'ประเภท', 'จำนวน', 'คงเหลือหลัง', 'คำร้อง', 'โดย', 'หมายเหตุ'])

    movements = StockMovement.objects.select_related(
        'product', 'by_user', 'request'
    ).order_by('-created_at')[:5000]

    for m in movements:
        from apps.inventory.templatetags.thai_date import to_thai_date
        writer.writerow([
            m.created_at.strftime('%Y-%m-%d %H:%M'),
            m.product.name,
            m.get_movement_type_display(),
            m.qty_change,
            m.balance_after,
            m.request.code if m.request else '',
            m.by_user.get_full_name() or m.by_user.username,
            m.note,
        ])

    return response
