import hashlib, json, subprocess, sys, xml.etree.ElementTree as ET, pathlib
W = pathlib.Path(r"C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w17-admin-users-react\src\web\frontend")
P = W / "src" / "Admin.tsx"
OUT = pathlib.Path(sys.argv[1])
MUT = {
 "mui-gio": ("new Date(value+'+07:00')", "new Date(value+'Z')"),
 "patch-403-giu-du-lieu": ("cause.code==='forbidden'){setDenied(true)", "cause.code==='__tat__'){setDenied(true)"),
 "hien-lai-gio-lech": ("new Date(time+7*3600000)", "new Date(time+0*3600000)"),
}
goc = P.read_bytes(); sha0 = hashlib.sha256(goc).hexdigest()
res = {"sha_goc": sha0, "phep": {}}
for name, (a, b) in MUT.items():
    s = goc.decode("utf-8"); assert s.count(a) == 1, name
    try:
        P.write_bytes(s.replace(a, b).encode("utf-8"))
        xml = OUT / (name + ".xml")
        r = subprocess.run(["npx.cmd", "vitest", "run", "--pool=threads", "--maxWorkers=1", "src/Admin.test.tsx", "--reporter=junit", "--outputFile=" + str(xml)], cwd=W, capture_output=True, text=True, encoding="utf-8")
        t = ET.parse(xml).getroot(); fails = [c.get("name") for c in t.iter("testcase") if c.find("failure") is not None]
        res["phep"][name] = {"thay": [a, b], "exit": r.returncode, "tests_do": fails}
    finally:
        P.write_bytes(goc)
    res["phep"][name]["sha_khoi_phuc"] = hashlib.sha256(P.read_bytes()).hexdigest()
    (OUT / "summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print("done", sha0)
