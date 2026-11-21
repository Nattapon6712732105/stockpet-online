/* ───── Sidebar toggle (mobile) ───── */
document.addEventListener('DOMContentLoaded', function () {
  const hamburger = document.getElementById('hamburger');
  const sidebar   = document.getElementById('sidebar');
  const overlay   = document.getElementById('sidebar-overlay');

  function openSidebar() {
    sidebar && sidebar.classList.add('open');
    overlay && overlay.classList.add('show');
  }
  function closeSidebar() {
    sidebar && sidebar.classList.remove('open');
    overlay && overlay.classList.remove('show');
  }

  hamburger && hamburger.addEventListener('click', openSidebar);
  overlay   && overlay.addEventListener('click', closeSidebar);

  /* ── HTMX ตะกร้า qty ── */
  document.addEventListener('change', function (e) {
    if (e.target.classList.contains('qty-input')) {
      updateCart();
    }
  });

  function updateCart() {
    let total = 0;
    document.querySelectorAll('.qty-input').forEach(inp => {
      const v = parseInt(inp.value) || 0;
      if (v > 0) total++;
    });
    const cartCount = document.getElementById('cart-count');
    if (cartCount) cartCount.textContent = total + ' รายการ';
  }

  /* ── +/- ปุ่มจำนวน ── */
  document.addEventListener('click', function (e) {
    if (e.target.classList.contains('qty-plus')) {
      const inp = e.target.closest('.qty-control').querySelector('.qty-input');
      inp.value = (parseInt(inp.value) || 0) + 1;
      inp.dispatchEvent(new Event('change'));
    }
    if (e.target.classList.contains('qty-minus')) {
      const inp = e.target.closest('.qty-control').querySelector('.qty-input');
      const v = (parseInt(inp.value) || 0) - 1;
      inp.value = Math.max(0, v);
      inp.dispatchEvent(new Event('change'));
    }
  });

  /* ── ค้นหาสด ── */
  const searchInp = document.getElementById('product-search');
  if (searchInp) {
    searchInp.addEventListener('input', function () {
      const q = this.value.toLowerCase();
      document.querySelectorAll('.product-row').forEach(row => {
        const name = row.dataset.name || '';
        row.style.display = name.includes(q) ? '' : 'none';
      });
    });
  }

  /* ── dismiss alerts ── */
  document.querySelectorAll('.alert-close').forEach(btn => {
    btn.addEventListener('click', function () {
      this.closest('.alert').remove();
    });
  });
});
