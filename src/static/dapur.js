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

const PASAR_NAMA = {
  terigu: "Terigu",
  gula: "Gula",
  minyak: "Minyak",
  ayam: "Ayam",
  telur: "Telur",
  kacang_hijau: "Kacang hijau"
};

function fmtPersenPasar(v) {
  const t = Number(v).toLocaleString("id-ID", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  return (v < 0 ? "" : "+") + t + "% vs dapur";
}

function fmtPeriodePasar(p) {
  if (!p || !p.dari || !p.sampai) return "-";
  const o = { day: "numeric", month: "short" };
  const a = new Date(p.dari + "T00:00:00").toLocaleDateString("id-ID", o);
  const b = new Date(p.sampai + "T00:00:00");
  return a + " - " + b.toLocaleDateString("id-ID", o) + " " + b.getFullYear();
}

async function loadPasar() {
  try {
    const panel = document.getElementById("panel-pasar");
    const grid = document.getElementById("pasar-grid");
    if (!panel || !grid) return;
    const r = await fetch("/api/pricing/commodities");
    const data = await r.json();
    const idx = data && data.indeks_pasar;
    const banding = (data && data.bandingan_pasar) || {};
    if (!idx || idx.ok !== true) return;
    const eceran = idx.eceran || {};

    const cards = Object.keys(PASAR_NAMA)
      .filter(k => eceran[k])
      .map(k => {
        const bd = banding[k];
        const sel = bd ? bd.selisih_dapur_vs_eceran_pct : null;
        let cls, label;
        if (sel === null || sel === undefined) {
          cls = "bg-stone-800 text-stone-400 border-stone-700";
          label = "tanpa data dapur";
        } else {
          cls = sel < 0
            ? "bg-stone-800 text-stone-300 border-stone-600"
            : "bg-amber-950/80 text-amber-300 border-amber-600/40";
          label = fmtPersenPasar(sel);
        }
        return `<div class="bg-stone-950/60 border border-stone-800 rounded-xl p-2.5">`
          + `<div class="text-[11px] font-semibold text-stone-400">${PASAR_NAMA[k]}</div>`
          + `<div class="font-extrabold text-sm text-stone-100 mt-0.5">Rp ${Number(eceran[k].median).toLocaleString("id-ID")}</div>`
          + `<span class="inline-block mt-1.5 px-2 py-0.5 rounded-full text-[11px] font-bold border ${cls}">${label}</span>`
          + `</div>`;
      }).join("");
    grid.innerHTML = cards;

    const per = document.getElementById("pasar-periode");
    const umur = document.getElementById("pasar-umur");
    const st = document.getElementById("pasar-status");
    if (per) per.textContent = fmtPeriodePasar(idx.periode);
    if (umur) umur.textContent = (idx.umur_hari === null || idx.umur_hari === undefined)
      ? "" : idx.umur_hari + " hari lalu";
    if (st) {
      const segar = idx.stale !== true;
      st.textContent = segar ? "data segar" : "data lama";
      st.className = "px-2.5 py-1 rounded-full text-[11px] font-bold border " + (segar
        ? "bg-emerald-950/80 text-emerald-300 border-emerald-600/40"
        : "bg-amber-950/80 text-amber-300 border-amber-600/40");
    }

    panel.classList.remove("hidden");
  } catch (err) {
    return;
  }
}

setInterval(loadPasar, 60000);
loadPasar();
