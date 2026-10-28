function rupiah(n) {
  return "Rp " + n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

function badge(s) {
  const meta = {
    MENUNGGU_BAYAR: { label: "Menunggu Bayar", bg: "bg-amber-950/80 text-amber-300 border-amber-600/40" },
    LUNAS: { label: "Lunas / Siap Kukus", bg: "bg-emerald-950/80 text-emerald-300 border-emerald-600/40" },
    GAGAL: { label: "Batal / Gagal", bg: "bg-rose-950/80 text-rose-300 border-rose-600/40" },
    SELESAI: { label: "Selesai Diantar", bg: "bg-blue-950/80 text-blue-300 border-blue-600/40" }
  };
  const conf = meta[s] || { label: s, bg: "bg-stone-800 text-stone-300 border-stone-600" };
  return `<span class="px-2.5 py-1 rounded-full text-[11px] font-bold border ${conf.bg}">${conf.label}</span>`;
}

async function loadQueue() {
  try {
    const r = await fetch("/api/kitchen/queue");
    const data = await r.json();
    const box = document.getElementById("queue");
    if (!box) return;

    const list = data.queue || [];

    // Update stats
    let pending = 0, paid = 0, done = 0;
    list.forEach(o => {
      if (o.status === "MENUNGGU_BAYAR") pending++;
      else if (o.status === "LUNAS") paid++;
      else if (o.status === "SELESAI") done++;
    });

    const statTotal = document.getElementById("stat-total");
    const statPending = document.getElementById("stat-pending");
    const statPaid = document.getElementById("stat-paid");
    const statDone = document.getElementById("stat-done");
    if (statTotal) statTotal.textContent = list.length;
    if (statPending) statPending.textContent = pending;
    if (statPaid) statPaid.textContent = paid;
    if (statDone) statDone.textContent = done;

    box.innerHTML = "";
    if (list.length === 0) {
      box.innerHTML = `
        <div class="col-span-full py-16 text-center text-stone-500 bg-stone-900/50 rounded-3xl border border-stone-800">
          <span class="text-4xl block mb-2">🥟</span>
          <p class="font-medium text-sm">Belum ada pesanan aktif di dapur.</p>
        </div>`;
      return;
    }

    list.slice().reverse().forEach(o => {
      const itemsHtml = o.items.map(i => `
        <div class="flex items-center justify-between text-xs py-1 border-b border-stone-800/60 last:border-0">
          <span class="text-stone-300 font-medium">${i.name}</span>
          <span class="font-bold text-amber-400 bg-amber-950/40 px-2 py-0.5 rounded-md border border-amber-800/30">×${i.qty}</span>
        </div>
      `).join("");

      const el = document.createElement("div");
      el.className = "ticket-card rounded-2xl p-4 flex flex-col justify-between space-y-3.5";
      
      const timeStr = o.created_at ? new Date(o.created_at).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }) : "-";

      el.innerHTML = `
        <div>
          <div class="flex items-center justify-between gap-2 pb-2.5 border-b border-stone-800">
            <div>
              <span class="text-xs font-mono text-amber-500 font-extrabold tracking-wider">#${o.queue_number || "-"}</span>
              <span class="text-xs text-stone-400 font-mono ml-1 font-bold">${o.order_code}</span>
            </div>
            ${badge(o.status)}
          </div>
          
          <div class="py-2.5 space-y-1">
            ${itemsHtml}
          </div>
        </div>

        <div class="pt-2.5 border-t border-stone-800 flex items-center justify-between">
          <div>
            <div class="text-[10px] text-stone-500">Total Pembayaran</div>
            <div class="font-bold text-sm text-stone-200">${rupiah(o.amount || o.total)}</div>
          </div>
          
          ${o.status === "LUNAS" ? `
            <button data-code="${o.order_code}" class="donebtn px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-bold text-xs shadow-md transition-all flex items-center gap-1">
              <span>✓ Siap Diantar</span>
            </button>
          ` : o.status === "MENUNGGU_BAYAR" ? `
            <div class="text-right">
              <button data-code="${o.order_code}" class="paidbtn px-3 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-500 active:scale-95 text-white font-bold text-xs shadow-md transition-all">
                Tandai Lunas
              </button>
              <div class="text-[10px] text-stone-500 mt-1">${timeStr}</div>
            </div>
          ` : `
            <span class="text-[11px] text-stone-500 italic">${timeStr}</span>
          `}
        </div>
      `;
      box.appendChild(el);
    });

    document.querySelectorAll(".paidbtn").forEach(b => {
      b.addEventListener("click", async () => {
        b.disabled = true;
        b.textContent = "Menyimpan...";
        await fetch("/api/orders/" + b.dataset.code + "/paid", { method: "POST" });
        loadQueue();
      });
    });

    document.querySelectorAll(".donebtn").forEach(b => {
      b.addEventListener("click", async () => {
        b.disabled = true;
        b.textContent = "Menyimpan...";
        await fetch("/api/orders/" + b.dataset.code + "/complete", { method: "POST" });
        loadQueue();
      });
    });

  } catch (err) {
    console.error("Gagal load queue dapur:", err);
  }
}

setInterval(loadQueue, 3000);
loadQueue();
