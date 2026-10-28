let PRODUCTS = [];
let cart = JSON.parse(localStorage.getItem("bakpao_cart") || "{}");

function rupiah(n) {
  return "Rp " + n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

async function loadMenu() {
  const r = await fetch("/api/products");
  const data = await r.json();
  PRODUCTS = data.products;
  const box = document.getElementById("menu");
  box.innerHTML = "";
  PRODUCTS.forEach(p => {
    const el = document.createElement("div");
    el.className = "card p-3";
    el.innerHTML =
      '<img src="' + p.img + '" alt="' + p.name + '" class="w-full h-36 object-cover rounded-md border border-[#2b2118]">' +
      '<h3 class="font-bold mt-2">' + p.name + '</h3>' +
      '<p class="sans text-sm text-[#5a4a3a]">' + p.description + '</p>' +
      '<div class="sans flex items-center justify-between mt-2">' +
      '<span class="font-bold">' + rupiah(p.price) + '</span>' +
      '<button data-id="' + p.id + '" class="btn-order addbtn px-3 py-1 text-sm font-bold">+ Tambah</button>' +
      '</div>';
    box.appendChild(el);
  });
  document.querySelectorAll(".addbtn").forEach(b => {
    b.addEventListener("click", () => {
      cart[b.dataset.id] = (cart[b.dataset.id] || 0) + 1;
      saveCart();
    });
  });
  renderCart();
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
  if (count === 0) { bar.classList.add("hidden"); return; }
  bar.classList.remove("hidden");
  document.getElementById("cartcount").textContent = count;
  document.getElementById("carttotal").textContent = rupiah(total);
}

document.getElementById("orderbtn").addEventListener("click", async () => {
  const items = Object.entries(cart).map(([product_id, qty]) => ({ product_id, qty }));
  const r = await fetch("/api/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items })
  });
  if (!r.ok) { alert("Gagal membuat pesanan."); return; }
  const order = await r.json();
  cart = {};
  saveCart();
  window.location.href = "/pay/" + order.order_code;
});

loadMenu();
