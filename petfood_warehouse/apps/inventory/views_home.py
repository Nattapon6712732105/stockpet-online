from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone

from apps.accounts.models import User
from apps.inventory.models import Product, CentralStock, StockMovement, Category
from apps.requisitions.models import RequisitionRequest


@login_required
def home(request):
    """หน้าแรก — แดชบอร์ดตามบทบาท"""
    user = request.user

    if user.is_admin:
        return _admin_dashboard(request)
    else:
        return _requester_dashboard(request)


def _admin_dashboard(request):
    pending_requests = RequisitionRequest.objects.filter(
        status='PENDING'
    ).select_related('branch', 'requested_by').prefetch_related('items')[:10]

    # สรุปสต็อก
    stocks = CentralStock.objects.select_related('product', 'product__category').all()
    total_products = stocks.count()
    low_stock = stocks.filter(quantity__lte=1000, product__min_stock__gt=0).extra(
        where=['quantity <= apps_inventory_product.min_stock']
    ).count() if False else 0  # คำนวณด้วย Python แทน

    stock_list = list(stocks)
    empty_count = sum(1 for s in stock_list if s.quantity == 0)
    low_count = sum(1 for s in stock_list if 0 < s.quantity <= s.product.min_stock)
    ok_count = sum(1 for s in stock_list if s.quantity > s.product.min_stock)

    today = timezone.now().date()
    movements_today = StockMovement.objects.filter(created_at__date=today).count()

    context = {
        'pending_requests': pending_requests,
        'pending_count': RequisitionRequest.objects.filter(status='PENDING').count(),
        'empty_count': empty_count,
        'low_count': low_count,
        'movements_today': movements_today,
        'stock_list': stock_list,
    }
    return render(request, 'inventory/admin_dashboard.html', context)


def _requester_dashboard(request):
    user = request.user
    if not user.branch:
        messages.warning(request, 'บัญชีของคุณยังไม่ได้ผูกกับสาขา กรุณาติดต่อผู้ดูแล')
        return render(request, 'inventory/requester_dashboard.html', {})

    my_requests = RequisitionRequest.objects.filter(
        branch=user.branch
    ).select_related('decided_by').prefetch_related('items')[:10]

    # สินค้าใกล้หมดในสาขา
    from apps.inventory.models import BranchStock
    low_branch = BranchStock.objects.filter(
        branch=user.branch
    ).select_related('product', 'product__category').filter(
        quantity__lte=10
    )

    context = {
        'my_requests': my_requests,
        'low_branch': low_branch,
        'pending_my': my_requests.filter(status='PENDING').count() if my_requests else 0,
    }
    return render(request, 'inventory/requester_dashboard.html', context)
