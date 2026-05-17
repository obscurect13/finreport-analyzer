import json
import csv
import io
from typing import Dict

def generate_json(result: Dict) -> bytes:
    """Return a JSON representation of the analysis as UTF‑8 bytes."""
    return json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")

def generate_csv(result: Dict) -> bytes:
    """Return a CSV representation (KPIs as rows, other sections as single‑line fields)."""
    output = io.StringIO()
    writer = csv.writer(output)
    # Header row for KPIs
    writer.writerow(["KPI Name", "Value", "Variation", "Sens"])
    for kpi in result.get("kpis", []):
        writer.writerow([
            kpi.get("nom", ""),
            kpi.get("valeur", ""),
            kpi.get("variation", ""),
            kpi.get("sens", ""),
        ])
    # Add a blank line then other sections as simple key/value rows
    writer.writerow([])
    writer.writerow(["Section", "Content"])
    writer.writerow(["Executive Summary", result.get("resume", "")])
    writer.writerow(["Tone", result.get("ton", "")])
    writer.writerow(["Tone Reason", result.get("raison_ton", "")])
    writer.writerow(["Themes", ", ".join(result.get("themes", []))])
    writer.writerow(["Risks", ", ".join(result.get("risques", []))])
    writer.writerow(["Opportunities", ", ".join(result.get("opportunites", []))])
    return output.getvalue().encode("utf-8")
