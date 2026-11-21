from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django_htmx.http import trigger_client_event

from .models import Product, CentralStock, StockMovement, Category
from apps.requisitions.services import receive_stock


def admin_required(view_func):
    """Decorator ตรวจสิทธิ์ admin"""
    from functools import wraps
    from django.core.exceptions import PermissionDenied

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def product_list(request):
    """รายการสินค้าในคลังกลาง"""
    q = request.GET.get('q', '')
    cat_id = request.GET.get('cat', '')
    status_filter = request.GET.get('status', '')

    stocks = CentralStock.objects.select_related('product', 'product__category').filter(
        product__is_active=True
    )

    if q:
        stocks = stocks.filter(
            Q(product__name__icontains=q) | Q(product__sku__icontains=q)
        )
    if cat_id:
        stocks = stocks.filter(product__category_id=cat_id)

    # กรองสถานะ
    all_stocks = list(stocks.order_by('product__category__name', 'product__name'))
    if status_filter == 'EMPTY':
        all_stocks = [s for s in all_stocks if s.quantity == 0]
    elif status_filter == 'WARN':
        all_stocks = [s for s in all_stocks if 0 < s.quantity <= s.product.min_stock]
    elif status_filter == 'OK':
        all_stocks = [s for s in all_stocks if s.quantity > s.product.min_stock]

    categories = Category.objects.all()
    context = {
        'stocks': all_stocks,
        'categories': categories,
        'q': q,
        'cat_id': cat_id,
        'status_filter': status_filter,
    }

    if request.htmx:
        return render(request, 'inventory/partials/stock_table.html', context)
    return render(request, 'inventory/product_list.html', context)


@admin_required
def receive_stock_view(request):
    """รับสินค้าเข้าคลังกลาง"""
    products = Product.objects.filter(is_active=True).select_related('central_stock', 'category')

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = request.POST.get('quantity', 0)
        note = request.POST.get('note', '')
        try:
            stock = receive_stock(int(product_id), int(quantity), request.user, note)
            messages.success(
                request,
                f'รับ {stock.product.name} เข้าคลังแล้ว {quantity} {stock.product.unit} '
                f'(คงเหลือ {stock.quantity} {stock.product.unit})'
            )
            return redirect('inventory:receive_stock')
        except Exception as e:
            messages.error(request, str(e))

    return render(request, 'inventory/receive_stock.html', {'products': products})


@admin_required
def issue_stock_view(request):
    """ตัดจ่ายสินค้าออกจากคลังกลางโดยตรง (admin)"""
    products = Product.objects.filter(is_active=True).select_related('central_stock', 'category')

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = request.POST.get('quantity', 0)
        reason = request.POST.get('reason', '').strip()
        note = request.POST.get('note', '').strip()

        full_note = f'[{reason}] {note}' if reason else note

        try:
            from apps.requisitions.services import issue_stock
            stock = issue_stock(int(product_id), int(quantity), request.user, full_note)
            messages.success(
                request,
                f'ตัดจ่าย {stock.product.name} ออกจากคลังแล้ว {quantity} {stock.product.unit} '
                f'(คงเหลือ {stock.quantity} {stock.product.unit})'
            )
            return redirect('inventory:issue_stock')
        except Exception as e:
            messages.error(request, str(e))

    return render(request, 'inventory/issue_stock.html', {'products': products})


@admin_required
def stock_movement_list(request):
    """ประวัติการเคลื่อนไหวสต็อก"""
    movements = StockMovement.objects.select_related(
        'product', 'by_user', 'request', 'request__branch'
    ).order_by('-created_at')

    # กรอง
    q = request.GET.get('q', '')
    mtype = request.GET.get('type', '')
    if q:
        movements = movements.filter(
            Q(product__name__icontains=q) | Q(request__code__icontains=q)
        )
    if mtype:
        movements = movements.filter(movement_type=mtype)

    context = {
        'movements': movements[:200],
        'q': q,
        'mtype': mtype,
        'movement_types': StockMovement.MovementType.choices,
    }
    return render(request, 'inventory/movement_list.html', context)


@admin_required
def product_manage(request):
    """จัดการสินค้า (เพิ่ม/แก้ไข)"""
    products = Product.objects.select_related('category', 'central_stock').filter(is_active=True)
    categories = Category.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            sku = request.POST.get('sku', '').strip()
            name = request.POST.get('name', '').strip()
            cat_id = request.POST.get('category')
            unit = request.POST.get('unit', '').strip()
            min_stock = int(request.POST.get('min_stock', 0))
            try:
                cat = Category.objects.get(pk=cat_id)
                product = Product.objects.create(
                    sku=sku, name=name, category=cat, unit=unit, min_stock=min_stock
                )
                CentralStock.objects.create(product=product, quantity=0)
                messages.success(request, f'เพิ่มสินค้า "{name}" เรียบร้อยแล้ว')
            except Exception as e:
                messages.error(request, f'เกิดข้อผิดพลาด: {e}')
        elif action == 'add_category':
            cat_name = request.POST.get('cat_name', '').strip()
            if cat_name:
                Category.objects.get_or_create(name=cat_name)
                messages.success(request, f'เพิ่มหมวด "{cat_name}" แล้ว')
        return redirect('inventory:manage')

    return render(request, 'inventory/product_manage.html', {
        'products': products,
        'categories': categories,
    })
