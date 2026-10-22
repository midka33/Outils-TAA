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

def evaluate(params, prefer_nominal=False):
    """Calcule une surface diagnostique, non une surface réglementaire.

    Pour les conventions TAA FEN-EXT/PORFEN-EXT, les cotes nominales
    Largeur x Hauteur priment sur la réservation brute de gros œuvre.
    Un paramètre explicitement nommé 'tableau' conserve la priorité.
    Si seules les cotes brutes existent, elles sont archivées dans candidates
    sans constituer une surface candidate automatique.
    """
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
    methods = dict((item["method"], item) for item in found)
    if prefer_nominal:
        # La cote 'brute' peut inclure coffre tunnel et tapées d'isolation.
        selected = methods.get("TABLEAU") or methods.get("NOMINALE")
    else:
        selected = (methods.get("TABLEAU") or methods.get("OUVERTURE_BRUTE")
                    or methods.get("NOMINALE"))
    if selected is None:
        comment = "Aucune paire de dimensions exploitable"
        if prefer_nominal and "OUVERTURE_BRUTE" in methods:
            comment = ("Convention TAA : largeur/hauteur nominales absentes ; "
                       "ne pas assimiler la réservation brute à la baie en tableau")
        return dict(selected=None, candidates=found, status="A_VERIFIER",
                    reason=" ; ".join(warnings + [comment]))
    reason = ["Correspondance avec l'ouverture en tableau non démontrée"]
    if prefer_nominal and selected["method"] == "NOMINALE":
        reason.append("Convention TAA : Largeur x Hauteur sans coffre tunnel ni tapées")
    reason += warnings
    if selected["width_origin"] != selected["height_origin"]:
        reason.append("Largeur et hauteur de portées différentes (type/occurrence)")
    for candidate in found:
        if candidate is not selected and abs(selected["area_m2"]-candidate["area_m2"]) > 0.01:
            reason.append("Ecart {} / {} : {:.3f} m²".format(
                selected["method"], candidate["method"],
                abs(selected["area_m2"]-candidate["area_m2"])))
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
                           facade_status=" | ".join(sorted(set(x.get("facade_status","") for x in items))),
                           rule_16_status=" | ".join(sorted(set(x.get("rule_16_status","") for x in items))),
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
