const CODE = window.location.pathname.split("/").pop();
document.getElementById("ocode").textContent = CODE;

function rupiah(n) {
  return "Rp " + n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

async function loadOrder() {
  const r = await fetch("/api/orders/" + CODE + "/qr");
  if (!r.ok) return;
  const q = await r.json();
  document.getElementById("nominal").textContent = rupiah(q.amount);
  document.getElementById("suffix").textContent = q.suffix;
  document.getElementById("qrpay").src = "data:image/png;base64," + q.qr_b64;
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

setInterval(refreshStatus, 2000);
loadOrder();
