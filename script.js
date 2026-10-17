const COLORS = { GENUINE: "#34d399", SUSPICIOUS: "#fbbf24", FRAUDULENT: "#fb7185" };
const MESSAGES = {
  COMPLETED: "✅ Payment completed",
  PENDING_OTP: "⏸ On hold – verify OTP to continue",
  DECLINED: "⛔ Payment declined",
};
const STATUS_TEXT = { COMPLETED: "Completed", PENDING_OTP: "Needs OTP", DECLINED: "Declined" };
const CIRCUMFERENCE = 2 * Math.PI * 58;
const $ = (id) => document.getElementById(id);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let current = null;

const post = (url, body) =>
  fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
    .then((r) => r.json());

/* ---------- live card preview ---------- */
function updateCard() {
  const sel = $("customer_id");
  $("ccName").textContent = sel.options[sel.selectedIndex].text.split(" ")[0];
  const amt = Number($("amount").value) || 0;
  $("ccAmount").textContent = "₹" + amt.toLocaleString("en-IN");
  $("ccCity").textContent = $("city").value;
}
["customer_id", "amount", "city"].forEach((id) => $(id).addEventListener("input", updateCard));

/* ---------- gauge ---------- */
function setGauge(percent, color) {
  const m = $("meter");
  m.style.stroke = color;
  m.style.strokeDashoffset = CIRCUMFERENCE * (1 - percent / 100);
}

async function pay() {
  $("payBtn").disabled = true;
  $("gauge").classList.add("loading");
  $("percent").textContent = "…";
  $("label").textContent = "Analyzing transaction…";
  $("label").className = "verdict";
  $("status").textContent = "";
  $("status").className = "status-pill";
  $("otpbox").style.display = "none";

  const body = {};
  ["customer_id", "amount", "merchant_risk", "city", "channel"].forEach((id) => (body[id] = $(id).value));

  try {
    const [d] = await Promise.all([post("/pay", body), sleep(800)]);
    $("gauge").classList.remove("loading");
    if (d.error) { $("label").textContent = d.error; $("percent").textContent = "–"; return; }
    show(d);
  } catch {
    $("gauge").classList.remove("loading");
    $("percent").textContent = "–";
    $("label").textContent = "Server error. Please try again.";
  } finally {
    $("payBtn").disabled = false;
  }
}

function show(d) {
  current = d;
  $("label").textContent = d.label[0] + d.label.slice(1).toLowerCase();
  $("label").className = "verdict " + d.label;
  $("percent").textContent = Math.round(d.probability) + "%";
  setGauge(d.probability, COLORS[d.label]);
  setStatus(d.status);
  $("otpbox").style.display = d.status === "PENDING_OTP" ? "block" : "none";
  refreshLedger();
}

function setStatus(status) {
  $("status").textContent = MESSAGES[status];
  $("status").className = "status-pill " + status;
}

async function verifyOtp() {
  const d = await post("/verify_otp", { id: current.id, otp: $("otp").value });
  if (d.error) { alert(d.error); return; }
  current.status = d.status;
  setStatus(d.status);
  $("otpbox").style.display = "none";
  $("otp").value = "";
  refreshLedger();
}

async function refreshLedger() {
  const rows = await (await fetch("/ledger")).json();
  const head = "<tr><th>ID</th><th>Amount</th><th>City</th><th>Fraud risk</th><th>Status</th></tr>";
  $("ledger").innerHTML = head + (rows.length
    ? rows.map((x) =>
        `<tr><td>${x.id}</td><td>₹${Number(x.amount).toLocaleString("en-IN")}</td><td>${x.city}</td>` +
        `<td>${x.probability}%</td><td><span class="pill ${x.status}">${STATUS_TEXT[x.status]}</span></td></tr>`
      ).join("")
    : `<tr><td colspan="5" class="empty">No transactions yet. Make a payment to see it here.</td></tr>`);
}

$("payBtn").addEventListener("click", pay);
$("otpBtn").addEventListener("click", verifyOtp);
updateCard();
refreshLedger();
