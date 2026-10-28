function rupiah(n) {
  return "Rp " + n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

function badge(s) {
  const label = { MENUNGGU_BAYAR: "Menunggu", LUNAS: "Lunas",
                  GAGAL: "Gagal", SELESAI: "Selesai" }[s] || s;
  const cls = { MENUNGGU_BAYAR: "st-Menunggu", LUNAS: "st-Lunas",
                GAGAL: "st-Gagal", SELESAI: "st-Selesai" }[s] || "";
  return '<span class="badge sans text-xs font-bold ' + cls + '">' + label + "</span>";
}

async function loadQueue() {
  const r = await fetch("/api/kitchen/queue");
  const data = await r.json();
  const box = document.getElementById("queue");
  box.innerHTML = "";
  if (data.queue.length === 0) {
    box.innerHTML = '<p class="sans text-sm">Belum ada pesanan.</p>';
    return;
  }
  data.queue.slice().reverse().forEach(o => {
    const items = o.items.map(i => i.qty + "x " + i.name).join(", ");
    const el = document.createElement("div");
    el.className = "card sans p-3 text-sm";
    el.innerHTML =
      '<div class="flex items-center justify-between">' +
      "<span class='font-bold'>#" + (o.queue_number || "-") + " · " +
      o.order_code + "</span>" + badge(o.status) + "</div>" +
      '<p class="mt-1">' + items + "</p>" +
      '<p class="font-bold">' + rupiah(o.amount) + "</p>" +
      (o.status === "MENUNGGU_BAYAR"
        ? '<button data-code="' + o.order_code +
          '" class="btn btn-paid paidbtn px-3 py-1 mt-2 text-xs font-bold">Tandai Lunas</button>'
        : o.status === "LUNAS"
        ? '<button data-code="' + o.order_code +
          '" class="btn donebtn px-3 py-1 mt-2 text-xs font-bold">Siap Diantar</button>'
        : "");
    box.appendChild(el);
  });
  document.querySelectorAll(".paidbtn").forEach(b => {
    b.addEventListener("click", async () => {
      await fetch("/api/orders/" + b.dataset.code + "/paid", { method: "POST" });
      loadQueue();
    });
  });
  document.querySelectorAll(".donebtn").forEach(b => {
    b.addEventListener("click", async () => {
      await fetch("/api/orders/" + b.dataset.code + "/complete", { method: "POST" });
      loadQueue();
    });
  });
}

setInterval(loadQueue, 3000);
loadQueue();
