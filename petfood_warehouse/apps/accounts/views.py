from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


def logout_view(request):
    """ออกจากระบบ (รองรับทั้ง GET และ POST)"""
    logout(request)
    return redirect('accounts:login')


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})
