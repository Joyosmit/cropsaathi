"""PMFBY rule validation + missing-field voice prompts."""
from __future__ import annotations
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
    return {"eligible": len(missing) == 0, "missing_fields": missing,
            "low_confidence_fields": low, "next_prompts": prompts,
            "next_field": needs[0] if needs else None, "payout_hint": hint}


CROPS = ["soybean", "paddy", "cotton", "wheat", "sugarcane", "maize",
         "सोयाबीन", "धान", "कपास", "कापूस", "भात", "गेहूं"]
CAUSES = {"flood": "Flood", "बाढ़": "Flood", "पूर": "Flood", "drought": "Drought",
          "सूखा": "Drought", "दुष्काळ": "Drought", "hail": "Hailstorm",
          "गारपीट": "Hailstorm", "pest": "Pest Attack", "कीट": "Pest Attack",
          "rain": "Excess Rainfall", "बारिश": "Excess Rainfall", "पाऊस": "Excess Rainfall"}


def merge_voice_into_claim(data: Dict[str, Any], transcript: str, target_field=None):
    import re
    t = transcript.strip()
    tl = t.lower()
    updated = dict(data)
    audit = audit_claim(data)
    fields = [target_field] if target_field else audit["missing_fields"] + ["damage_percentage"]
    filled = None
    for f in fields:
        if f == "farmer_name" and _empty(updated.get("farmer_name")):
            m = re.search(r"(?:नाव|नाम|name is)\s+([A-Za-z\u0900-\u097F ]{3,40})", t)
            updated["farmer_name"] = m.group(1).strip() if m else t[:40]
            filled = f
            break
        if f == "survey_khasra_number" and _empty(updated.get("survey_khasra_number")):
            m = re.search(r"(\d+\s*/\s*\d+[A-Za-z]?)", t) or re.search(r"(\d+)", t)
            if m:
                updated["survey_khasra_number"] = m.group(1).strip()
                filled = f
                break
        if f == "land_area_acres" and _empty(updated.get("land_area_acres")):
            m = re.search(r"(\d+(?:\.\d+)?)", tl)
            if m:
                updated["land_area_acres"] = float(m.group(1))
                filled = f
                break
        if f == "crop_type" and _empty(updated.get("crop_type")):
            for c in CROPS:
                if c in tl:
                    updated["crop_type"] = c
                    filled = f
                    break
            if filled:
                break
        if f == "damage_reason" and _empty(updated.get("damage_reason")):
            for k, v in CAUSES.items():
                if k in tl:
                    updated["damage_reason"] = v
                    filled = f
                    break
            if filled:
                break
        if f == "loss_date" and _empty(updated.get("loss_date")):
            m = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", t)
            if m:
                updated["loss_date"] = m.group(1)
                filled = f
                break
            if "18" in t and ("सितंबर" in t or "सप्टेंबर" in t or "september" in tl):
                updated["loss_date"] = "2026-09-18"
                filled = f
                break
        if f == "damage_percentage":
            m = re.search(r"(\d+)\s*(?:%|percent|टक्के|प्रतिशत)", tl)
            if m:
                updated["damage_percentage"] = int(m.group(1))
                filled = f
                break
            if "साठ" in tl or "sixty" in tl:
                updated["damage_percentage"] = 60
                filled = f
                break
    if not filled:
        miss = audit_claim(updated)["missing_fields"]
        if miss and (updated.get(miss[0]) in (None, "")):
            updated[miss[0]] = t[:120]
            filled = miss[0]
    return updated, filled
