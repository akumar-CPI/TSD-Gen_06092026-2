#!/usr/bin/env python3
"""
parse_iflow.py

Extracts a normalized JSON representation of every pallet function,
process (Integration Process / Local Integration Process / Exception
Sub Process), participant and adapter/channel from an SAP Integration
Suite iFlow design-time package (.zip containing a .iflw BPMN2 file).

Usage:
    python parse_iflow.py <path-to-iflow.zip> <output.json>

Nothing is dropped: every ifl:property found on every flow element is
captured, even if generate_tsd.py doesn't have an exact template layout
for that particular activityType yet.
"""
import sys
import os
import json
import zipfile
import tempfile
import xml.etree.ElementTree as ET

FLOW_NODE_TAGS = {
    "serviceTask", "callActivity", "scriptTask", "sendTask", "receiveTask",
    "exclusiveGateway", "parallelGateway", "inclusiveGateway",
    "startEvent", "endEvent", "intermediateCatchEvent",
    "intermediateThrowEvent", "boundaryEvent", "task",
}
PROCESS_TAGS = {"process", "subProcess"}


def local(tag):
    return tag.split('}')[-1] if '}' in tag else tag


def get_properties(elem):
    """Direct ifl:property key/value pairs on this element's extensionElements."""
    props = {}
    for child in elem:
        if local(child.tag) == "extensionElements":
            for prop in child:
                if local(prop.tag) == "property":
                    k = v = None
                    for pc in prop:
                        t = local(pc.tag)
                        if t == "key":
                            k = (pc.text or "").strip()
                        elif t == "value":
                            v = (pc.text or "").strip() if pc.text else ""
                    if k:
                        props[k] = v
    return props


def find_iflw(zip_path, extract_dir):
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(extract_dir)
    for root, _, files in os.walk(extract_dir):
        for f in files:
            if f.endswith(".iflw"):
                return os.path.join(root, f)
    raise FileNotFoundError(
        "No .iflw file found inside the package. Expected it under "
        "src/main/resources/scenarioflows/integrationflow/."
    )


def guess_package_name(extract_dir):
    # project.json / .project or manifest may hold the human readable name
    for fname in ("project.json",):
        candidate = os.path.join(extract_dir, fname)
        if os.path.isfile(candidate):
            try:
                with open(candidate) as f:
                    data = json.load(f)
                if isinstance(data, dict) and "name" in data:
                    return data["name"]
            except Exception:
                pass
    return os.path.basename(os.path.normpath(extract_dir))


def process_kind(elem, tag):
    """Classify a process/subProcess element into the TSD template's
    Integration Process / Local Integration Process / Exception Sub
    Process buckets. Best-effort heuristic - adjust as needed for your
    org's naming conventions."""
    name = (elem.get("name") or "").lower()
    triggered_by_event = elem.get("triggeredByEvent") == "true"
    if tag == "subProcess" and triggered_by_event:
        return "Exception Sub Process"
    if tag == "subProcess":
        return "Local Integration Process"
    if "local" in name:
        return "Local Integration Process"
    return "Integration Process"


# --------------------------------------------------------------------------
# SAP CPI reuses the same activityType for several visually distinct pallet
# functions (confirmed against real iFlow exports) and only disambiguates
# them via a secondary property. Without this, e.g. every Content Modifier
# gets mislabeled as Content Enricher, because both share activityType
# "Enricher". This function is the single place that resolves the *real*
# pallet function so schema_map.py can key off something reliable.
# --------------------------------------------------------------------------
def resolve_pallet_type(activity_type, props):
    if activity_type == "Enricher":
        # Content Modifier always carries a bodyType property (Constant/
        # Expression body); the legacy Content Enricher does not.
        return "ContentModifier" if "bodyType" in props else "ContentEnricher"
    if activity_type == "Script":
        # subActivityType literally holds "GroovyScript" or "JavaScript".
        return props.get("subActivityType") or "GroovyScript"
    if activity_type == "Mapping":
        # subActivityType holds "XSLTMapping" / "MessageMapping" /
        # "OperationMapping" - confirmed for XSLTMapping against a real
        # export; the other two are inferred by analogy.
        return props.get("subActivityType") or "MessageMapping"
    if activity_type == "DBstorage":
        op = (props.get("operation") or "").strip().lower()
        return {
            "get": "DBstorage_Get",
            "select": "DBstorage_Select",
            "write": "DBstorage_Write",
            "delete": "DBstorage_Delete",
            "persist": "DBstorage_Persist",
        }.get(op, "DBstorage_Get")
    if activity_type == "Splitter":
        # splitType literally holds "GeneralSplitter" / "IteratingSplitter" / etc.
        return props.get("splitType") or "GeneralSplitter"
    if activity_type == "ProcessCallElement":
        sub = (props.get("subActivityType") or "").strip().lower()
        # NOTE: "nonloopingprocess" contains the substring "loop" too, so
        # this must be an exact match, not a substring check.
        return "LoopingProcessCallElement" if sub == "loopingprocess" else "ProcessCallElement"
    return activity_type


def parse(zip_path):
    tmpdir = tempfile.mkdtemp(prefix="iflow_extract_")
    iflw_path = find_iflw(zip_path, tmpdir)
    package_name = guess_package_name(tmpdir)

    tree = ET.parse(iflw_path)
    root = tree.getroot()

    result = {
        "iflow_file": os.path.basename(iflw_path),
        "package_name": package_name,
        "participants": [],
        "adapters": [],
        "processes": [],
        "pallet_elements": [],
    }

    participant_by_id = {}

    # ---- Collaboration: participants + message flows (adapters) ----
    for collab in root.iter():
        if local(collab.tag) != "collaboration":
            continue
        for child in collab:
            ctag = local(child.tag)
            if ctag == "participant":
                pid = child.get("id")
                pname = child.get("name", "")
                pprops = get_properties(child)
                # ifl:type is an XML attribute (not a nested ifl:property)
                for attr_name, attr_val in child.attrib.items():
                    if local(attr_name) == "type" and attr_val:
                        pprops["ifl:type"] = attr_val
                participant_by_id[pid] = pname
                result["participants"].append({
                    "id": pid, "name": pname, "properties": pprops,
                })
            elif ctag == "messageFlow":
                mprops = get_properties(child)
                src = child.get("sourceRef")
                tgt = child.get("targetRef")
                # Real SAP exports use lowercase "direction" as the property
                # key (confirmed against production iFlow XML); some tooling
                # docs show "Direction" - accept either, prefer lowercase.
                direction = mprops.get("direction") or mprops.get("Direction", "")
                result["adapters"].append({
                    "id": child.get("id"),
                    "name": child.get("name", ""),
                    "source": participant_by_id.get(src, src),
                    "target": participant_by_id.get(tgt, tgt),
                    "component_type": mprops.get("ComponentType", ""),
                    "direction": direction,
                    "properties": mprops,
                })

    # ---- Router (exclusiveGateway) route conditions ----
    # Route conditions are NOT on the gateway element itself - they live on
    # the outgoing bpmn2:sequenceFlow elements (name + conditionExpression
    # child), with the gateway's own "default" attribute pointing at the
    # id of whichever sequenceFlow is the default/otherwise route. Missing
    # this entirely was a real gap - confirmed against a real export.
    sequence_flows_by_source = {}
    for sf in root.iter():
        if local(sf.tag) != "sequenceFlow":
            continue
        src = sf.get("sourceRef")
        cond = ""
        for c in sf:
            if local(c.tag) == "conditionExpression":
                cond = (c.text or "").strip()
        sequence_flows_by_source.setdefault(src, []).append({
            "id": sf.get("id"),
            "name": sf.get("name") or "",
            "condition": cond,
        })

    # ---- Processes + nested flow elements ----
    for proc in root.iter():
        tag = local(proc.tag)
        if tag not in PROCESS_TAGS:
            continue
        proc_id = proc.get("id")
        proc_name = proc.get("name", proc_id)
        kind = process_kind(proc, tag)
        proc_props = get_properties(proc)
        result["processes"].append({
            "id": proc_id, "name": proc_name, "kind": kind,
            "properties": proc_props,
        })

        for child in proc:
            ctag = local(child.tag)
            if ctag not in FLOW_NODE_TAGS:
                continue
            props = get_properties(child)
            activity_type = props.get("activityType", "")
            resolved_type = resolve_pallet_type(activity_type, props) if activity_type else ctag

            routes = None
            if ctag == "exclusiveGateway":
                default_id = child.get("default")
                outgoing = sequence_flows_by_source.get(child.get("id"), [])
                routes = []
                for idx, sf in enumerate(outgoing, start=1):
                    routes.append({
                        "Order": str(idx),
                        "Route Name": sf["name"],
                        "Conditional Expression": sf["condition"],
                        "Default Route": "Yes" if sf["id"] == default_id else "No",
                    })

            result["pallet_elements"].append({
                "id": child.get("id"),
                "name": child.get("name", child.get("id")),
                "xml_tag": ctag,
                "activity_type": activity_type,
                "resolved_type": resolved_type,
                "process_id": proc_id,
                "process_name": proc_name,
                "process_kind": kind,
                "properties": props,
                "routes": routes,
            })

    return result


def main():
    if len(sys.argv) != 3:
        print("Usage: python parse_iflow.py <iflow.zip> <output.json>")
        sys.exit(1)
    zip_path, out_path = sys.argv[1], sys.argv[2]
    data = parse(zip_path)
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Parsed {len(data['pallet_elements'])} pallet elements, "
          f"{len(data['adapters'])} adapters, "
          f"{len(data['processes'])} processes -> {out_path}")


if __name__ == "__main__":
    main()
