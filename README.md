# iFlow → Technical Specification Document generator

Generates a Word (.docx) Technical Specification Document from an SAP
Integration Suite (Cloud Integration) iFlow package, matching the
FICOPROC TSD template's exact table format.

## Document structure

```
1. Participants
2. Process Overview
   2.1 Integration Process
   2.2 Local Integration Process
3. Pallet Function Details
   3.1 Content Modifier      <- ONE heading per TYPE. Every instance's
       [table: Set Order Headers]     table stacks directly underneath -
       [table: Set Retry Headers]     no "Instance 1/2" labels, each
   3.2 Router                         table's own Name row identifies it.
       [table incl. Route Conditions sub-table]
   ...
4. Connectivity
   4.1 HTTP Receiver
   ...
```

A pallet function type with zero occurrences gets no section at all. A
type that occurs but has no schema entry yet still gets a numbered
heading with a Name-only table (never invisible, never a raw dump).

## Three bugs fixed this round (all confirmed against a real production export)

**1. Tables were visually merging into one giant table.** This is a
real Word/python-docx behavior: two `<w:tbl>` elements placed
back-to-back with nothing between them render as a single continuous
table. Every table-creating helper in `generate_tsd.py`
(`new_table()`, `add_multi_column_table()`) now unconditionally emits
a spacer paragraph immediately after itself, so this can't recur.
Verified: zero consecutive-table violations across 192 tables in a
real 8,000-line production iFlow.

**2. Router's route conditions were never captured at all.** They
don't live on the Router element itself - they're on the outgoing
`bpmn2:sequenceFlow` elements (`name` + `conditionExpression` child),
with the gateway's own `default` attribute pointing at whichever
sequenceFlow is the default route. `parse_iflow.py` now extracts this
and `generate_tsd.py` renders it as its own Order/Route Name/
Conditional Expression/Default Route table, matching the template.

**3. Schema coverage had been over-trimmed.** Every pallet function
section from your original template is back (Security: Decryptor/
Encryptor/Signer/Verifier, Persistence: all Data Store ops + Persist +
Write Variables, Validator, all four Convertors, Encoder/Decoder
family, Aggregator/Gather/Join/Multicast, Filter, Message Digest,
Timer, Escalation End) - see the full list in `schema_map.py`.

## Correctness: verified vs. best-effort

SAP CPI reuses the same internal `activityType` for several visually
distinct pallet functions, disambiguated by a secondary property.
Missing this caused the original "Content Modifier shows as Content
Enricher" bug. `parse_iflow.py`'s `resolve_pallet_type()` is the single
place this is resolved, verified against a real export:

| Shared `activityType` | Disambiguated by | Resolves to |
|---|---|---|
| `Enricher` | presence of `bodyType` | Content Modifier / Content Enricher |
| `Script` | `subActivityType` | Groovy Script / Java Script |
| `Mapping` | `subActivityType` | XSLT / Message / Operation Mapping |
| `DBstorage` | `operation` | Get / Select / Write / Delete / Persist |
| `Splitter` | `splitType` | General / Iterating Splitter |
| `ProcessCallElement` | `subActivityType` (**exact** match to `"loopingprocess"` - a substring check was a bug caught during testing, since `"nonloopingprocess"` also contains "loop") | Process Call / Looping Process Call |

Also fixed: adapter `direction` is stored **lowercase** in real
exports, not `Direction`.

Every entry in `schema_map.py` carries `"verified": True/False`:
- **`True`** — property names checked against a real production
  `.iflw` export. Trust these.
- **`False`** — the table's **labels/structure match the template
  exactly**, but the underlying property key name is a best-effort
  guess from documentation/convention, not yet confirmed against a
  real export. If a field renders blank for a step you know is
  configured, open `parsed.json`, find that element's raw
  `properties`, and correct the key name in `schema_map.py` - it's a
  one-line fix, not a redesign, precisely because the structure is
  already right.

This is an honest tradeoff: showing the right template structure with
a possibly-wrong property key (which you can fix once you see it) beats
either (a) silently omitting the whole section, or (b) dumping every
raw property to guarantee something shows up, which is what caused the
"unnecessary backend details" complaint last round.

## Field-spec language (`schema_map.py`)

- `"PropKey"` — plain value, shown as-is.
- `"__NAME__"` — the element's own name.
- `{"bool": "PropKey"}` — a single ☑/☐ with no text label, for plain
  on/off template fields.
- `{"prop": "PropKey", "checkbox": ["OptA", "OptB"]}` — every option
  shown with a box, checked when the raw value textually matches.
- `{"prop": "PropKey", "checkbox": {"rawvalue": "Display Label"}}` —
  maps the raw *stored* value to the *displayed* label. Use whenever
  they differ (e.g. CPI stores Data Store visibility as
  `"local"`/`"global"`; the template shows "Integration Flow"/"Global").
- `["PropKeyA", "PropKeyB"]` — first non-empty wins (covers adapter
  versions that store the same concept under a different key).

## Nested "table inside a property" values

CPI stores Content Modifier's Message Header / Exchange Property
entries as a single property whose value is itself escaped XML
(`<row><cell id='Action'>Create</cell>...</row><row>...`).
`generate_tsd.py` detects this pattern on *any* property (not just
those two specific keys) and renders it as a proper Action/Name/Type/
Datatype/Value/Default table.

## Production-ready GitHub Actions workflow

`.github/workflows/generate-tsd.yml`:
- **Pinned dependency** (`requirements.txt` — `python-docx==1.1.2`,
  tested against this exact version, not just "latest").
- **Per-file validation** before anything is trusted: output file must
  exist, be non-trivially sized (catches near-empty/broken generation),
  and pass `zipfile.testzip()` (a docx *is* a zip archive - this
  catches truncated/corrupt output). A broken input zip is caught with
  a clear `::error::` annotation, not a silent partial success.
- **Artifact upload independent of the commit-back step** — the
  generated docx is always downloadable from the workflow run itself
  (Actions tab → run → Artifacts), even if branch protection or token
  permissions block the git push. This was a real gap in the previous
  version: if the push failed, the work was simply lost.
- **Concurrency control** so two pushes can't race to commit at once.
- Clear `::group::`/`::error::` annotations per file so a failure in
  one iFlow doesn't obscure what happened with the others.

Requires repo Settings → Actions → General → Workflow permissions set
to "Read and write permissions" for the commit-back step (the artifact
upload works regardless).

## Try it locally

```bash
pip install -r requirements.txt
python scripts/parse_iflow.py path/to/YourIFlow.zip parsed.json
python scripts/generate_tsd.py parsed.json YourIFlow_TSD.docx
```

## Extending coverage

Adding a type that isn't covered, or upgrading a `"verified": False`
entry once you've checked it, is editing one dict entry in
`schema_map.py` - no other code changes needed.
