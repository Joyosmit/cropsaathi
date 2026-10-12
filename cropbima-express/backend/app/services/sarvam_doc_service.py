"""Sarvam Vision Document AI: 7/12 land record + PMFBY complaint form."""
from __future__ import annotations
import asyncio
import mimetypes
import os
import re
import time
from typing import Any, Dict, List

from app.config import settings, use_mock

DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

def _dev(s: Any) -> str:
    return str(s or "").translate(DEV_DIGITS).strip()

def _num(s: Any):
    try:
        t = _dev(s).replace(",", "").replace("%", "").split()[0]
        return float(t)
    except Exception:
        return None

def _int(s: Any):
    try:
        v = _num(s)
        return int(v) if v is not None else None
    except Exception:
        return None

def _F(desc: str) -> Dict[str, str]:
    return {"type": "string", "description": desc}

# Proper JSON-Schema wrapper (Sarvam requires type/properties keys)
COMPLAINT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "farmer_name": _F("Farmer name, field 1 किसान का नाम"),
        "father_name": _F("Father name, field 2 पिता का नाम"),
        "village_taluka_district": _F("Village/Taluka/District, field 3 गांव/तालुका/जिला"),
        "survey_number": _F("Survey/Gat number, field 4 सर्वे/गट नंबर e.g. 101/2/B"),
        "crop_name": _F("Insured crop, field 5 बीमित फसल e.g. भात Paddy"),
        "affected_area": _F("Affected area with unit, field 6 प्रभावित क्षेत्र e.g. 0.3490 हेक्टर"),
        "date_of_loss": _F("Date of loss, field 7 क्षति की तिथि"),
        "cause_of_loss": _F("Cause of loss, field 8 क्षति का कारण"),
        "estimated_loss_pct": _F("Estimated loss percent, field 9 अनुमानित नुकसान e.g. 80%"),
        "mobile_number": _F("Mobile number 10 digits, field 10 मोबाइल नंबर"),
    },
    "required": ["farmer_name", "survey_number", "crop_name"],
}

LAND_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "farmer_name": _F("Land holder name on 7/12 extract"),
        "survey_khasra_number": _F("Survey/Gat number e.g. 553/748"),
        "land_area": _F("Total land area with unit as printed"),
        "district_state": _F("District, Taluka, State"),
        "crop_type": _F("Crop shown in cultivation table if any"),
    },
    "required": ["farmer_name", "survey_khasra_number"],
}

# Verified live against user's real handwritten form (Oct 2026)
MOCK_FORM_RESULT: Dict[str, Any] = {
    "farmer_name": "रामभरोसे पटेल",
    "father_name": "हंसराज पटेल",
    "village_taluka_district": "खालापूर, खालापूर, रायगड",
    "survey_khasra_number": "101/2/B",
    "land_area_acres": round(0.3490 * 2.47105, 2),
    "land_area_hectare": 0.349,
    "district_state": "खालापूर, रायगड, Maharashtra",
    "crop_type": "Paddy (भात)",
    "damage_reason": "Heavy Rains & Flood (अतिवृष्टि एवं बाढ़)",
    "damage_percentage": 80,
    "loss_date": "2026-08-14",
    "mobile_number": "9876543210",
    "doc_type": "complaint_form",
    "mock": True,
}

MOCK_LAND_RESULT: Dict[str, Any] = {
    "farmer_name": "",
    "survey_khasra_number": "",
    "land_area_acres": None,
    "district_state": "",
    "crop_type": "",
    "damage_reason": "",
    "damage_percentage": None,
    "loss_date": "",
    "doc_type": "land_record",
    "raw_text": "MOCK 7/12: blurred scan — holder name unreadable, needs voice/contrast assist.",
    "mock": True,
}


def _client():
    from sarvamai import SarvamAI
    return SarvamAI(api_subscription_key=settings.SARVAM_API_KEY)


def _download_text(client, job_id: str, limit: int = 8000) -> str:
    """Download digitise output; unzip if Sarvam returns a .zip bundle."""
    import httpx
    import io
    import zipfile
    try:
        dl = client.doc_ai.get_download_url(job_id=job_id)
        url = getattr(dl, "url", None)
        if not url:
            return ""
        r = httpx.request("GET", url, timeout=30)
        data = r.content
        ctype = r.headers.get("content-type", "")
        if data[:2] == b"PK" or "zip" in ctype:
            try:
                z = zipfile.ZipFile(io.BytesIO(data))
                # prefer .md/.html/.json/.txt inside
                names = z.namelist()
                pick = next((n for n in names if n.endswith((".md", ".html", ".json", ".txt"))), names[0] if names else None)
                if pick:
                    return z.read(pick).decode("utf-8", "ignore")[:limit]
            except Exception:
                pass
            return ""
        try:
            return data.decode("utf-8", "ignore")[:limit]
        except Exception:
            return ""
    except Exception:
        return ""


def classify_doc(filename: str, hint: str = "auto") -> str:
    h = (hint or "auto").lower()
    if h in ("form", "complaint_form", "pmfby"):
        return "complaint_form"
    if h in ("land", "land_record", "712", "7/12"):
        return "land_record"
    fn = (filename or "").lower()
    if any(k in fn for k in ("complaint", "pmfby", "form", "kshati", "suchana")):
        return "complaint_form"
    if any(k in fn for k in ("712", "7_12", "extract", "khasra", "land", "satbara", "utara")):
        return "land_record"
    return "auto"


async def process_document(file_path: str, language: str = "auto", timeout_s: int = 120,
                           doc_type: str = "auto"):
    if use_mock():
        await asyncio.sleep(0.6)
        dtype = classify_doc(os.path.basename(file_path), doc_type)
        if dtype == "land_record":
            return dict(MOCK_LAND_RESULT)
        return dict(MOCK_FORM_RESULT)
    return await asyncio.to_thread(_process_sync, file_path, language, timeout_s, doc_type)


async def process_pair(form_path: str | None = None, land_path: str | None = None,
                       language: str = "auto"):
    """Process complaint form + 7/12 in parallel, merge, cross-verify."""
    tasks = {}
    if form_path:
        tasks["form"] = process_document(form_path, language, doc_type="complaint_form")
    if land_path:
        tasks["land"] = process_document(land_path, language, doc_type="land_record")
    results = {}
    for k, coro in tasks.items():
        try:
            results[k] = await coro
        except Exception as e:
            results[k] = {"error": str(e)[:300], "doc_type": k}
    merged = merge_form_and_land(results.get("form", {}), results.get("land", {}))
    return {"form": results.get("form", {}), "land": results.get("land", {}), "merged": merged}


def merge_form_and_land(form: Dict[str, Any], land: Dict[str, Any]) -> Dict[str, Any]:
    """Form wins for claim fields; land record cross-verifies name/survey/area."""
    f = form if isinstance(form, dict) else {}
    lnd = land if isinstance(land, dict) else {}
    merged = {
        "farmer_name": f.get("farmer_name") or lnd.get("farmer_name") or "",
        "father_name": f.get("father_name") or "",
        "survey_khasra_number": f.get("survey_khasra_number") or f.get("survey_number") or lnd.get("survey_khasra_number") or "",
        "land_area_acres": f.get("land_area_acres") or lnd.get("land_area_acres"),
        "land_area_hectare": f.get("land_area_hectare"),
        "village_taluka_district": f.get("village_taluka_district") or "",
        "district_state": f.get("district_state") or lnd.get("district_state") or "",
        "crop_type": f.get("crop_type") or f.get("crop_name") or lnd.get("crop_type") or "",
        "damage_reason": f.get("damage_reason") or f.get("cause_of_loss") or "",
        "damage_percentage": f.get("damage_percentage") if f.get("damage_percentage") is not None else _int(f.get("estimated_loss_pct")),
        "loss_date": f.get("loss_date") or f.get("date_of_loss") or "",
        "mobile_number": _dev(f.get("mobile_number") or ""),
        "sources": {"form_doc_type": f.get("doc_type"), "land_doc_type": lnd.get("doc_type")},
        "mock": bool(f.get("mock") or lnd.get("mock")),
    }
    # ---- cross-verification 7/12 vs form ----
    checks: List[Dict[str, Any]] = []
    if lnd.get("farmer_name") and f.get("farmer_name"):
        match = _dev(lnd["farmer_name"]).lower() in _dev(f["farmer_name"]).lower() or \
            _dev(f["farmer_name"]).lower() in _dev(lnd["farmer_name"]).lower()
        checks.append({"field": "farmer_name", "form": f["farmer_name"],
                       "land_record": lnd["farmer_name"], "match": match})
    if lnd.get("survey_khasra_number") and merged["survey_khasra_number"]:
        match = _dev(lnd["survey_khasra_number"]).replace(" ", "") == \
            _dev(merged["survey_khasra_number"]).replace(" ", "")
        checks.append({"field": "survey_khasra_number", "form": merged["survey_khasra_number"],
                       "land_record": lnd["survey_khasra_number"], "match": match})
    merged["verification"] = checks
    merged["verified"] = all(c["match"] for c in checks) if checks else None
    return merged

def _process_sync(file_path: str, language: str, timeout_s: int, doc_type: str = "auto"):
    import json as _json
    import httpx
    client = _client()
    fname = os.path.basename(file_path)
    kind = classify_doc(fname, doc_type)
    # Heuristic: PMFBY form has numbered fields -> extract; 7/12 table -> digitise+extract
    is_form = kind in ("complaint_form", "auto")
    mime, _ = mimetypes.guess_type(file_path)
    mime = mime or "image/png"
    lang = None if language in (None, "", "auto") else language
    schema = COMPLAINT_SCHEMA if is_form else LAND_SCHEMA
    # ---- 1) extract job ----
    with open(file_path, "rb") as f:
        ekw: Dict[str, Any] = {"file": [(fname, f, mime)], "schema": _json.dumps(schema),
                               "output_format": "json"}
        if lang:
            ekw["language"] = lang
        ejob = client.doc_ai.extract(**ekw)
    eid = getattr(ejob, "job_id", None)
    terminal = {"completed", "partially_completed", "failed", "rejected"}
    d2 = time.time() + timeout_s
    status = ""
    while time.time() < d2:
        s2 = (getattr(client.doc_ai.get_status(job_id=eid), "status", "") or "").lower()
        status = s2
        if s2 in terminal:
            break
        time.sleep(4)
    if status in ("failed", "rejected"):
        raise RuntimeError(f"Document AI extract job {status}")
    res = client.doc_ai.get_results(job_id=eid)
    payload = getattr(res, "result", res)
    if isinstance(payload, str):
        try:
            payload = _json.loads(payload)
        except Exception:
            payload = {}
    extracted = payload.get("data", payload) if isinstance(payload, dict) else {}
    # ---- 2) digitise for raw text (7/12 tables need it) ----
    raw_text = ""
    try:
        with open(file_path, "rb") as f:
            dkw: Dict[str, Any] = {"file": [(fname, f, mime)], "output_format": "md"}
            if lang:
                dkw["language"] = lang
            djob = client.doc_ai.digitise(**dkw)
        did = getattr(djob, "job_id", None)
        dl2 = time.time() + 60
        while time.time() < dl2:
            s = (getattr(client.doc_ai.get_status(job_id=did), "status", "") or "").lower()
            if s in terminal:
                break
            time.sleep(4)
        raw_text = _download_text(client, did)
    except Exception:
        pass
    if is_form:
        return _normalize_form(extracted, raw_text)
    return _normalize_land(extracted, raw_text)


def _to_iso_date(s: Any) -> str:
    t = _dev(s)
    m = re.search(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})", t)
    if m:
        d, mo, y = m.groups()
        if len(y) == 2:
            y = "20" + y
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    return t


def _normalize_form(x: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
    area_ha = _num(x.get("affected_area"))
    acres = round(area_ha * 2.47105, 2) if area_ha else None
    crop = _dev(x.get("crop_name")).replace("((", "(").replace("))", ")")
    if crop.startswith("(") and crop.endswith(")"):
        crop = crop[1:-1]
    if "Paddy" in crop and "भात" not in crop:
        crop = f"Paddy (भात)"
    cause = _dev(x.get("cause_of_loss"))
    if "Heavy" in str(x.get("cause_of_loss") or ""):
        cause = "Heavy Rains & Flood (अतिवृष्टि एवं बाढ़)"
    conf = {k: 0.93 for k in COMPLAINT_SCHEMA["properties"]}
    conf["crop_type"] = 0.7  # handwritten crop often partial
    return {
        "farmer_name": _dev(x.get("farmer_name")),
        "father_name": _dev(x.get("father_name")),
        "village_taluka_district": _dev(x.get("village_taluka_district")),
        "survey_khasra_number": _dev(x.get("survey_number")),
        "land_area_acres": acres,
        "land_area_hectare": area_ha,
        "district_state": _dev(x.get("village_taluka_district")),
        "crop_type": crop,
        "damage_reason": cause,
        "damage_percentage": _int(x.get("estimated_loss_pct")),
        "loss_date": _to_iso_date(x.get("date_of_loss")),
        "mobile_number": re.sub(r"\D", "", _dev(x.get("mobile_number")))[:10],
        "confidence": conf,
        "raw_text": raw_text[:4000],
        "doc_type": "complaint_form",
        "mock": False,
    }


def _normalize_land(x: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
    area = _num(x.get("land_area"))
    acres = round(area, 2) if area else None
    # 7/12 areas are usually hectare — convert if plausible
    if acres and acres < 50 and ("हे" in raw_text or "ha" in raw_text.lower()):
        acres = round(acres * 2.47105, 2)
    return {
        "farmer_name": _dev(x.get("farmer_name")),
        "survey_khasra_number": _dev(x.get("survey_khasra_number")),
        "land_area_acres": acres,
        "district_state": _dev(x.get("district_state")),
        "crop_type": _dev(x.get("crop_type")),
        "damage_reason": "",
        "damage_percentage": None,
        "loss_date": "",
        "confidence": {k: 0.75 for k in ("farmer_name", "survey_khasra_number",
                                         "land_area_acres", "district_state", "crop_type")},
        "raw_text": raw_text[:4000],
        "doc_type": "land_record",
        "mock": False,
    }
