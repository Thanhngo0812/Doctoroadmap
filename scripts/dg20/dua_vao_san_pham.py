"""Đưa ba mô hình đã chọn (DG-20) vào `vendor/` của worktree, theo duyệt của Claude (28/10): `vendor/a1-nhe` phiên bản `r2-full-v2-dg20`,
`vendor/a8-pass-phu-ml` phiên bản `e5-d01-a-v2-dg20`. Sau đó sửa tay `MODEL_HASHES` và phiên bản trong `nhe_parser.py` theo giá trị in ra.
  tmp/venv-ml/Scripts/python.exe scripts/dg20/dua_vao_san_pham.py
"""
import hashlib
import json
import shutil
import statistics

import chung

PHIEN_BAN_A1 = "r2-full-v2-dg20"
PHIEN_BAN_A8 = "e5-d01-a-v2-dg20"


def sha(duong):
    return hashlib.sha256(duong.read_bytes()).hexdigest()


def main():
    moi = chung.ra() / "mo-hinh-moi"
    vendor = chung.WORKTREE / "vendor"
    a1 = vendor / "a1-nhe"
    cu = json.loads((a1 / "manifest.json").read_text(encoding="utf-8"))
    shutil.copyfile(moi / "m1-chon/heading.joblib", a1 / "heading.joblib")
    shutil.copyfile(moi / "m2-chon/join.joblib", a1 / "join.joblib")
    ban_chon = {m: json.loads((moi / f"{m}-chon/manifest.json").read_text(encoding="utf-8")) for m in ("m1", "m2", "m3")}
    manifest = {"version": PHIEN_BAN_A1, "research_fingerprint": cu["research_fingerprint"],
                "models": {"heading.joblib": sha(a1 / "heading.joblib"), "join.joblib": sha(a1 / "join.joblib")},
                "dg20": {"nguon": "báo cáo DG-20, chọn lại num_leaves bằng LOBO-16 và luật một sai số chuẩn; kiểm tái tạo r2-full-v1 trùng SHA-256 trước khi đổi",
                         "heading": {"num_leaves": ban_chon["m1"]["cau_hinh"]["num_leaves"], "n_estimators": ban_chon["m1"]["cau_hinh"]["n_estimators"]},
                         "join": {"num_leaves": ban_chon["m2"]["cau_hinh"]["num_leaves"], "n_estimators": ban_chon["m2"]["cau_hinh"]["n_estimators"]},
                         "ban_truoc": {"version": cu["version"], "models": cu["models"]}}}
    (a1 / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    a8 = vendor / "a8-pass-phu-ml"
    cu8 = json.loads((a8 / "manifest.json").read_text(encoding="utf-8"))
    m3 = ban_chon["m3"]
    shutil.copyfile(moi / "m3-chon/model.txt", a8 / "model.txt")
    ap_cuon = json.loads((chung.ra() / "chon-m3.json").read_text(encoding="utf-8"))["ap_theo_cuon"][str(m3["cau_hinh"]["num_leaves"])]
    cu8.update({
        "phien_ban": PHIEN_BAN_A8, "ngay_hoc": m3["ngay_hoc"],
        "mo_hinh": f"LightGBM {m3['thu_vien']['lightgbm']}, như thi_nghiem_e2b.make_model nhưng num_leaves={m3['cau_hinh']['num_leaves']}, n_estimators={m3['cau_hinh']['n_estimators']} (DG-20), seed 20261005",
        "ap_ngoai_mau_theo_sach_trung_vi": float(statistics.median(ap_cuon.values())),
        "hieu_chinh": m3["hieu_chinh"], "sha256_model": sha(a8 / "model.txt"),
        "dg20": {"nguon": "báo cáo DG-20, LOBO-16 và luật một sai số chuẩn; AP ngoài mẫu theo sách ở trường trên là trung vị 16 lần LOBO của cấu hình chọn",
                 "ban_truoc": {"phien_ban": "e5-d01-a-v1", "sha256_model": "6dbf87ef269c8f2f810bc5a5b6d6338e9a7075bc2978e7c6946ca6b59531d56a"}},
    })
    (a8 / "manifest.json").write_text(json.dumps(cu8, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"a1_models": manifest["models"], "a1_version": PHIEN_BAN_A1, "a8_sha256_model": cu8["sha256_model"], "a8_phien_ban": PHIEN_BAN_A8}, indent=1))


if __name__ == "__main__":
    main()
