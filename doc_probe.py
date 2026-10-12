import os, time, json
from dotenv import load_dotenv
load_dotenv("cropbima-express/backend/.env")
from sarvamai import SarvamAI
c = SarvamAI(api_subscription_key=os.getenv("SARVAM_API_KEY"))

def F(desc):
    return {"type": "string", "description": desc}

COMPLAINT_SCHEMA = json.dumps({
    "type": "object",
    "properties": {
        "farmer_name": F("Farmer name, field 1 किसान का नाम, e.g. रामभरोसे पटेल"),
        "father_name": F("Father name, field 2 पिता का नाम"),
        "village_taluka_district": F("Village/Taluka/District, field 3 गांव/तालुका/जिला"),
        "survey_number": F("Survey/Gat number, field 4 सर्वे/गट नंबर"),
        "crop_name": F("Insured crop, field 5 बीमित फसल"),
        "affected_area": F("Affected area with unit, field 6 प्रभावित क्षेत्र"),
        "date_of_loss": F("Date of loss, field 7 क्षति की तिथि"),
        "cause_of_loss": F("Cause of loss, field 8 क्षति का कारण"),
        "estimated_loss_pct": F("Estimated loss %, field 9 अनुमानित नुकसान"),
        "mobile_number": F("Mobile number, field 10 मोबाइल नंबर"),
    },
    "required": ["farmer_name", "survey_number", "crop_name"],
})

for path, mode in [("cropbima-express/test_data/sample_pmfby_form.png", "extract"),
                   ("cropbima-express/test_data/sample_712_extract.png", "digitise")]:
    print("=" * 60, "\nFILE:", path, mode)
    with open(path, "rb") as f:
        kw = {"file": [(os.path.basename(path), f, "image/png")], "language": "hi-IN"}
        if mode == "extract":
            kw.update({"schema": COMPLAINT_SCHEMA, "output_format": "json"})
            job = c.doc_ai.extract(**kw)
        else:
            kw.update({"output_format": "md"})
            job = c.doc_ai.digitise(**kw)
    print("job:", job.job_id)
    for _ in range(30):
        st = c.doc_ai.get_status(job_id=job.job_id)
        print(" status:", st.status)
        if st.status.lower() in ("completed", "partially_completed", "failed", "rejected"):
            break
        time.sleep(5)
    try:
        res = c.doc_ai.get_results(job_id=job.job_id)
        print("RESULT:", str(res.result)[:2500])
    except Exception as e:
        print("results err:", str(e)[:300])
    try:
        dl = c.doc_ai.get_download_url(job_id=job.job_id)
        print("DL:", dl.url[:120] if dl.url else None)
    except Exception as e:
        print("dl err:", str(e)[:200])
