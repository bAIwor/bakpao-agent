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

document.getElementById("uploadbtn").addEventListener("click", async () => {
  const f = document.getElementById("bukti").files[0];
  const msg = document.getElementById("uploadmsg");
  if (!f) { msg.textContent = "Pilih file gambar dulu."; return; }
  const fd = new FormData();
  fd.append("file", f);
  const r = await fetch("/api/orders/" + CODE + "/verify", {
    method: "POST", body: fd
  });
  const data = await r.json();
  msg.textContent = "Hasil: " + (data.reason || data.status || r.status);
  refreshStatus();
});

setInterval(refreshStatus, 2000);
loadOrder();
