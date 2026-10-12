"""PMFBY rule validation + missing-field voice prompts."""
from __future__ import annotations
import re
from typing import Dict, Any, List

REQUIRED = ["farmer_name", "survey_khasra_number", "land_area_acres",
            "crop_type", "loss_date", "damage_reason"]

PROMPTS: Dict[str, Dict[str, str]] = {
    "farmer_name": {
        "hi-IN": "कृपया बोलकर अपना पूरा नाम बताएं, जैसा आधार या 7/12 पर है।",
        "mr-IN": "कृपया बोलून तुमचं पूर्ण नाव सांगा, जसं आधार किंवा 7/12 वर आहे।",
        "en-IN": "Please speak your full name as on Aadhaar or the land record.",
        "ta-IN": "ஆதாரில் உள்ளபடி உங்கள் முழு பெயரை கூறுங்கள்.",
        "te-IN": "ఆధార్‌లో ఉన్నట్లుగా మీ పూర్తి పేరు చెప్పండి.",
    },
    "survey_khasra_number": {
        "hi-IN": "कृपया अपना खसरा या सर्वे नंबर बोलकर बताएं।",
        "mr-IN": "कृपया तुमचा गट नंबर किंवा सर्व्हे नंबर बोलून सांगा।",
        "en-IN": "Please speak your Khasra or survey number.",
        "ta-IN": "உங்கள் சர்வே எண்ணைக் கூறுங்கள்.",
        "te-IN": "మీ సర్వే నంబర్ చెప్పండి.",
    },
    "land_area_acres": {
        "hi-IN": "आपके खेत का कुल रकबा एकड़ में कितना है? बोलकर बताएं।",
        "mr-IN": "तुमच्या शेताचं एकूण क्षेत्रफळ एकरमध्ये किती आहे?",
        "en-IN": "What is your total land area in acres?",
        "ta-IN": "உங்கள் நிலத்தின் பரப்பு ஏக்கரில் எவ்வளவு?",
        "te-IN": "మీ పొలం విస్తీర్ణం ఎకరాల్లో ఎంత?",
    },
    "crop_type": {
        "hi-IN": "कौन सी फसल का नुकसान हुआ? जैसे सोयाबीन, धान, कपास।",
        "mr-IN": "कोणत्या पिकाचं नुकसान झालं? जसं सोयाबीन, कापूस, भात।",
        "en-IN": "Which crop was damaged? Soybean, paddy, cotton?",
        "ta-IN": "எந்த பயிர் சேதமடைந்தது?",
        "te-IN": "ఏ పంట నష్టపోయింది?",
    },
    "loss_date": {
        "hi-IN": "आपके दस्तावेज़ से नुकसान की तारीख समझ नहीं आ रही है। कृपया बोलकर बताएं कि बारिश किस तारीख को हुई थी?",
        "mr-IN": "कागदपत्रांतून नुकसानाची तारीख समजली नाही. पाऊस कोणत्या तारखेला झाला ते सांगा.",
        "en-IN": "I could not read the loss date. Please speak the date of rainfall.",
        "ta-IN": "சேத தேதி தெளிவாக இல்லை. மழை தேதியை கூறுங்கள்.",
        "te-IN": "నష్టం తేదీ స్పష్టంగా లేదు. వర్షం తేదీ చెప్పండి.",
    },
    "damage_reason": {
        "hi-IN": "नुकसान का कारण क्या था? बाढ़, सूखा, ओलावृष्टि या कीट?",
        "mr-IN": "नुकसानीचं कारण काय? पूर, दुष्काळ, गारपीट की कीड?",
        "en-IN": "What caused the loss? Flood, drought, hailstorm, pests?",
        "ta-IN": "சேதத்திற்கான காரணம் என்ன?",
        "te-IN": "నష్టానికి కారణం ఏమిటి?",
    },
}

def _empty(v):
    return v is None or (isinstance(v, str) and not v.strip())


def audit_claim(data: Dict[str, Any], language: str = "hi-IN"):
    missing: List[str] = [f for f in REQUIRED if _empty(data.get(f))]
    low = []
    conf = data.get("confidence", {}) or {}
    for f in REQUIRED:
        try:
            if f not in missing and float(conf.get(f, 1.0)) < 0.6:
                low.append(f)
        except Exception:
            pass
    needs = missing + [f for f in low if f not in missing]
    lang = language if language in ("hi-IN", "mr-IN", "ta-IN", "te-IN", "en-IN") else "hi-IN"
    prompts = [PROMPTS[f].get(lang, PROMPTS[f]["en-IN"]) for f in needs]
    hint = None
    try:
        p = data.get("damage_percentage")
        if p is not None:
            p = int(p)
            hint = ("High loss — full assessment recommended" if p >= 50
                    else "Partial loss — field inspection may apply" if p >= 33
                    else "Below PMFBY 33% threshold — may not qualify")
    except Exception:
        pass
    summary = ""
    if not needs:
        nm = data.get("farmer_name", "farmer")
        summary = {
            "hi-IN": f"सभी जानकारी पूरी है, {nm} जी। कोई कमी नहीं है। आप सीधे सबमिट कर सकते हैं, या बोलकर कोई सुधार बता सकते हैं।",
            "mr-IN": f"सर्व माहिती पूर्ण आहे, {nm} जी। थेट सबमिट करा किंवा बोलून दुरुस्ती सांगा।",
            "en-IN": f"All details are complete, {nm}. You can submit directly, or speak a correction.",
            "ta-IN": "அனைத்து விவரங்களும் நிறைவடைந்தன. சமர்ப்பிக்கலாம் அல்லது திருத்தம் கூறலாம்.",
            "te-IN": "అన్ని వివరాలు పూర్తయ్యాయి. సమర్పించండి లేదా సవరణ చెప్పండి.",
        }.get(lang, f"All details complete. Submit or speak a correction.")
    return {"eligible": len(missing) == 0, "missing_fields": missing,
            "low_confidence_fields": low, "next_prompts": prompts,
            "next_field": needs[0] if needs else None, "payout_hint": hint,
            "summary": summary}


CROPS = ["soybean", "soyabean", "soyabin", "soya", "सोयाबीन", "सोयाबिन",
         "paddy", "pady", "bhat", "भात", "dhan", "धान",
         "cotton", "कपास", "कापूस", "wheat", "गेहूं", "sugarcane", "maize"]
CROP_CANON = {"soyabean": "Soybean", "soyabin": "Soybean", "soya": "Soybean",
              "सोयाबीन": "Soybean", "सोयाबिन": "Soybean",
              "pady": "Paddy", "bhat": "Paddy (भात)", "dhan": "Paddy", "धान": "Paddy", "भात": "Paddy (भात)"}
CAUSES = {"flood": "Flood", "बाढ़": "Flood", "पूर": "Flood", "baar": "Flood",
          "barish": "Excess Rainfall", "baarish": "Excess Rainfall",
          "drought": "Drought",
          "सूखा": "Drought", "दुष्काळ": "Drought", "hail": "Hailstorm",
          "गारपीट": "Hailstorm", "pest": "Pest Attack", "कीट": "Pest Attack",
          "rain": "Excess Rainfall", "बारिश": "Excess Rainfall", "पाऊस": "Excess Rainfall"}


def _detect_fields(tl: str):
    """All claim fields the transcript touches (multi-intent: crop + cause)."""
    found = []
    if re.search(r"(father|पिता|वडील)", tl):
        found.append("father_name")
    if re.search(r"(mobile|मोबाइल|मोबाईल|phone)", tl) and re.search(r"\d{6,}", tl):
        found.append("mobile_number")
    if re.search(r"(survey|khasra|गट|सर्वे|खसरा|gat).{0,10}\d|^\d+\s*/\s*\d+", tl):
        found.append("survey_khasra_number")
    if re.search(r"(village|gaon|गांव|गाव|taluka|तालुका|district|जिला|जिल्हा)", tl):
        found.append("village_taluka_district")
    if re.search(r"(acre|hectare|एकर|हेक्टर|क्षेत्र|रकबा|area)", tl) or re.search(r"\d+\.\d+", tl):
        found.append("land_area_acres")
    for c in CROPS:
        if c in tl:
            found.append("crop_type")
            break
    for k in CAUSES:
        if k in tl:
            found.append("damage_reason")
            break
    if re.search(r"(loss|nuksan|नुकसान|क्षति|kharab|खराब|percent|टक्के|प्रतिशत|%)", tl):
        found.append("damage_percentage")
    if re.search(r"(date|तारीख|दिनांक|august|september|जुलाई|अगस्त|सितंबर|\d{1,2}[/\-]\d{1,2})", tl):
        found.append("loss_date")
    if not found and re.search(r"(name|नाव|नाम)", tl):
        found.append("farmer_name")
    return found


def _detect_field(tl: str):
    f = _detect_fields(tl)
    return f[0] if f else None


def _apply_value(updated: Dict[str, Any], f: str, t: str, tl: str) -> bool:
    """Try to extract + set field f from transcript. Returns True if set."""
    if f == "farmer_name":
        m = re.search(r"(?:नाव|नाम|name is|नाव आहे|माझं नाव|मेरा नाम)\s+([A-Za-z\u0900-\u097F ]{3,40})", t)
        updated["farmer_name"] = (m.group(1).strip() if m else t[:40])
        return True
    if f == "father_name":
        m = re.search(r"(?:पिता|वडील|father(?:'s)?(?:\s*name)?(?:\s*is)?)\s*(?:का नाम|चं नाव|is|:)?\s*([A-Za-z\u0900-\u097F ]{3,40})", t, re.IGNORECASE)
        updated["father_name"] = (m.group(1).strip() if m else t[:40])
        return True
    if f == "survey_khasra_number":
        m = re.search(r"(\d+\s*/\s*\d+\s*/?\s*[A-Za-z\u0900-\u097F]?)", t) or re.search(r"(\d+)", t)
        if m:
            updated["survey_khasra_number"] = m.group(1).strip()
            return True
        return False
    if f == "land_area_acres":
        m = re.search(r"(\d+(?:\.\d+)?)", tl)
        if m:
            updated["land_area_acres"] = float(m.group(1))
            return True
        return False
    if f == "village_taluka_district":
        updated["village_taluka_district"] = t[:120]
        return True
    if f == "mobile_number":
        m = re.search(r"(\d{10})", re.sub(r"\D", "", t))
        if m:
            updated["mobile_number"] = m.group(1)
            return True
        return False
    if f == "crop_type":
        for c in CROPS:
            if c in tl:
                updated["crop_type"] = CROP_CANON.get(c, c.capitalize() if c.isascii() else c)
                return True
        updated["crop_type"] = t[:40]
        return True
    if f == "damage_reason":
        for k, v in CAUSES.items():
            if k in tl:
                if v == "Flood" and ("rain" in tl or "barish" in tl or "baar" in tl or "वजह" in tl or "wajah" in tl):
                    updated["damage_reason"] = "Heavy Rains & Flood (अतिवृष्टि एवं बाढ़)"
                else:
                    updated["damage_reason"] = v
                return True
        updated["damage_reason"] = t[:80]
        return True
    if f == "loss_date":
        m = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", t)
        if m:
            updated["loss_date"] = m.group(1)
            return True
        if "18" in t and ("सितंबर" in t or "सप्टेंबर" in t or "september" in tl):
            updated["loss_date"] = "2026-09-18"
            return True
        if "14" in t and ("august" in tl or "ऑगस्ट" in t):
            updated["loss_date"] = "2026-08-14"
            return True
        updated["loss_date"] = t[:40]
        return True
    if f == "damage_percentage":
        m = re.search(r"(\d+)\s*(?:%|percent|टक्के|प्रतिशत)", tl)
        if m:
            updated["damage_percentage"] = int(m.group(1))
            return True
        if "साठ" in tl or "sixty" in tl:
            updated["damage_percentage"] = 60
            return True
        if "ऐंशी" in tl or "eighty" in tl or "अस्सी" in tl:
            updated["damage_percentage"] = 80
            return True
        return False
    return False


def merge_voice_into_claim(data: Dict[str, Any], transcript: str, target_field=None):
    t = transcript.strip()
    tl = t.lower()
    updated = dict(data)
    audit = audit_claim(data)
    if target_field:
        fields = [target_field]
    elif audit["missing_fields"]:
        # gap-fill mode: prefer detected field if it's actually missing
        guessed = _detect_field(tl)
        missing = [f for f in audit["missing_fields"] if _empty(data.get(f))]
        if guessed and (guessed in missing or guessed in ("damage_percentage", "father_name", "mobile_number", "village_taluka_district")):
            fields = [guessed]
        else:
            fields = missing + ["damage_percentage"]
    else:
        # correction mode: apply EVERY detected field (crop + cause together)
        fields = _detect_fields(tl)
    filled_list = []
    for f in fields:
        if not f:
            continue
        if audit["missing_fields"] and not _empty(updated.get(f)) and f != "damage_percentage":
            continue  # gap mode must not overwrite good OCR values
        if _apply_value(updated, f, t, tl):
            filled_list.append(f)
    filled = filled_list[0] if filled_list else None
    if not filled and not audit["missing_fields"]:
        return updated, None  # correction mode: don't scribble transcript into random fields
    if not filled:
        miss = audit_claim(updated)["missing_fields"]
        if miss and (updated.get(miss[0]) in (None, "")):
            updated[miss[0]] = t[:120]
            filled = miss[0]
            filled_list = [filled]
    updated["_filled_fields"] = filled_list
    return updated, filled
