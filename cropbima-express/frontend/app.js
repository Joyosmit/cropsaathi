const $ = id => document.getElementById(id);
let claim = null, auditR = null, lastPrompt = "", mediaRec = null, chunks = [];
let formFile = null, landFile = null;
const step = n => [1,2,3,4].forEach(i => $("s"+i).classList.toggle("active", i<=n));

async function api(path, opts={}) {
  const r = await fetch(path, opts);
  if (!r.ok) { const t = await r.text(); throw new Error(t.slice(0,300)); }
  const ct = r.headers.get("content-type")||"";
  return ct.includes("json") ? r.json() : r.blob();
}
async function refreshMode(){ try{ const h = await api("/health"); $("mode").textContent = h.mock_mode ? "MOCK ● no key" : "LIVE ● Sarvam API"; }catch{} }
refreshMode();

// ---- two-slot upload ----
function preview(f){ return f.type.startsWith("image") ? `<br/><img src="${URL.createObjectURL(f)}"/>` : ""; }
function setSlot(slot, f){
  if (slot === "form") { formFile = f; $("formPrev").innerHTML = "✅ " + f.name + preview(f); }
  else { landFile = f; $("landPrev").innerHTML = "✅ " + f.name + preview(f); }
}
function wireDrop(dropId, inputId, slot){
  const drop = $(dropId), inp = $(inputId);
  ["dragover","dragenter"].forEach(e => drop.addEventListener(e, ev => {ev.preventDefault(); drop.style.background="#dcfce7";}));
  ["dragleave","drop"].forEach(e => drop.addEventListener(e, ev => {ev.preventDefault(); drop.style.background="";}));
  drop.addEventListener("drop", ev => { const f = ev.dataTransfer.files[0]; if (f) setSlot(slot, f); });
  inp.addEventListener("change", () => { if (inp.files[0]) setSlot(slot, inp.files[0]); });
}
wireDrop("dropForm","fileForm","form");
wireDrop("dropLand","fileLand","land");

$("demoBtn").onclick = async () => {
  $("docStatus").textContent = "⏳ Loading your sample form + 7/12…";
  const fb = await (await fetch("/assets/sample_pmfby_form.png")).blob();
  const lb = await (await fetch("/assets/sample_712_extract.png")).blob();
  setSlot("form", new File([fb], "sample_pmfby_form.png", {type:"image/png"}));
  setSlot("land", new File([lb], "sample_712_extract.png", {type:"image/png"}));
  $("docStatus").textContent = "✅ Samples loaded — hit “Process both documents”.";
};
$("processPairBtn").onclick = async () => {
  if (!formFile && !landFile) return alert("Upload the form and/or 7/12 first (or use sample docs).");
  $("docStatus").textContent = "⏳ Sarvam Vision reading " +
    [formFile&&"complaint form", landFile&&"7/12 extract"].filter(Boolean).join(" + ") + " …";
  const fd = new FormData();
  if (formFile) fd.append("form", formFile);
  if (landFile) fd.append("land_record", landFile);
  try {
    const out = await api("/api/v1/documents/process-pair", {method:"POST", body:fd});
    claim = out.merged;
    const bits = [];
    if (out.form?.farmer_name) bits.push("Form → " + out.form.farmer_name);
    if (out.land?.farmer_name) bits.push("7/12 → " + out.land.farmer_name);
    else if (out.land) bits.push("7/12 → digitised " + (out.land.raw_text||"").slice(0,60));
    if (claim.verification?.length) bits.push("check: " + claim.verification.map(v=>v.field+" "+(v.match?"✅":"⚠️")).join(", "));
    $("docStatus").textContent = (claim.mock?"⚠️ MOCK · ":"✅ ") + bits.join(" | ");
    renderFields(); step(2); await runAudit();
  } catch(e){ $("docStatus").textContent = "❌ " + e.message; }
};
// __PART2__

function renderFields(){
  const F = [["farmer_name","Farmer"],["father_name","Father"],
    ["survey_khasra_number","Survey/Gat"],["land_area_acres","Area (acres)"],
    ["land_area_hectare","Area (hectare)"],["village_taluka_district","Village/Taluka/Dist"],
    ["crop_type","Crop"],["damage_reason","Cause"],["damage_percentage","Loss %"],
    ["loss_date","Loss date"],["mobile_number","Mobile"]];
  $("verifyCard").hidden = false;
  let html = F.map(([k,l]) =>
    `<div class="field"><b>${l}</b><input data-k="${k}" value="${claim[k] ?? ""}"/></div>`).join("");
  if (claim.verification?.length) html += claim.verification.map(v =>
    `<div class="field ver ${v.match?"":"bad"}"><b>7/12 check · ${v.field} ${v.match?"✅":"⚠️"}</b><span class="src">form: ${v.form}<br/>7/12: ${v.land_record}</span></div>`).join("");
  $("fields").innerHTML = html;
  $("fields").querySelectorAll("input").forEach(i => i.onchange = () => {
    let v = i.value;
    if (["land_area_acres","land_area_hectare","damage_percentage"].includes(i.dataset.k)) v = v===""?null:Number(v);
    claim[i.dataset.k] = v;
  });
}
$("auditBtn").onclick = () => runAudit();
async function runAudit(){
  auditR = await api("/api/v1/claims/audit", {method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({data: claim, language: $("lang").value})});
  renderAudit();
}
function renderAudit(){
  $("auditCard").hidden = false; step(3);
  lastPrompt = auditR.next_prompts[0] || auditR.summary || "";
  let html = `<p>Eligible: <b>${auditR.eligible?"Yes ✅":"No — missing: "+auditR.missing_fields.join(", ")}</b></p>` +
    (auditR.payout_hint?`<p>💡 ${auditR.payout_hint}</p>`:"");
  if (auditR.next_prompts.length) html += auditR.next_prompts.map(p=>`<p class="status">🎙️ ${p}</p>`).join("");
  else if (auditR.summary) html += `<p class="status">🎙️ ${auditR.summary}</p>`;
  html += `<p class="hint">Or correct any single field by voice: <select id="targetField">` +
    `<option value="">auto-detect</option>` +
    [["farmer_name","Farmer"],["father_name","Father"],["survey_khasra_number","Survey/Gat"],
     ["land_area_acres","Area"],["village_taluka_district","Village"],["crop_type","Crop"],
     ["damage_reason","Cause"],["damage_percentage","Loss %"],["loss_date","Loss date"],
     ["mobile_number","Mobile"]].map(([v,l])=>`<option value="${v}">${l}</option>`).join("") +
    `</select></p>`;
  $("auditOut").innerHTML = html;
  if (auditR.eligible) { $("submitCard").hidden = false; step(4); }
}
// ---- voice ----
$("recBtn").onclick = async () => {
  if (mediaRec && mediaRec.state === "recording") { mediaRec.stop(); return; }
  const stream = await navigator.mediaDevices.getUserMedia({audio:true});
  mediaRec = new MediaRecorder(stream); chunks = [];
  mediaRec.ondataavailable = e => chunks.push(e.data);
  mediaRec.onstop = async () => {
    const blob = new Blob(chunks, {type:"audio/webm"});
    $("heard").textContent = "⏳ Saaras transcribing…";
    const fd = new FormData(); fd.append("file", blob, "voice.webm"); fd.append("language", "auto");
    try {
      const s = await api("/api/v1/voice/stt", {method:"POST", body:fd});
      $("heard").textContent = "👂 Heard ("+s.language_code+"): " + s.transcript;
      const target = document.getElementById("targetField")?.value || null;
      const vf = await api("/api/v1/claims/voice-fill", {method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({data: claim, transcript: s.transcript, language: $("lang").value, target_field: target})});
      claim = vf.updated_data;
      if (vf.filled_field) {
        $("heard").textContent += `  → updated: ${vf.filled_field} = ${claim[vf.filled_field]} ✅`;
        speak(`${vf.filled_field} updated.`);
      } else {
        $("heard").textContent += "  → no field matched. Pick a field above or speak a full correction (e.g. 'father name is …').";
        speak("Sorry, I could not match that. Please pick a field or speak again.");
      }
      renderFields(); auditR = vf.audit; renderAudit();
    } catch(e){ $("heard").textContent = "❌ " + e.message; }
  };
  mediaRec.start(); $("recBtn").textContent = "⏹️ Stop / रोकें";
  setTimeout(()=>{ if(mediaRec.state==="recording") mediaRec.stop(); $("recBtn").textContent="🎤 Speak / बोलें"; }, 25000);
};
async function speak(text){
  try {
    const b = await api("/api/v1/voice/tts", {method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({text, language_code:$("lang").value, speaker:"simran"})});
    const p = $("player"); p.src = URL.createObjectURL(b); p.style.display="block"; p.play();
  } catch(e){ console.warn("tts failed", e); }
}
$("ttsBtn").onclick = async () => {
  if (!lastPrompt) return alert("No prompt yet — run audit first");
  speak(lastPrompt);
};
// ---- submit ----
$("submitBtn").onclick = async () => {
  const c = await api("/api/v1/claims", {method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({...claim, language:$("lang").value})});
  const s = await api(`/api/v1/claims/${c.id}/submit`, {method:"POST"});
  $("refOut").textContent = `✅ Claim ${s.reference} submitted!`;
  $("jsonOut").textContent = JSON.stringify(s.summary, null, 2);
  const pdf = $("pdfBtn"); pdf.hidden = false; pdf.href = `/api/v1/claims/${c.id}/receipt.pdf`;
};
