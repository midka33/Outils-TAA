# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import unicodedata

PAIRS = (
 ("TABLEAU", ("largeur tableau","largeur en tableau","tableau largeur","width tableau"), ("hauteur tableau","hauteur en tableau","tableau hauteur","height tableau")),
 ("OUVERTURE_BRUTE", ("rough width","largeur brute","largeur ouverture","largeur de l ouverture","largeur baie","largeur de baie"), ("rough height","hauteur brute","hauteur ouverture","hauteur de l ouverture","hauteur baie","hauteur de baie")),
 ("NOMINALE", ("width","largeur","nominal width","largeur nominale"), ("height","hauteur","nominal height","hauteur nominale")),
)

def normalize_name(value):
    value = unicodedata.normalize("NFKD", (value or "").lower())
    value = "".join(c for c in value if not unicodedata.combining(c))
    for c in "_-./:;()[]'’":
        value = value.replace(c, " ")
    return " ".join(value.split())

def _pick(params, aliases):
    values = []
    for item in params or []:
        if normalize_name(item.get("name")) not in aliases:
            continue
        try:
            x = float(item.get("value_m"))
        except (TypeError, ValueError):
            continue
        if 0 < x < 100:
            values.append(item)
    for origin in ("occurrence", "type"):
        same = [p for p in values if p.get("origin") == origin]
        if same:
            numbers = [float(p["value_m"]) for p in same]
            if max(numbers) - min(numbers) > 0.001:
                return None, "Valeurs contradictoires ({})".format(origin)
            return same[0], None
    return None, None

def evaluate(params):
    found, warnings = [], []
    for method, widths, heights in PAIRS:
        w, werr = _pick(params, widths)
        h, herr = _pick(params, heights)
        if werr or herr:
            warnings.append("{} : {}".format(method, "; ".join(x for x in (werr,herr) if x)))
        if w and h and not (werr or herr):
            found.append(dict(method=method, width_m=float(w["value_m"]), height_m=float(h["value_m"]),
                              area_m2=float(w["value_m"])*float(h["value_m"]),
                              width_parameter=w["name"], height_parameter=h["name"],
                              width_origin=w["origin"], height_origin=h["origin"]))
    selected = next((x for x in found if x["method"] in ("TABLEAU","OUVERTURE_BRUTE")), None)
    if selected is None:
        selected = next((x for x in found if x["method"]=="NOMINALE"), None)
    if selected is None:
        return dict(selected=None, candidates=found, status="A_VERIFIER",
                    reason=" ; ".join(warnings) or "Aucune paire de dimensions exploitable")
    nominal = next((x for x in found if x["method"]=="NOMINALE"), None)
    reason = ["Correspondance avec l'ouverture en tableau non démontrée"] + warnings
    if selected["width_origin"] != selected["height_origin"]:
        reason.append("Largeur et hauteur de portées différentes (type/occurrence)")
    if nominal and nominal is not selected and abs(selected["area_m2"]-nominal["area_m2"])>0.01:
        reason.append("Écart nominal/tableau ou brut : {:.3f} m²".format(abs(selected["area_m2"]-nominal["area_m2"])))
    status={"TABLEAU":"CANDIDAT_TABLEAU", "OUVERTURE_BRUTE":"CANDIDAT_OUVERTURE",
            "NOMINALE":"NOMINAL_A_CONFIRMER"}[selected["method"]]
    if warnings:
        status="A_VERIFIER"
    return dict(selected=selected, candidates=found, status=status, reason=" ; ".join(reason))

def aggregate_by_type(rows):
    groups={}
    for item in rows:
        key=(item.get("source_id",""),item.get("family",""),item.get("type",""))
        groups.setdefault(key,[]).append(item)
    output=[]
    for key in sorted(groups):
        items=groups[key]
        distinct=set((str(x.get("area_m2","")), x.get("status",""),x.get("method","")) for x in items)
        output.append(dict(source=items[0].get("source",""),source_id=key[0],
                           family=key[1],type=key[2],count=len(items),
                           status=items[0].get("status","") if len(distinct)==1 else "VARIABLE_SELON_OCCURRENCE",
                           methods=" | ".join(sorted(set(x.get("method","") for x in items))),
                           areas_m2=" | ".join(sorted(set(str(x.get("area_m2","")) for x in items))),
                           examples=" | ".join(str(x.get("element_id","")) for x in items[:5])))
    return output

def csv_escape(value):
    try:
        unicode_type = unicode
    except NameError:
        unicode_type = str
    value = "" if value is None else (value if isinstance(value,unicode_type) else unicode_type(value))
    return '"' + value.replace('"','""').replace("\n"," ").replace("\r"," ") + '"'

def csv_content(rows, fields):
    lines=[";".join(csv_escape(k) for k in fields)]
    for item in rows:
        lines.append(";".join(csv_escape(item.get(k,"")) for k in fields))
    return "\r\n".join(lines)+"\r\n"
