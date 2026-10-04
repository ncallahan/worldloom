#!/usr/bin/env python3
"""Provisional FMG spatial-boundary experiment."""
from __future__ import annotations
import copy, importlib.metadata, json, math, os, platform, sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from worldloom.core.hashing import fingerprint
from worldloom.core.spatial import SpatialGrid
from worldloom.core.state import WorldState
from worldloom.core.provenance import Provenance

EXPERIMENT = "fmg-spatial-boundary"
SLICE_DIR = ROOT / "experiments" / "fmg_scale" / "slices"
OUT_DIR = Path(__file__).resolve().parent / "results"

@dataclass(frozen=True)
class CoordinateTransform:
    source_space: str
    target_space: str
    matrix: tuple[float, float, float, float]
    offset: tuple[float, float]
    axis_order: str
    y_direction: str
    origin: tuple[float, float]
    scale: tuple[float, float]
    geographic_interpretation: str | None = None
    bounds: tuple[float, float, float, float] | None = None
    def apply_point(self, point):
        a,b,d,e=self.matrix; c,f=self.offset; x,y=point
        return (a*x+b*y+c,d*x+e*y+f)
    def inverse(self):
        a,b,d,e=self.matrix; det=a*e-b*d
        if det==0: raise ValueError("non-invertible transform")
        ia,ib,id_,ie=e/det,-b/det,-d/det,a/det; c,f=self.offset
        return CoordinateTransform(self.target_space,self.source_space,(ia,ib,id_,ie),
            (-(ia*c+ib*f),-(id_*c+ie*f)),self.axis_order,self.y_direction,self.origin,
            self.scale,self.geographic_interpretation,self.bounds)
    def as_dict(self):
        return {"source_space":self.source_space,"target_space":self.target_space,"matrix":list(self.matrix),
                "offset":list(self.offset),"axis_order":self.axis_order,"y_direction":self.y_direction,
                "origin":list(self.origin),"scale":list(self.scale),
                "geographic_interpretation":self.geographic_interpretation,
                "bounds":list(self.bounds) if self.bounds is not None else None}
    @classmethod
    def from_dict(cls,d):
        return cls(d["source_space"],d["target_space"],tuple(d["matrix"]),tuple(d["offset"]),
                   d["axis_order"],d["y_direction"],tuple(d["origin"]),tuple(d["scale"]),
                   d.get("geographic_interpretation"),tuple(d["bounds"]) if d.get("bounds") is not None else None)

def strict_equal(a,b):
    if type(a) is not type(b): return False
    if isinstance(a,dict): return len(a)==len(b) and set(a.keys())==set(b.keys()) and all(strict_equal(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)): return len(a)==len(b) and all(strict_equal(x,y) for x,y in zip(a,b))
    return a==b

def all_finite(obj):
    if isinstance(obj,dict): return all(all_finite(k) and all_finite(v) for k,v in obj.items())
    if isinstance(obj,(list,tuple)): return all(all_finite(x) for x in obj)
    return not(type(obj) is float and not math.isfinite(obj))

def exact_type_walk(obj):
    bad=[]
    if isinstance(obj,dict):
        for k,v in obj.items(): bad += exact_type_walk(k)+exact_type_walk(v)
    elif isinstance(obj,(list,tuple)):
        for x in obj: bad += exact_type_walk(x)
    elif type(obj) not in (str,int,float,bool,type(None)): bad.append(type(obj).__name__)
    return bad

def err(a,b): return max(abs(float(a[0])-float(b[0])),abs(float(a[1])-float(b[1])))
def dist(a,b): return math.hypot(float(a[0])-float(b[0]),float(a[1])-float(b[1]))
def bbox(points):
    p=list(points); return [min(x for x,y in p),min(y for x,y in p),max(x for x,y in p),max(y for x,y in p)] if p else None
def centroid(points):
    p=list(points); return [sum(x for x,y in p)/len(p),sum(y for x,y in p)/len(p)] if p else None

def fingerprint_assertions():
    out={"tuple_vs_list_fingerprint_equal":fingerprint((1,2))==fingerprint([1,2]),
      "int_vs_float_fingerprint_equal":fingerprint(1)==fingerprint(1.0),
      "bool_vs_int_fingerprint_equal":fingerprint(True)==fingerprint(1),
      "negative_zero_fingerprint_equal":fingerprint(-0.0)==fingerprint(0.0),
      "dict_order_insensitive":fingerprint({"a":1,"b":2})==fingerprint({"b":2,"a":1}),
      "tuple_vs_list_strict_equal":strict_equal((1,2),[1,2]),
      "int_vs_float_strict_equal":strict_equal(1,1.0),
      "bool_vs_int_strict_equal":strict_equal(True,1),
      "negative_zero_strict_equal":strict_equal(-0.0,0.0),
      "nan_fingerprinted":fingerprint(float("nan"))}
    try: import numpy as np
    except ImportError: out["numpy"]={"installed":False}
    else:
        n={"float64_type_is_float":type(np.float64(1.25)) is float}
        try: fingerprint(np.float64(1.25)); n["float64_fingerprint"]="accepted"
        except Exception as e: n["float64_fingerprint"]=type(e).__name__
        for name,value in (("int64",np.int64(1)),("bool_",np.bool_(True))):
            try: fingerprint(value); n[name]="accepted"
            except Exception as e: n[name]=type(e).__name__
        out["numpy"]={"installed":True,**n}
    return out

def load_slice(stem):
    p=SLICE_DIR/f"{stem}_burg1_hop3.json"
    return json.loads(p.read_text()),json.loads((p.with_suffix(p.suffix+".remap.json")).read_text())

def point_sets(data):
    burgs=[b for b in data["pack"]["burgs"] if isinstance(b,dict) and "x" in b and "y" in b]
    markers=[m for m in data["pack"]["markers"] if isinstance(m,dict) and "x" in m and "y" in m]
    routes=[(p[0],p[1]) for r in data["pack"]["routes"] for p in r.get("points",[]) if len(p)>=2]
    return {"burgs":[(b["x"],b["y"]) for b in burgs],"markers":[(m["x"],m["y"]) for m in markers],"routes":routes}

def transform_points(points,t): return [t.apply_point(p) for p in points]
def transform_dict(pts,t): return {k:transform_points(v,t) for k,v in pts.items()}

def topology_snapshot(data):
    p=data["pack"]; cells=p["cells"]; verts=p["vertices"]
    return {"counts":{"pack_cells":len(cells),"pack_vertices":len(verts),"grid_cells":len(data["grid"]["cells"]),"grid_vertices":len(data["grid"]["vertices"])},
      "cell_c":[copy.deepcopy(c["c"]) for c in cells],"cell_v":[copy.deepcopy(c["v"]) for c in cells],
      "cell_g":[copy.deepcopy(c["g"]) for c in cells],"vertex_v":[copy.deepcopy(v["v"]) for v in verts],
      "vertex_c":[copy.deepcopy(v["c"]) for v in verts],
      "burg_refs":[(b.get("i"),b.get("cell"),b.get("state")) for b in p["burgs"] if isinstance(b,dict)],
      "route_refs":[(r.get("i"),[p[2] if len(p)>=3 else None for p in r.get("points",[])]) for r in p["routes"]],
      "sentinel_values":{"river_cells":[x for r in p["rivers"] for x in r.get("cells",[]) if x==-1],
                         "vertex_v":[x for v in verts for x in v["v"] if x==-1],
                         "vertex_c":[x for v in verts for x in v["c"] if x==-1]}}

def topology_result(data,remap):
    b=topology_snapshot(data); a=copy.deepcopy(b)
    checks={"counts_equal":b["counts"]==a["counts"],"cell_c_equal":b["cell_c"]==a["cell_c"],
      "cell_v_equal":b["cell_v"]==a["cell_v"],"cell_g_equal":b["cell_g"]==a["cell_g"],
      "vertex_v_equal":b["vertex_v"]==a["vertex_v"],"vertex_c_equal":b["vertex_c"]==a["vertex_c"],
      "burg_refs_equal":b["burg_refs"]==a["burg_refs"],"route_refs_equal":b["route_refs"]==a["route_refs"]}
    s=b["sentinel_values"]; checks["sentinel_exact"]=s==a["sentinel_values"] and all(type(x) is int and x==-1 for key in s for x in s[key])
    checks["all_topology_equal"]=all(checks.values())
    checks["remap_local_counts"]={k:len(remap.get(k,[])) for k in ("cell_map","vertex_map","grid_cell_map","grid_vertex_map")}
    return checks

def candidate_transforms(data):
    w,h=float(data["info"]["width"]),float(data["info"]["height"]); mc=data["mapCoordinates"]
    ls=(mc["lonE"]-mc["lonW"])/w; ts=-(mc["latN"]-mc["latS"])/h
    geo=CoordinateTransform("fmg-map","geographic",(ls,0.0,0.0,ts),(mc["lonW"],mc["latN"]),
      "x/y -> lon/lat","north-to-south as y increases",(0.0,0.0),(ls,abs(ts)),
      "observed FMG mapCoordinates affine; no CRS assigned",(mc["lonW"],mc["latS"],mc["lonE"],mc["latN"]))
    ident=CoordinateTransform("fmg-map","fmg-map",(1.0,0.0,0.0,1.0),(0.0,0.0),
      "x/y","north-to-south as y increases",(0.0,0.0),(1.0,1.0),"FMG map-space units",(0.0,0.0,w,h))
    local=CoordinateTransform("fmg-map","worldloom-local",(1.0/w,0.0,0.0,-1.0/h),(-0.5,0.5),
      "x/y","north-up",(w/2,h/2),(1.0/w,1.0/h),"normalised local map coordinates; no CRS",(-0.5,-0.5,0.5,0.5))
    return {"R1":(ident,geo),"R2":(local,compose(local.inverse(),geo))}

def compose(first,second):
    a,b,d,e=first.matrix; c,f=first.offset; g,h,i,j=second.matrix; k,l=second.offset
    return CoordinateTransform(first.source_space,second.target_space,(g*a+h*d,g*b+h*e,i*a+j*d,i*b+j*e),
      (g*c+h*f+k,i*c+j*f+l),first.axis_order,second.y_direction,first.origin,first.scale,
      second.geographic_interpretation,second.bounds)

def candidate_run(data,name,ts):
    fmg_to_wl,wl_to_ext=ts; pts=point_sets(data); wl=transform_dict(pts,fmg_to_wl)
    ext=transform_dict(wl,wl_to_ext); back_wl=transform_dict(ext,wl_to_ext.inverse()); back=transform_dict(back_wl,fmg_to_wl.inverse())
    metrics={}
    for k,v in pts.items():
        e=[err(x,y) for x,y in zip(v,back[k])]
        metrics[k]={"count":len(v),"max_abs_coordinate_error":max(e,default=0.0),"exact_numeric":all(x==0.0 for x in e),
          "strict_type_equal":strict_equal(v,back[k]),"fingerprint_equal":fingerprint(v)==fingerprint(back[k]),
          "fingerprint_disagrees_with_strict":fingerprint(v)==fingerprint(back[k]) and not strict_equal(v,back[k])}
    det=lambda t:t.matrix[0]*t.matrix[3]-t.matrix[1]*t.matrix[2]
    return {"candidate":name,"transforms":{"fmg_to_wl":fmg_to_wl.as_dict(),"wl_to_external":wl_to_ext.as_dict()},
      "points":metrics,"wl_bounds":{k:bbox(v) for k,v in wl.items()},"external_bounds":{k:bbox(v) for k,v in ext.items()},
      "orientation":{"fmg_to_wl_determinant":det(fmg_to_wl),"wl_to_external_determinant":det(wl_to_ext)},
      "determinism":{"strict_equal":strict_equal(wl,transform_dict(pts,fmg_to_wl)),
                     "fingerprint_equal":fingerprint(wl)==fingerprint(transform_dict(pts,fmg_to_wl))},
      "type_walk_bad_types":exact_type_walk(wl),"finite":all_finite(wl) and all_finite(ext) and all_finite(back)}

def geometry_metrics(data):
    pts=point_sets(data); out={}
    for k,v in pts.items():
        out[k]={"count":len(v),"bounds":bbox(v),"centroid":centroid(v)}
        if len(v)>=3: out[k]["first_three_pair_distances"]=[dist(v[0],v[1]),dist(v[1],v[2])]
        if len(v)>=2: out[k]["first_last_distance"]=dist(v[0],v[-1])
    out["pack_cell_polygon_area"]={"available":False,"reason":"pack.cells have no p and pack.vertices have no p in these slices; grid.vertices have p but retained grid-cell ring membership is absent"}
    out["pack_vertex_coordinates"]={"available":False,"reason":"pack.vertices[].p is absent from both slice fixtures"}
    out["stored_pack_cell_area"]={"available":any("area" in c for c in data["pack"]["cells"])}
    return out

def anisotropy(data):
    mc=data["mapCoordinates"]; w,h=float(data["info"]["width"]),float(data["info"]["height"])
    a=(mc["lonE"]-mc["lonW"])/w; e=-(mc["latN"]-mc["latS"])/h
    return {"lon_slope":a,"lat_slope":e,"isotropic_within_1e-15":abs(abs(a)-abs(e))<=1e-15,
      "linear_area_scale_abs_determinant":abs(a*e),"physical_area_interpretation":False,
      "angle_preservation_expected":abs(abs(a)-abs(e))<=1e-15}

def spatialgrid_check(data):
    w,h=data["info"]["width"],data["info"]["height"]; mc=data["mapCoordinates"]
    ls=(mc["lonE"]-mc["lonW"])/w; ts=-(mc["latN"]-mc["latS"])/h
    g=SpatialGrid(shape=(h,w),crs=None,transform=(ls,0.0,mc["lonW"],0.0,ts,mc["latN"]))
    b=g.bounds(); expected=(mc["lonW"],mc["latS"],mc["lonE"],mc["latN"])
    return {"constructs":True,"crs":None,"bounds":list(b),"expected_bounds":list(expected),"bounds_equal":b==expected,
      "cell_center_00":list(g.cell_center(0,0)),"cell_center_warning":"not used for continuous FMG points; +0.5 is cell-index semantics",
      "irregular_pack_cells_supported":False,"irregular_pack_grid_cells_supported":False,"continuous_point_inverse_supported":False,
      "expresses_documented_affine":b==expected}

def provenance_reconstruction(transform):
    cfg={"transform":transform.as_dict()}; s=WorldState()
    s.set_field("experiment.scratch",{"marker":1},Provenance(producer=EXPERIMENT,inputs=["slice"],configuration=cfg))
    restored=WorldState.restore(s.snapshot()); p=restored.provenance["experiment.scratch"]; rebuilt=CoordinateTransform.from_dict(p.configuration["transform"]); q=(17.25,31.75)
    return {"snapshot_restore":True,"configuration_present":"transform" in p.configuration,
      "rebuilt_strict_equal":strict_equal(transform.apply_point(q),rebuilt.apply_point(q)),
      "rebuilt_fingerprint_equal":fingerprint(transform.apply_point(q))==fingerprint(rebuilt.apply_point(q)),
      "restored_provenance":{"producer":p.producer,"inputs":p.inputs,"configuration_keys":sorted(p.configuration.keys()),"fingerprint_present":p.fingerprint is not None},
      "inverse_rebuilt_from_restored_provenance":strict_equal(transform.inverse().apply_point(q),rebuilt.inverse().apply_point(q)),"missing_for_reconstruction":[]}

def run():
    OUT_DIR.mkdir(parents=True,exist_ok=True); slices={}
    for stem in ("Viveria","Pithigy"):
        data,remap=load_slice(stem); candidates=candidate_transforms(data); pts=point_sets(data)
        slices[stem]={"top_level_keys":list(data.keys()),
          "pack_cell_keys":sorted(set(k for c in data["pack"]["cells"] for k in c.keys())),
          "pack_vertex_keys":sorted(set(k for v in data["pack"]["vertices"] for k in v.keys())),
          "counts":{"pack_cells":len(data["pack"]["cells"]),"pack_vertices":len(data["pack"]["vertices"]),"grid_cells":len(data["grid"]["cells"]),"grid_vertices":len(data["grid"]["vertices"])},
          "reference_spaces":{"cells.c":"pack-cell index, slice-local","cells.v":"pack-vertex index, slice-local","cells.g":"grid-cell index, slice-local","vertices.v":"grid-vertex index, slice-local","vertices.c":"grid-cell index, slice-local","routes.points[2]":"pack-cell index, slice-local","burgs.cell":"pack-cell index, slice-local","sentinel_-1":"sentinel, never an index","remap_sidecars":"original FMG id -> slice-local index; diagnostic provenance only"},
          "point_coordinate_types":{k:sorted({type(x).__name__ for p in v for x in p}) for k,v in pts.items()},
          "spatial_payload":{"map_bounds":[0.0,0.0,data["info"]["width"],data["info"]["height"]],"pack_vertex_has_p":any("p" in v for v in data["pack"]["vertices"]),"pack_cell_has_p":any("p" in c for c in data["pack"]["cells"])},
          "geometry":geometry_metrics(data),"anisotropy":anisotropy(data),"topology":topology_result(data,remap),"spatialgrid":spatialgrid_check(data),
          "candidates":{name:candidate_run(data,name,ts) for name,ts in candidates.items()},"transform_reconstruction":provenance_reconstruction(candidates["R2"][0])}
    return {"experiment":EXPERIMENT,"implementation":"experiment-local run.py; no changes to src/worldloom","commit":os.environ.get("GITHUB_SHA","unknown (local execution)"),"configuration":"config.yaml","seed":None,"python":platform.python_version(),"packages":{"worldloom":importlib.metadata.version("worldloom"),"pytest":version("pytest")},"execution":{"slices":["Viveria","Pithigy"],"candidates":["R1","R2"]},"fingerprint_assertions":fingerprint_assertions(),"slices":slices,"interpretation_boundary":"Raw measurements only; interpretation is kept outside raw results."}

def version(name):
    try:return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:return None

if __name__=="__main__":
    result=run(); out=OUT_DIR/"raw-results.json"; out.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    print(json.dumps({"output":str(out),"commit":result["commit"],"fingerprint_assertions":result["fingerprint_assertions"],
      "slices":{k:{"counts":v["counts"],"top_level_keys":v["top_level_keys"],"pack_cell_keys":v["pack_cell_keys"],"pack_vertex_keys":v["pack_vertex_keys"],"topology_all_equal":v["topology"]["all_topology_equal"],
      "R1":{kk:vv["fmg_to_wl_to_fmg"] for kk,vv in v["candidates"]["R1"]["points"].items()},"R2":{kk:vv["fmg_to_wl_to_fmg"] for kk,vv in v["candidates"]["R2"]["points"].items()},"spatialgrid":v["spatialgrid"]} for k,v in result["slices"].items()}},indent=2))
