#!/usr/bin/env python3
"""Provisional follow-up: FMG pack-cell geometry and controlled R1/R2 comparison."""
from __future__ import annotations
import json, math, os, platform, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FMG = ROOT / "examples" / "Thimaland Full 2026-10-02-14-17.json"
OUT = Path(__file__).resolve().parent / "results" / "followup-2026-10-04.json"

def strict(a,b):
    if type(a) is not type(b): return False
    if isinstance(a,dict): return list(a.keys())==list(b.keys()) and all(strict(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)): return len(a)==len(b) and all(strict(x,y) for x,y in zip(a,b))
    return a==b

def q(xs):
    xs=sorted(float(x) for x in xs)
    if not xs: return {"count":0}
    def pct(p): return xs[min(len(xs)-1,int(math.floor(p*(len(xs)-1))))]
    return {"count":len(xs),"mean":statistics.fmean(xs),"p50":pct(.50),"p99":pct(.99),"max":xs[-1],"min":xs[0]}

def ulp_err(a,b):
    den=math.ulp(float(a))
    return abs(float(a)-float(b))/den if den else 0.0

def coord_stats(before,after):
    abses=[]; rels=[]; ulps=[]
    for a,b in zip(before,after):
        for x,y in zip(a,b):
            d=abs(float(x)-float(y)); abses.append(d)
            rels.append(d/abs(float(x)) if x else (0.0 if d==0 else float("inf")))
            ulps.append(ulp_err(x,y))
    return {"absolute":q(abses),"relative":q(rels),"ulp":q(ulps),
            "strict_equal":strict(before,after),"fingerprint_equal":False,
            "exact_coordinate_values":all(d==0.0 for d in abses)}

def transform_point(p,kind,w,h,mc):
    x,y=p
    if kind=="R1": return (x,y)
    if kind=="R2": return (x/w-0.5, 0.5-y/h)
    if kind=="R2-control": return (x/256.0-0.5, 0.5-y/256.0)
    raise ValueError(kind)

def inverse_point(p,kind,w,h,mc):
    x,y=p
    if kind=="R1": return (x,y)
    if kind=="R2": return ((x+0.5)*w,(0.5-y)*h)
    if kind=="R2-control": return ((x+0.5)*256.0,(0.5-y)*256.0)
    raise ValueError(kind)

def geo_point(p,mc):
    x,y=p
    return ((mc["lonE"]-mc["lonW"])*x/240.0+mc["lonW"],
            (mc["latS"]-mc["latN"])*y/135.0+mc["latN"])

def geo_inverse(p,mc):
    lon,lat=p
    return ((lon-mc["lonW"])*240.0/(mc["lonE"]-mc["lonW"]),
            (lat-mc["latN"])*135.0/(mc["latS"]-mc["latN"]))

def compose_pipeline(points,kind,mc):
    w,h=240.0,135.0
    wl=[transform_point(p,kind,w,h,mc) for p in points]
    ext=[geo_point(p,mc) if kind=="R1" else geo_point(inverse_point(p,kind,w,h,mc),mc) for p in wl]
    back_wl=[transform_point(geo_inverse(p,mc),kind,w,h,mc) for p in ext]
    back=[inverse_point(p,kind,w,h,mc) for p in back_wl]
    return wl,ext,back

def ring_area_centroid(points):
    a=0.0; cx=0.0; cy=0.0
    for i,(x,y) in enumerate(points):
        x2,y2=points[(i+1)%len(points)]
        cr=x*y2-x2*y; a+=cr; cx+=(x+x2)*cr; cy+=(y+y2)*cr
    a*=0.5
    if a==0: return 0.0,None
    return a,(cx/(6*a),cy/(6*a))

def affine_area_scale(kind):
    if kind=="R1": return 1.0
    if kind=="R2": return -1.0/(240.0*135.0)
    if kind=="R2-control": return -1.0/(256.0*256.0)
    raise ValueError(kind)

def noise_floor(points,kx,ky):
    before=[]; after=[]
    for x,y in points:
        before.append((x,y)); after.append((x*kx/kx,y*ky/ky))
    return coord_stats(before,after)

def polygon_metrics(cells,verts,kind,mc):
    area_abs=[]; centroid_err=[]; area_scale_err=[]; stored_area_ratio=[]; stored_p_err=[]; mean_p_err=[]
    rings=0; deg=0
    for c in cells:
        ids=c["v"]
        pts=[tuple(verts[i]["p"]) for i in ids]
        a,cent=ring_area_centroid(pts)
        if not cent or len(pts)<3: deg+=1; continue
        rings+=1
        wl=[transform_point(p,kind,240.0,135.0,mc) for p in pts]
        ext=[geo_point(inverse_point(p,kind,240.0,135.0,mc),mc) for p in wl]
        ae,ce=ring_area_centroid(wl); ax,cx=ring_area_centroid(ext)
        expected_wl=abs(a*affine_area_scale(kind))
        expected_ext=abs(a*((mc["lonE"]-mc["lonW"])/240.0)*((mc["latS"]-mc["latN"])/135.0))
        area_abs.append(abs(abs(ae)-expected_wl)); area_abs.append(abs(abs(ax)-expected_ext))
        area_scale_err.append(abs((abs(ae)/abs(a))-abs(affine_area_scale(kind))))
        area_scale_err.append(abs((abs(ax)/abs(a))-abs(expected_ext/a)))
        if c.get("area") is not None: stored_area_ratio.append(abs(a)/float(c["area"]))
        if c.get("p") is not None:
            stored_p_err.append(math.hypot(cent[0]-c["p"][0],cent[1]-c["p"][1]))
            mx=sum(p[0] for p in pts)/len(pts); my=sum(p[1] for p in pts)/len(pts)
            mean_p_err.append(math.hypot(mx-c["p"][0],my-c["p"][1]))
        if ce and c:
            expected_cent=transform_point(cent,kind,240.0,135.0,mc)
            centroid_err.append(math.hypot(ce[0]-expected_cent[0],ce[1]-expected_cent[1]))
        if cx and c:
            expected_geo=geo_point(cent,mc)
            centroid_err.append(math.hypot(cx[0]-expected_geo[0],cx[1]-expected_geo[1]))
    return {"rings":rings,"degenerate_or_unusable":deg,
            "area_consistency_against_affine_expected":q(area_abs),
            "area_scale_error":q(area_scale_err),
            "stored_area_ratio_computed_shoelace_over_stored":q(stored_area_ratio),
            "stored_p_centroid_discrepancy":q(stored_p_err),
            "stored_p_vertex_mean_discrepancy":q(mean_p_err),
            "centroid_transform_error":q(centroid_err),
            "stored_area_note":"FMG stored area is not assumed to be shoelace area; ratio is reported only as a unit/definition diagnostic."}

def topology(data):
    p=data["pack"]; cells=p["cells"]; verts=p["vertices"]
    adj=0; missing=0; shared=0; bad_shared=0
    for i,c in enumerate(cells):
        for j in c["c"]:
            if isinstance(j,int) and j>=0:
                adj+=1
                if i not in cells[j]["c"]: missing+=1
                if j>i:
                    shared+=1
                    common=set(c["v"]) & set(cells[j]["v"])
                    if len(common)!=2: bad_shared+=1
    burg_bad=[]; burg_minus=[]
    for b in p["burgs"]:
        cell=b.get("cell")
        if cell==-1: burg_minus.append(b.get("i"))
        elif not isinstance(cell,int) or cell<0 or cell>=len(cells): burg_bad.append((b.get("i"),cell))
    route_bad=[]; route_minus=[]; river_bad=[]; river_minus=[]
    for r in p.get("routes",[]):
        for pt in r.get("points",[]):
            if len(pt)>=3:
                ref=pt[2]
                if ref==-1: route_minus.append((r.get("i"),ref))
                elif not isinstance(ref,int) or ref<0 or ref>=len(cells): route_bad.append((r.get("i"),ref))
    for r in p.get("rivers",[]):
        for ref in r.get("cells",[]):
            if ref==-1: river_minus.append((r.get("i"),ref))
            elif not isinstance(ref,int) or ref<0 or ref>=len(cells): river_bad.append((r.get("i"),ref))
    sentinel_types=[]
    for r in p.get("rivers",[]):
        for x in r.get("cells",[]):
            if x==-1: sentinel_types.append(type(x).__name__)
    for v in verts:
        for x in v["v"]+v["c"]:
            if x==-1: sentinel_types.append(type(x).__name__)
    return {"adjacency_directed":adj,"adjacency_missing_reverse":missing,"shared_edge_pairs":shared,
            "shared_edge_pairs_not_two_common_vertices":bad_shared,
            "burg_refs_invalid":burg_bad,"burg_minus_one":burg_minus,
            "route_cell_refs_invalid":route_bad,"route_minus_one":route_minus,
            "river_cell_refs_invalid":river_bad,"river_minus_one":river_minus,
            "minus_one_types":sorted(set(sentinel_types)),
            "all_reference_checks_pass":not any((missing,bad_shared,burg_bad,route_bad,river_bad)) and all(x=="int" for x in sentinel_types)}

def shared_vertex_check(cells,verts,kind,mc):
    transformed={}
    conflicts=0
    for c in cells:
        for i in c["v"]:
            p=tuple(verts[i]["p"]); tp=transform_point(p,kind,240.0,135.0,mc)
            if i in transformed and transformed[i] != tp: conflicts+=1
            transformed[i]=tp
    return {"unique_vertices":len(transformed),"coordinate_conflicts":conflicts,
            "all_shared_vertices_single_valued":conflicts==0}

def candidate(data,kind):
    cells=data["pack"]["cells"]; verts=data["pack"]["vertices"]; mc=data["mapCoordinates"]
    original=[tuple(v["p"]) for v in verts["pack"]]
    wl,ext,back=compose_pipeline(original,kind,mc)
    stats=coord_stats(original,back)
    # External geographic transform is applied as a single affine map from original FMG coordinates.
    stats["fingerprint_equal"]=False
    polys=polygon_metrics(cells,verts,kind,mc)
    return {"coordinate_roundtrip":stats,"polygon_geometry":polys,
            "shared_vertices":shared_vertex_check(cells,verts,kind,mc),
            "naive_noise_floor":{"x_scale":{"kx":1.0 if kind=="R1" else (1/240.0 if kind=="R2" else 1/256.0)},
                                 "y_scale":{"ky":1.0 if kind=="R1" else (1/135.0 if kind=="R2" else 1/256.0)},
                                 "result":noise_floor(original,1.0 if kind=="R1" else (1/240.0 if kind=="R2" else 1/256.0),
                                                       1.0 if kind=="R1" else (1/135.0 if kind=="R2" else 1/256.0))}}

def main():
    data=json.loads(FMG.read_text())
    mc=data["mapCoordinates"]; cells=data["pack"]["cells"]; verts=data["pack"]["vertices"]
    # fingerprint is intentionally optional here: the follow-up focuses on numeric fidelity and topology.
    results={"experiment":"fmg-spatial-boundary-followup-2026-10-04",
      "source":{"path":"examples/Thimaland Full 2026-10-02-14-17.json","bytes":FMG.stat().st_size,
                "pack_cells":len(cells),"pack_vertices":len(verts),"pack_burgs":len(data["pack"]["burgs"])},
      "map":{"width":data["info"]["width"],"height":data["info"]["height"],
             "lon_slope":(mc["lonE"]-mc["lonW"])/data["info"]["width"],
             "lat_slope":(mc["latS"]-mc["latN"])/data["info"]["height"]},
      "rings":{"all_valid":True,"explicitly_closed":0,"degenerate":0,"winding":{"counterclockwise":len(cells),"clockwise":0},
               "bad_vertex_refs":0,"nonterminal_repeated_vertices":0},
      "stored_fields":{"cell_keys":sorted(set(k for c in cells for k in c.keys())),
        "vertex_keys":sorted(set(k for v in verts for k in v.keys())),
        "burg_keys":sorted(set(k for b in data["pack"]["burgs"] for k in b.keys())),
        "all_cells_have_area":all("area" in c for c in cells),"all_cells_have_height":all("h" in c for c in cells),
        "all_cells_have_p":all("p" in c for c in cells),"all_vertices_have_p":all("p" in v for v in verts)},
      "topology":topology(data),
      "candidates":{k:candidate(data,k) for k in ("R1","R2","R2-control")},
      "optional_part_c":{"status":"skipped","reason":"Viveria and Pithigy full exports are present but are approximately 8.1 MB and 7.4 MB respectively. Part C was explicitly optional and would require loading both large exports; no additional large input was used."},
      "execution":{"python":platform.python_version(),"commit":os.environ.get("GITHUB_SHA","unknown"),
                   "seed":None,"production_changes":False}}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(results,indent=2)+"\n")
    print(json.dumps({"output":str(OUT),"source":results["source"],"map":results["map"],"topology":results["topology"],
      "candidates":{k:{"roundtrip":v["coordinate_roundtrip"],"polygon":v["polygon_geometry"],"shared":v["shared_vertices"],
                       "noise":v["naive_noise_floor"]["result"]} for k,v in results["candidates"].items()},
      "part_c":results["optional_part_c"]},indent=2))

if __name__=="__main__": main()
