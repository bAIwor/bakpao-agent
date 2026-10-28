let PRODUCTS = [];
let cart = JSON.parse(localStorage.getItem("bakpao_cart") || "{}");
let activeFilter = "all";

function rupiah(n) {
  return "Rp " + n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

async function loadMenu() {
  try {
    const r = await fetch("/api/products");
    const data = await r.json();
    PRODUCTS = data.products;
    renderMenu();
    syncFilterLabels();
    renderCart();
  } catch (err) {
    console.error("Gagal memuat produk:", err);
  }
}

function renderMenu() {
  const box = document.getElementById("menu");
  if (!box) return;
  box.innerHTML = "";

  const filtered = PRODUCTS.filter(p => {
    if (activeFilter === "all") return true;
    if (activeFilter === "reguler") return p.size === "reguler";
    if (activeFilter === "mini") return p.size === "mini";
    return true;
  });

  filtered.forEach(p => {
    const qtyInCart = cart[p.id] || 0;
    const el = document.createElement("div");
    el.className = "bakery-card rounded-3xl p-4 flex flex-col justify-between relative group";
    
    // Badges & styling
    const sizeColor = p.size === "reguler" 
      ? "bg-amber-100 text-amber-900 border-amber-300" 
      : "bg-emerald-100 text-emerald-900 border-emerald-300";
    const badgeText = p.badge || (p.size === "reguler" ? "Pilihan Utama ✨" : "Ukuran Mini 🌟");

    el.innerHTML = `
      <div class="relative w-full h-44 rounded-2xl overflow-hidden bg-amber-50 mb-3.5 border border-amber-200/50">
        <img src="${p.img}" alt="${p.name}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500">
        <span class="absolute top-2.5 left-2.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-white/90 backdrop-blur-md shadow-sm border ${sizeColor}">
          ${(p.size === 'reguler' ? 'Reguler' : 'Mini')} · ${rupiah(p.price)}
        </span>
        <span class="absolute bottom-2.5 right-2.5 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-stone-900/80 text-white backdrop-blur-sm">
          ${badgeText}
        </span>
      </div>

      <div class="space-y-1.5 flex-1">
        <h3 class="font-bold text-base sm:text-lg text-amber-950 leading-snug group-hover:text-amber-700 transition-colors">
          ${p.name}
        </h3>
        <p class="text-xs sm:text-sm text-stone-600 leading-relaxed line-clamp-2">
          ${p.description}
        </p>
      </div>

      <div class="pt-4 mt-2 border-t border-amber-100/70 flex items-center justify-between gap-2">
        <div>
          <span class="text-[10px] uppercase font-semibold tracking-wider text-stone-400 block">Harga</span>
          <span class="text-lg font-extrabold text-amber-900 tracking-tight leading-none">${rupiah(p.price)}</span>
        </div>

        <button data-id="${p.id}" class="addbtn px-4 py-2 rounded-xl bg-amber-800 hover:bg-amber-900 active:scale-95 text-white font-bold text-xs sm:text-sm shadow-md transition-all flex items-center gap-1.5">
          <span>+ Tambah</span>
          ${qtyInCart > 0 ? `<span class="px-1.5 py-0.5 bg-amber-500 rounded-full text-[10px] font-black">${qtyInCart}</span>` : ''}
        </button>
      </div>
    `;
    box.appendChild(el);
  });

  document.querySelectorAll(".addbtn").forEach(b => {
    b.addEventListener("click", () => {
      const id = b.dataset.id;
      cart[id] = (cart[id] || 0) + 1;
      saveCart();
      renderMenu(); // update in-card counter
    });
  });
}

function syncFilterLabels() {
  const container = document.getElementById("filter-tabs");
  if (!container) return;
  const btn = name => container.querySelector('[data-filter="' + name + '"]');
  const all = btn("all");
  if (all) all.textContent = "Semua (" + PRODUCTS.length + ")";
  ["reguler", "mini"].forEach(size => {
    const items = PRODUCTS.filter(p => p.size === size);
    const el = btn(size);
    if (!el || items.length === 0) return;
    const cheapest = Math.min.apply(null, items.map(p => p.price));
    el.textContent = (size === "reguler" ? "Reguler" : "Mini") + " · " + rupiah(cheapest);
  });
}

function setupFilterTabs() {
  const container = document.getElementById("filter-tabs");
  if (!container) return;
  const buttons = container.querySelectorAll(".tab-btn");
  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => {
        b.className = "tab-btn px-3 py-1.5 rounded-xl bg-white text-stone-700 hover:bg-amber-50 border border-stone-200 transition-all";
      });
      btn.className = "tab-btn px-3 py-1.5 rounded-xl bg-amber-800 text-white shadow-sm transition-all";
      activeFilter = btn.dataset.filter;
      renderMenu();
    });
  });
}

function saveCart() {
  localStorage.setItem("bakpao_cart", JSON.stringify(cart));
  renderCart();
}

function cartTotals() {
  let count = 0, total = 0;
  for (const [id, qty] of Object.entries(cart)) {
    const p = PRODUCTS.find(x => x.id === id);
    if (!p) continue;
    count += qty;
    total += p.price * qty;
  }
  return { count, total };
}

function renderCart() {
  const { count, total } = cartTotals();
  const bar = document.getElementById("cartbar");
  if (!bar) return;

  const main = document.querySelector("main");
  if (count === 0) {
    bar.classList.add("hidden");
    if (main) main.style.paddingBottom = "";
    return;
  }
  bar.classList.remove("hidden");
  // keranjang mengambang bisa lebih tinggi dari pb-36 -> beri ruang dinamis
  if (main) main.style.paddingBottom = (bar.offsetHeight + 24) + "px";

  document.getElementById("cartcount").textContent = count;
  document.getElementById("carttotal").textContent = rupiah(total);

  const box = document.getElementById("cartitems");
  if (!box) return;
  box.innerHTML = "";

  for (const [id, qty] of Object.entries(cart)) {
    const p = PRODUCTS.find(x => x.id === id);
    if (!p) continue;
    const row = document.createElement("div");
    row.className = "flex items-center justify-between text-xs sm:text-sm py-1.5";
    row.innerHTML = `
      <div class="flex items-center gap-2">
        <span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
        <span class="font-medium text-stone-800">${p.name}</span>
        <span class="text-stone-400 font-semibold">(${rupiah(p.price)})</span>
      </div>
      <div class="flex items-center gap-1.5">
        <span class="font-extrabold text-amber-950 w-6 text-center">${qty}</span>
        <div class="inline-flex rounded-lg border border-stone-200 bg-white p-0.5 shadow-xs">
          <button data-id="${id}" data-act="dec" class="cartbtn w-6 h-6 flex items-center justify-center rounded hover:bg-amber-100 text-stone-700 font-bold">−</button>
          <button data-id="${id}" data-act="inc" class="cartbtn w-6 h-6 flex items-center justify-center rounded hover:bg-amber-100 text-stone-700 font-bold">+</button>
        </div>
        <button data-id="${id}" data-act="del" class="cartbtn text-stone-400 hover:text-rose-600 p-1 text-xs ml-1" title="Hapus">✕</button>
      </div>
    `;
    box.appendChild(row);
  }

  box.querySelectorAll(".cartbtn").forEach(b => {
    b.addEventListener("click", () => {
      const id = b.dataset.id;
      if (b.dataset.act === "inc") cart[id] = (cart[id] || 0) + 1;
      if (b.dataset.act === "dec") {
        cart[id] = (cart[id] || 1) - 1;
        if (cart[id] <= 0) delete cart[id];
      }
      if (b.dataset.act === "del") delete cart[id];
      saveCart();
      renderMenu();
    });
  });
}

document.getElementById("clearbtn")?.addEventListener("click", () => {
  cart = {};
  saveCart();
  renderMenu();
});

document.getElementById("orderbtn")?.addEventListener("click", async () => {
  const btn = document.getElementById("orderbtn");
  const originalText = btn.innerHTML;
  
  const items = Object.entries(cart).map(([product_id, qty]) => ({ product_id, qty }));
  if (items.length === 0) return;

  btn.disabled = true;
  btn.innerHTML = `<span>Memproses Pesanan... ⏳</span>`;

  try {
    const r = await fetch("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items })
    });
    if (!r.ok) {
      alert("Gagal membuat pesanan. Silakan coba lagi.");
      btn.disabled = false;
      btn.innerHTML = originalText;
      return;
    }
    const order = await r.json();
    cart = {};
    saveCart();
    window.location.href = "/pay/" + order.order_code;
  } catch (err) {
    alert("Koneksi gagal. Periksa koneksi internet Anda.");
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
});

setupFilterTabs();
loadMenu();
