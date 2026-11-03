const CODE = window.location.pathname.split("/").pop();
document.getElementById("ocode").textContent = CODE;

function rupiah(n) {
  return "Rp " + n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

let expireAt = null;
let countdownTimer = null;

function startCountdown(createdAt, ttlMinutes) {
  if (!createdAt || !ttlMinutes) return;
  expireAt = new Date(createdAt).getTime() + ttlMinutes * 60 * 1000;
  const el = document.getElementById("countdown");
  const box = document.getElementById("countbox");
  if (!el) return;
  function tick() {
    const sisa = Math.max(0, expireAt - Date.now());
    const m = Math.floor(sisa / 60000);
    const s = Math.floor((sisa % 60000) / 1000);
    el.textContent = String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
    if (sisa === 0) {
      clearInterval(countdownTimer);
      if (box) { box.className = "bg-stone-100 rounded-2xl p-3 border border-stone-200 text-center"; }
      el.textContent = "KADALUWARSA";
      el.className = "text-xl font-extrabold font-mono text-stone-500 tracking-wider";
      const e = document.getElementById("ordererr");
      if (e) { e.classList.remove("hidden"); e.innerHTML = 'Waktu habis — tiket hangus. <a href=\"/\" class=\"underline\">Buat pesanan baru</a>'; }
    }
  }
  tick();
  countdownTimer = setInterval(tick, 1000);
}

async function loadOrder() {
  const r = await fetch("/api/orders/" + CODE + "/qr");
  if (!r.ok) {
    const e = document.getElementById("ordererr");
    if (e) e.classList.remove("hidden");
    return;
  }
  const q = await r.json();
  if (q.status === "GAGAL") {
    const e = document.getElementById("ordererr");
    if (e) { e.classList.remove("hidden"); e.innerHTML = 'Pesanan kadaluwarsa / dibatalkan. <a href=\"/\" class=\"underline\">Buat pesanan baru</a>'; }
    return;
  }
  document.getElementById("nominal").textContent = rupiah(q.amount);
  document.getElementById("suffix").textContent = q.suffix;
  const qrEl = document.getElementById("qrpay");
  if (qrEl) qrEl.src = "data:image/png;base64," + q.qr_b64;
  startCountdown(q.created_at, q.ttl_minutes);
  refreshStatus();
}

async function refreshStatus() {
  const r = await fetch("/api/orders/" + CODE);
  if (!r.ok) return;
  const o = await r.json();
  const el = document.getElementById("statusline");
  el.textContent = "Status: " + (o.status === "LUNAS" ? "LUNAS ✅" : o.status);
}

const REASON = {
  nominal_beda: "Nominal tidak cocok",
  bukan_struk_transfer: "Gambar ini bukan bukti transfer",
  duplikat_transaksi: "Struk ini sudah dipakai pesanan lain",
  di_luar_jendela_waktu: "Waktu pembayaran di luar 60 menit dari pesanan",
  confidence_rendah: "Gambar kurang jelas, coba foto ulang",
  nominal_ambigu: "Angka nominal tidak terbaca pasti",
  nominal_tidak_terbaca: "Nominal tidak terbaca",
  verifikasi_gagal: "Verifikasi gagal, coba lagi",
  respons_tidak_valid: "Verifikasi gagal, coba lagi"
};

document.getElementById("uploadbtn").addEventListener("click", async () => {
  const f = document.getElementById("bukti").files[0];
  const msg = document.getElementById("uploadmsg");
  if (!f) { msg.textContent = "Pilih file gambar dulu."; return; }
  msg.textContent = "Memeriksa bukti...";
  const fd = new FormData();
  fd.append("file", f);
  const r = await fetch("/api/orders/" + CODE + "/verify", {
    method: "POST", body: fd
  });
  const data = await r.json();
  const alasan = REASON[data.reason] || data.reason || "";
  if (data.status === "LUNAS") {
    msg.textContent = "Bukti diterima. Pesanan LUNAS.";
  } else if (data.status === "TIDAK_COCOK") {
    msg.textContent = alasan + (data.notes ? " — " + data.notes : "");
  } else if (data.status === "PERLU_DICEK") {
    msg.textContent = "Perlu dicek dapur — " + alasan;
  } else {
    msg.textContent = "Gagal: " + alasan;
  }
  refreshStatus();
});

document.getElementById("retryorder")?.addEventListener("click", (ev) => {
  ev.preventDefault();
  document.getElementById("ordererr")?.classList.add("hidden");
  loadOrder();
});

document.getElementById("cancelbtn")?.addEventListener("click", async () => {
  if (!confirm("Batalkan pesanan ini?")) return;
  await fetch("/api/orders/" + CODE + "/cancel", { method: "POST" });
  window.location.href = "/";
});

setInterval(refreshStatus, 2000);
loadOrder();
