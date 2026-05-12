import os
import shutil
import json
from datetime import datetime
from src.services.extraction.vendor_detector import VendorDetector

# Configuration
SOURCE_DIR = "samples/Input_Bills"
DATASETS_DIR = "datasets"
OUTPUT_DIR = "output/regression"

# Counters
counters = {"NT": 0, "PEA": 0, "Water": 0, "Unknown": 0}
audit_log = []
bootstrap_report = {"total_files": 0, "providers": counters, "malformed": 0}

def classify(filename):
    # Simplified classification based on existing VendorDetector rules
    # In a real scenario, use OCR extraction here.
    name = filename.upper()
    if "NT" in name or "TOT" in name: return "NT"
    if "PEA" in name or "ไฟฟ้า" in name: return "PEA"
    if "WATER" in name or "ประปา" in name: return "Water"
    return "Unknown"

# Initialize
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Process
for root, _, files in os.walk(SOURCE_DIR):
    for file in files:
        if not file.endswith(".pdf"): continue
        
        bootstrap_report["total_files"] += 1
        src_path = os.path.join(root, file)
        
        # Classification
        provider = classify(file)
        if provider == "Unknown": bootstrap_report["malformed"] += 1
        
        # Incremental naming
        counters[provider] += 1
        new_name = f"{provider}_{datetime.now().year}_{counters[provider]:04d}.pdf"
        
        # Copy to raw_original
        target_raw = os.path.join(DATASETS_DIR, "raw_original", provider.lower(), new_name)
        os.makedirs(os.path.dirname(target_raw), exist_ok=True)
        shutil.copy2(src_path, target_raw)
        
        # Audit log entry
        audit_log.append(f"{src_path} -> {target_raw}")
        
        # Golden initialization
        if provider != "Unknown":
            target_golden = os.path.join(DATASETS_DIR, "golden", provider.lower(), new_name)
            os.makedirs(os.path.dirname(target_golden), exist_ok=True)
            shutil.copy2(src_path, target_golden)
            
            # Truth JSON
            truth = {
                "provider": provider,
                "bill_number": None,
                "account_number": None,
                "bill_date": None,
                "total_amount": None,
                "human_verified": False
            }
            with open(target_golden.replace(".pdf", ".truth.json"), "w", encoding="utf-8") as f:
                json.dump(truth, f, indent=4)

# Save reports
with open(os.path.join(OUTPUT_DIR, "bootstrap_report.json"), "w") as f:
    json.dump(bootstrap_report, f, indent=4)

with open(os.path.join(OUTPUT_DIR, "dataset_audit.txt"), "w") as f:
    f.write("\n".join(audit_log))
