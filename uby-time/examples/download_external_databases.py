#!/usr/bin/env python3
"""
Download 4 external databases suitable for UBY integration.

Downloads to data/raw/external/:
  - gvp/             : Smithsonian Global Volcanism Program (TSV)
  - nasa_exoplanets/ : NASA Exoplanet Archive (CSV via TAP)
  - itrdb/           : NOAA ITRDB tree-ring measurements (sample of .rwl files)
  - neotoma/         : Neotoma paleoecology dataset metadata (JSON via API)

UBY integration value:
  - ITRDB: annual-resolution, multi-site, fills 1-12 ka gap
  - GVP:   Holocene eruptions, fills LIP-modern gap
  - Neotoma: mixed-time-unit (radiocarbon vs cal yr BP), needs age model
  - NASA Exoplanet: cosmological axis extension
"""

from __future__ import annotations

import csv
import json
import ssl
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_DIR = ROOT / "data" / "raw" / "external"

USER_AGENT = "Mozilla/5.0 (UBY-Specification research pipeline)"

# Permissive SSL context (Smithsonian GVP serves a cert with hostname mismatch)
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _http_get(url: str, dest: Path, timeout: int = 60) -> bool:
    """Download a URL to dest. Returns True on success."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            data = resp.read()
        dest.write_bytes(data)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  [ERROR] {url}: {exc}")
        return False


def _http_get_text(url: str, timeout: int = 60) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        print(f"  [ERROR] {url}: {exc}")
        return None


# ---------------------------------------------------------------------------
# 1. Smithsonian Global Volcanism Program (via Smithsonian direct export)
# ---------------------------------------------------------------------------

def download_gvp() -> int:
    """Download GVP Holocene volcano list (Excel XML) + parse to CSV."""
    print("[1/4] Downloading Smithsonian GVP ...")
    out_dir = EXT_DIR / "gvp"
    _ensure_dir(out_dir)

    # Smithsonian provides an Excel XML download of the Holocene volcano list
    xml_url = "https://a.cf11.si.edu/database/list_volcano_holocene_excel.cfm"
    xml_dest = out_dir / "holocene_volcano_list.xls"
    print(f"  GET {xml_url} ...")
    if not _http_get(xml_url, xml_dest, timeout=180):
        return 0

    # Parse the XML Excel file to extract volcano records
    n = _parse_gvp_excel_xml(xml_dest, out_dir / "holocene_volcano_list.csv")
    print(f"  GVP: {n} Holocene volcanoes")
    return n


def _parse_gvp_excel_xml(xml_path: Path, csv_out: Path) -> int:
    """Parse Smithsonian's Excel XML ( SpreadsheetML 2003) into CSV.

    Uses lxml.etree (recover=True) which tolerates malformed characters
    that break stdlib ElementTree.
    """
    try:
        from lxml import etree
    except ImportError:
        print("  [ERROR] lxml required to parse GVP Excel XML")
        return 0

    # Recover mode tolerates malformed characters
    parser = etree.XMLParser(recover=True, encoding="utf-8")
    try:
        tree = etree.parse(str(xml_path), parser=parser)
    except Exception as exc:  # noqa: BLE001
        print(f"  [ERROR] lxml parse: {exc}")
        return 0

    NS = "{urn:schemas-microsoft-com:office:spreadsheet}"
    rows_data: list[list[str]] = []
    for row in tree.iter(f"{NS}Row"):
        cells: list[str] = []
        for cell in row.iter(f"{NS}Cell"):
            idx_attr = cell.attrib.get(f"{NS}Index")
            if idx_attr:
                idx = int(idx_attr) - 1
                while len(cells) < idx:
                    cells.append("")
            data_el = cell.find(f"{NS}Data")
            if data_el is not None and data_el.text is not None:
                cells.append(data_el.text)
            else:
                cells.append("")
        if cells:
            rows_data.append(cells)

    if not rows_data:
        print("  [WARN] no rows parsed from Excel XML")
        return 0

    max_w = max(len(r) for r in rows_data)
    for r in rows_data:
        while len(r) < max_w:
            r.append("")

    with csv_out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        for row in rows_data:
            writer.writerow(row)

    return max(0, len(rows_data) - 1)


# ---------------------------------------------------------------------------
# 2. NASA Exoplanet Archive (TAP API)
# ---------------------------------------------------------------------------

def download_nasa_exoplanets() -> int:
    """Download confirmed exoplanets CSV via TAP."""
    print("[2/4] Downloading NASA Exoplanet Archive ...")
    out_dir = EXT_DIR / "nasa_exoplanets"
    _ensure_dir(out_dir)

    # Default parameter sets only (deduplicated), CSV
    query = "select+*+from+ps+where+default_flag=1+order+by+pl_name"
    url = (
        "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?"
        f"query={query}&format=csv"
    )
    dest = out_dir / "confirmed_planets_default.csv"
    print(f"  GET {url[:90]} ...")
    ok = _http_get(url, dest, timeout=180)
    if not ok:
        return 0
    # Count rows (minus header)
    with dest.open("r", encoding="utf-8", errors="replace") as fh:
        n = sum(1 for _ in fh) - 1
    print(f"  NASA Exoplanet: {n} confirmed planets")
    return max(0, n)


# ---------------------------------------------------------------------------
# 3. NOAA ITRDB tree-ring measurements (sample)
# ---------------------------------------------------------------------------

def download_itrdb(limit: int = 0) -> int:
    """Download ITRDB chronology files (zipped per-continent packages).

    NOAA NCEI packages the full ITRDB v7.13 chronologies into 8 zip
    files by continent (~17.5 MB total). We download all 8 zips and
    extract .crn (chronology) files. Each .crn file is an annual-
    resolution time series for one site.
    """
    print("[3/4] Downloading NOAA ITRDB chronology packages ...")
    out_dir = EXT_DIR / "itrdb"
    _ensure_dir(out_dir)

    base = "https://www.ncei.noaa.gov/pub/data/paleo/treering/chronologies/"
    regions = [
        "africa",
        "asia",
        "australia",
        "canada",
        "europe",
        "mexico",
        "southamerica",
        "usa",
    ]

    n_files = 0
    for region in regions:
        zip_name = f"itrdb-v713-{region}-crn.zip"
        zip_url = base + zip_name
        zip_dest = out_dir / zip_name
        if not (zip_dest.exists() and zip_dest.stat().st_size > 0):
            print(f"  GET {zip_url} ...")
            if not _http_get(zip_url, zip_dest, timeout=180):
                continue
        # Extract .crn files
        try:
            import zipfile
            with zipfile.ZipFile(zip_dest, "r") as zf:
                members = [m for m in zf.namelist() if m.endswith(".crn")]
                extract_dir = out_dir / region
                _ensure_dir(extract_dir)
                for member in members:
                    # Skip directory entries
                    if member.endswith("/"):
                        continue
                    # Extract to region subdir, flatten filename
                    target_name = Path(member).name
                    target_path = extract_dir / target_name
                    if not target_path.exists():
                        with zf.open(member) as src, target_path.open("wb") as dst:
                            dst.write(src.read())
                n_files += len(members)
                print(f"    {region}: {len(members)} .crn chronologies extracted")
        except Exception as exc:  # noqa: BLE001
            print(f"  [ERROR] unzip {zip_name}: {exc}")
            continue

    print(f"  ITRDB: {n_files} .crn chronology files saved to {out_dir}")
    return n_files


# ---------------------------------------------------------------------------
# 4. Neotoma paleoecology (API)
# ---------------------------------------------------------------------------

def download_neotoma(limit: int = 1000) -> int:
    """Download Neotoma dataset metadata via API.

    We download metadata for datasets across multiple taxon groups
    (pollen, vertebrates, diatoms, ostracodes, plant macrofossils).
    Each record includes site, dataset type, and age range.
    Full sample downloads require a per-dataset API call (heavy); we
    capture metadata only.
    """
    print(f"[4/4] Downloading Neotoma (metadata, limit={limit}) ...")
    out_dir = EXT_DIR / "neotoma"
    _ensure_dir(out_dir)

    # Neotoma API: /v2.0/data/sites returns paginated site metadata
    base = "https://api.neotomadb.org/v2.0/data/sites"
    n_total = 0
    out_path = out_dir / "sites.jsonl"
    with out_path.open("w", encoding="utf-8") as out_fh:
        offset = 0
        page_size = 500
        while n_total < limit:
            limit_param = min(page_size, limit - n_total)
            url = f"{base}?limit={limit_param}&offset={offset}"
            print(f"  GET {url} ...")
            text = _http_get_text(url, timeout=120)
            if text is None:
                break
            try:
                obj = json.loads(text)
            except json.JSONDecodeError:
                print(f"  [WARN] non-JSON response, stopping")
                break
            sites = obj.get("data", [])
            if not sites:
                break
            for site in sites:
                out_fh.write(json.dumps(site, ensure_ascii=False) + "\n")
                n_total += 1
            if len(sites) < limit_param:
                break
            offset += page_size
            time.sleep(0.2)  # be polite
    print(f"  Neotoma: {n_total} site records saved to {out_path}")
    return n_total


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    _ensure_dir(EXT_DIR)
    print("=" * 70)
    print("UBY external databases download")
    print("=" * 70)

    t0 = time.time()
    n_gvp = download_gvp()
    n_exo = download_nasa_exoplanets()
    n_itrdb = download_itrdb(limit=0)
    n_neo = download_neotoma(limit=1000)
    dt = time.time() - t0

    print()
    print("=" * 70)
    print(f"Summary (wall={dt:.1f}s):")
    print(f"  GVP volcanoes+events : {n_gvp}")
    print(f"  NASA Exoplanets       : {n_exo}")
    print(f"  NOAA ITRDB (.rwl)    : {n_itrdb}")
    print(f"  Neotoma sites        : {n_neo}")
    print(f"  TOTAL records        : {n_gvp + n_exo + n_itrdb + n_neo}")
    print("=" * 70)

    # Write manifest
    manifest = {
        "generated_by": "UBY external databases download pipeline",
        "download_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sources": {
            "gvp": {
                "path": "data/raw/external/gvp/",
                "records": n_gvp,
                "attribution": "Smithsonian Global Volcanism Program; NOAA NCEI",
            },
            "nasa_exoplanets": {
                "path": "data/raw/external/nasa_exoplanets/",
                "records": n_exo,
                "attribution": "NASA Exoplanet Archive (Caltech/IPAC)",
            },
            "itrdb": {
                "path": "data/raw/external/itrdb/",
                "records": n_itrdb,
                "attribution": "NOAA NCEI Paleoclimatology / ITRDB",
                "note": "Sample of 200 .rwl chronologies; full ITRDB has 5000+",
            },
            "neotoma": {
                "path": "data/raw/external/neotoma/",
                "records": n_neo,
                "attribution": "Neotoma Paleoecology Database",
                "note": "Site metadata only; samples require per-dataset API calls",
            },
        },
    }
    manifest_path = EXT_DIR / "_external_databases_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nManifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
