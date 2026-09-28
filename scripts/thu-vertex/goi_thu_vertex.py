"""Gọi thử Gemini qua Vertex AI (google-genai, vertexai=True) — công cụ thử, không thuộc luồng chính.

Kiểm bốn việc trước khi tính chuyển luồng sang Vertex: có thông tin đăng nhập Google Cloud; gọi được đúng mô hình dev
(`gemini-3.1-flash-lite`, temperature 0); đầu ra JSON theo schema (luồng dựa vào điều này); số token thật để ước chi.
Dữ liệu gửi đi là vài tiêu đề tự đặt ở ba ngôn ngữ, không có nội dung giáo trình. Không đọc `.env`, không in bí mật.

Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/thu-vertex/goi_thu_vertex.py [--key-file KHOA.json] [--project ID] [--location global]
      [--model TEN] [--list-models]
Cần một trong ba: `--key-file` trỏ tới khoá service account (để ngoài repo); biến môi trường GOOGLE_APPLICATION_CREDENTIALS;
hoặc `gcloud auth application-default login`.
"""
import argparse
import json
import sys
import time

sys.path.insert(0, "src")
from doc2roadmap.application.prerequisite_prompt import PRICING_USD_PER_MILLION  # noqa: E402

DEFAULT_PROJECT = "gen-lang-client-0947038321"
SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
PROMPT = ("Classify each heading by its teaching function. Allowed labels: lesson, exercise, outline. "
          "Headings: ['Bài tập chương 2', 'Exercices du chapitre 3', '1.1 Tập hợp', 'Table des matières', '第2章 线性映射']. "
          "Return JSON matching the schema, one item per heading, same order.")
SCHEMA = {"type": "object", "properties": {"labels": {"type": "array", "items": {
    "type": "object", "properties": {"heading": {"type": "string"},
                                     "label": {"type": "string", "enum": ["lesson", "exercise", "outline"]}},
    "required": ["heading", "label"]}}}, "required": ["labels"]}
EXPECTED = ["exercise", "exercise", "lesson", "outline", "lesson"]


def credentials_or_exit(key_file=None):
    import google.auth
    from google.auth.exceptions import DefaultCredentialsError
    if key_file:
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_file(key_file, scopes=SCOPES)
        print(f"Thông tin đăng nhập: khoá service account {credentials.service_account_email}")
        return credentials
    try:
        credentials, adc_project = google.auth.default(scopes=SCOPES)
    except DefaultCredentialsError:
        print("Chưa có thông tin đăng nhập Google Cloud. Chọn một cách:\n"
              "  1) Khoá service account (vai trò 'Vertex AI User'), lưu NGOÀI repo, rồi đặt biến môi trường\n"
              "     GOOGLE_APPLICATION_CREDENTIALS=<đường dẫn tới tệp .json>\n"
              "  2) Cài Google Cloud CLI rồi chạy: gcloud auth application-default login")
        raise SystemExit(2)
    kind = type(credentials).__module__.rsplit(".", 1)[-1] + "." + type(credentials).__name__
    print(f"Thông tin đăng nhập: {kind}; project của ADC: {adc_project or '(không có)'}")
    return credentials


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument("--location", default="global")
    parser.add_argument("--model", default="gemini-3.1-flash-lite")
    parser.add_argument("--list-models", action="store_true", help="liệt kê mô hình có chữ 'flash' rồi dừng")
    parser.add_argument("--key-file", help="tệp khoá service account (.json, để ngoài repo); bỏ trống thì dùng ADC")
    args = parser.parse_args()

    from google import genai
    from google.genai import errors, types

    credentials = credentials_or_exit(args.key_file)
    client = genai.Client(vertexai=True, project=args.project, location=args.location, credentials=credentials)
    try:
        if args.list_models:
            names = sorted(m.name for m in client.models.list() if "flash" in (m.name or ""))
            print("\n".join(names) or "(không thấy mô hình nào có chữ 'flash')")
            return 0
        started = time.perf_counter()
        response = client.models.generate_content(
            model=args.model, contents=PROMPT,
            config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=512,
                                               response_mime_type="application/json", response_schema=SCHEMA))
        seconds = time.perf_counter() - started
    except errors.APIError as error:
        print(f"Lỗi API {error.code} {error.status}: {error.message}")
        if error.code == 403:
            print("Gợi ý: bật 'Vertex AI API' cho project và cấp vai trò 'Vertex AI User' cho tài khoản đang dùng.")
        elif error.code == 404:
            print("Gợi ý: tên mô hình hoặc vùng không có trên Vertex; chạy lại với --list-models.")
        return 1

    usage = response.usage_metadata
    tokens_in = usage.prompt_token_count or 0
    tokens_out = (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
    usd = (tokens_in * PRICING_USD_PER_MILLION["input"] + tokens_out * PRICING_USD_PER_MILLION["output"]) / 1e6
    print(f"Mô hình trả lời: {response.model_version}; {seconds:.2f} s")
    print(f"Token: vào {tokens_in}, ra {usage.candidates_token_count}, suy nghĩ {usage.thoughts_token_count}")
    print(f"Ước chi {usd:.8f} USD theo bảng giá Developer API trong repo — giá Vertex cần đối chiếu trang giá Vertex AI")
    data = json.loads(response.text)
    got = [row["label"] for row in data["labels"]]
    print(json.dumps(data, ensure_ascii=False, indent=1))
    print(f"JSON theo schema: đúng; nhãn khớp dự kiến {sum(a == b for a, b in zip(got, EXPECTED))}/{len(EXPECTED)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
