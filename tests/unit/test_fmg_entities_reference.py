"""Differential guard for the temporary frozen FMG entity builder reference."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import pytest
from worldloom.adapters.fmg import entities as current
from worldloom.adapters.fmg.entities import COLLECTION_SPECS, REFERENCE_SPECS

ROOT = Path(__file__).parents[2]
EXAMPLES = ROOT / "examples"
SLICES = ROOT / "experiments" / "fmg_scale" / "slices"
COLLECTIONS = tuple(COLLECTION_SPECS)
FIXTURES = (
 EXAMPLES / "Thimaland Full 2026-10-02-14-17.json",
 EXAMPLES / "Pithigy Full 2026-10-02-11-35.json",
 EXAMPLES / "Viveria Full 2026-10-02-11-31.json",
 SLICES / "Pithigy_burg1_hop3.json",
 SLICES / "Viveria_burg1_hop3.json",
)
_spec = importlib.util.spec_from_file_location("fmg_entities_ref", ROOT / "tests/reference/fmg_entities_ref.py")
reference = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(reference)

def outcome(module, data):
 try:
  entities, report = module.build_entities(deepcopy(data))
  return ("ok", list(entities.items()), report, json.dumps(report))
 except Exception as exc:
  return ("error", type(exc).__name__, str(exc))

def assert_same(data):
 assert outcome(reference, data) == outcome(current, data)

def thimaland():
 return json.loads(FIXTURES[0].read_text(encoding="utf-8"))

@pytest.mark.parametrize("path", FIXTURES)
def test_canonical_exports_and_hop_three_slices(path):
 assert_same(json.loads(path.read_text(encoding="utf-8")))

def test_existing_hand_built_reference_route_mesh_surrogate_and_lookup_cases():
 cases = [
  {"pack":{"cells":[{},{}],"states":[{"i":0,"neighbors":[1,-1,99,"x"],"provinces":[1,0,-1]},{"i":1,"neighbors":[0],"provinces":[]}],"provinces":[0,{"i":1,"state":0,"center":1},{"i":2,"state":99,"center":-1}],"burgs":[0,{"i":1,"cell":1,"state":-1}],"cultures":[{"i":0}],"religions":[{"i":0}]}},
  {"pack":{"cells":[{}],"states":[],"provinces":[],"burgs":[],"cultures":[],"religions":[],"rivers":[{"i":1,"cells":[0,-1,0]}],"routes":[{"i":0,"points":"not-a-list"},{"i":1,"points":[[1,2]]},{"i":2,"points":[[1,2,"x"]]}],"markers":[{"i":0,"cell":"x"}]}},
  {"pack":{"cells":[{}],"states":[],"provinces":[],"burgs":[],"cultures":[],"religions":[],"rivers":[],"markers":[],"routes":[{"i":0,"points":[[1,2,0]]}]}},
  {"pack":{"cells":[{}],"states":[],"provinces":[],"burgs":[],"cultures":[],"religions":[],"rivers":[],"routes":[],"markers":[{"i":0,"name":"bad"+chr(0xD802),"nested":["x"+chr(0xD803)],"meta":{chr(0xD804):"value"} }]}},
 ]
 for data in cases: assert_same(data)

@pytest.mark.parametrize("collection", COLLECTIONS)
def test_non_dict_record_each_collection(collection):
 data=thimaland(); records=data["pack"][collection]
 records[1 if collection in {"provinces","burgs"} else 0]="not-a-record"
 assert_same(data)

@pytest.mark.parametrize("bad_id", ["missing","string","bool","none"])
def test_missing_and_malformed_explicit_ids(bad_id):
 data=thimaland(); record=data["pack"]["states"][0]
 if bad_id=="missing": record.pop("i")
 else: record["i"]={"string":"bad","bool":True,"none":None}[bad_id]
 assert_same(data)

@pytest.mark.parametrize("collection", COLLECTIONS)
def test_duplicate_explicit_id_each_collection(collection):
 data=thimaland(); records=data["pack"][collection]
 valid=next(r for r in records if isinstance(r,dict) and isinstance(r.get("i"),int) and not isinstance(r.get("i"),bool))
 records.append(deepcopy(valid))
 expected=("error","ValueError",f"Duplicate explicit FMG i in pack.{collection}: {valid['i']}")
 assert outcome(reference,data)==expected
 assert outcome(current,data)==expected

@pytest.mark.parametrize("collection", COLLECTIONS)
@pytest.mark.parametrize("bad_value", ["not-list",None])
def test_non_list_collection_errors(collection,bad_value):
 data=thimaland(); data["pack"][collection]=bad_value; assert_same(data)

@pytest.mark.parametrize("collection", COLLECTIONS)
def test_absent_collection(collection):
 data=thimaland(); data["pack"].pop(collection); assert_same(data)

def reference_cases():
 base=thimaland()
 for collection, fields in REFERENCE_SPECS.items():
  for field, (_target,_mesh) in fields.items():
   for value in (-1,99,0,"x",True):
    for as_list in (False,True):
     data=deepcopy(base)
     record=next((r for r in data["pack"][collection] if isinstance(r,dict) and "i" in r),None)
     if record is None:
      record={"i": 987654}
      data["pack"][collection].append(record)
     record[field]=[value] if as_list else value
     yield collection,field,value,as_list,data

@pytest.mark.parametrize("collection,field,value,as_list,data",list(reference_cases()))
def test_reference_values_scalar_and_list(collection,field,value,as_list,data):
 assert_same(data)

@pytest.mark.parametrize("points",["not-list",[],[[1,2]],[[1,2,0,3]],[[1,2,"x"]],[[1,2,-1]],[[1,2,999]]])
def test_route_point_shapes_and_cell_values(points):
 data=thimaland(); data["pack"]["routes"][0]["points"]=points; assert_same(data)

@pytest.mark.parametrize("present",[True,False])
def test_excluded_keys_present_absent(present):
 data=thimaland(); record=data["pack"]["states"][0]
 if present: record.update({"coa":{"x":1},"military":[],"campaigns":[]})
 else:
  for key in ("coa","military","campaigns"): record.pop(key,None)
 assert_same(data)

def test_empty_pack():
 assert_same({"pack":{}})

def test_forced_derived_id_collision_raises_in_both(monkeypatch):
 data={"pack":{"cells":[{}],**{c:[] for c in COLLECTIONS}}}
 data["pack"]["states"]=[{"i":1},{"i":2}]
 monkeypatch.setattr(reference,"derive_entity_id",lambda *args:"state:constant")
 monkeypatch.setattr(current,"derive_entity_id",lambda *args:"state:constant")
 expected=("error","ValueError","Derived entity ID collision: state:constant")
 assert outcome(reference,data)==expected
 assert outcome(current,data)==expected
