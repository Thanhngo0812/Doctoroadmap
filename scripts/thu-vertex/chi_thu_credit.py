"""Chi thử khoảng 0,5 USD qua Vertex AI để kiểm tiền có trừ vào credit Google Cloud không (chủ dự án yêu cầu 2026-09-28).

Để khoản chi không phí, mô hình viết các chương giáo trình tổng hợp bằng tiếng Pháp, Trung, Nga, Đức — dùng làm tài liệu chạy thử cho
các vé đa ngôn ngữ (không thay tài liệu thật T19). Không gửi nội dung giáo trình nào. Mỗi lời gọi gắn nhãn billing
`doc2roadmap=kiem-tra-credit` để lọc trong báo cáo Billing. Trần cứng tính theo bảng giá Developer API trong repo, có giữ chỗ cho lời
gọi đang chạy; giá Vertex thật có thể khác một chút.

Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/thu-vertex/chi_thu_credit.py [--target 0.5] [--cap 0.55]
Kết quả: tmp/vertex-credit-check/ (chương sinh ra và sổ chi).
"""
import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.application.prerequisite_prompt import PRICING_USD_PER_MILLION as PRICE  # noqa: E402

LANGUAGES = ["French", "Simplified Chinese", "Russian", "German"]
TOPICS = ["vector spaces and subspaces", "linear maps and matrices", "eigenvalues and eigenvectors", "inner product spaces",
          "probability spaces and random variables", "decision trees", "gradient descent", "graph traversal algorithms",
          "relational databases and normal forms", "finite automata", "numerical integration", "determinants",
          "systems of linear equations", "bases and dimension", "orthogonal projections", "singular value decomposition",
          "quadratic forms", "limits and continuity", "derivatives and their applications", "Riemann integration",
          "sequences and series", "ordinary differential equations", "combinatorics and counting", "discrete random variables",
          "continuous distributions", "the central limit theorem", "point estimation", "confidence intervals",
          "hypothesis testing", "linear regression", "logistic regression", "naive Bayes classifiers", "k-means clustering",
          "support vector machines", "neural networks and backpropagation", "convolutional networks", "overfitting and "
          "regularization", "cross-validation", "sorting algorithms", "hash tables", "binary search trees",
          "dynamic programming", "shortest paths", "minimum spanning trees", "computational complexity", "regular expressions",
          "context-free grammars", "SQL queries", "transactions and concurrency control", "indexing in databases",
          "the TCP/IP model", "routing algorithms", "operating system processes", "memory management",
          "public-key cryptography", "information entropy"]
PROMPT = ("Write, in {language}, one chapter of about 5000 words of a university textbook on '{topic}'. Structure: chapter title "
          "with its number; a short table of contents; a preface paragraph; numbered sections (1.1, 1.2, ...) and subsections; "
          "numbered definitions, theorems and examples written in the conventions of that language; worked examples; and an "
          "exercises section at the end. Plain text, headings on their own lines.")
MAX_OUTPUT = 8192
OUTPUT = Path("tmp/vertex-credit-check")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target", type=float, default=0.5)
    parser.add_argument("--cap", type=float, default=0.55)
    parser.add_argument("--project", default="gen-lang-client-0947038321")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    from google import genai
    from google.genai import types

    client = genai.Client(vertexai=True, project=args.project, location="global")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    lock, ledger = threading.Lock(), []
    state = {"spent": 0.0, "reserved": 0.0, "index": 0}
    reserve = (4000 * PRICE["input"] + MAX_OUTPUT * PRICE["output"]) / 1e6
    started = datetime.now(timezone.utc)

    def next_job():
        with lock:
            if state["spent"] >= args.target or state["spent"] + state["reserved"] + reserve > args.cap:
                return None
            state["reserved"] += reserve
            i = state["index"]
            state["index"] += 1
        return i, LANGUAGES[i % len(LANGUAGES)], TOPICS[(i // len(LANGUAGES)) % len(TOPICS)]

    def worker():
        while (job := next_job()) is not None:
            i, language, topic = job
            t0 = time.perf_counter()
            try:
                response = client.models.generate_content(
                    model="gemini-3.1-flash-lite", contents=PROMPT.format(language=language, topic=topic),
                    config=types.GenerateContentConfig(
                        temperature=0.0, max_output_tokens=MAX_OUTPUT, labels={"doc2roadmap": "kiem-tra-credit"},
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)))
                usage = response.usage_metadata
                tokens_in = usage.prompt_token_count or 0
                tokens_out = (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
                usd = (tokens_in * PRICE["input"] + tokens_out * PRICE["output"]) / 1e6
                name = f"{i:03d}-{language.split()[-1].lower()}-{topic.split()[0]}.txt"
                (OUTPUT / name).write_text(response.text or "", encoding="utf-8")
                row = {"i": i, "language": language, "topic": topic, "input": tokens_in, "output": tokens_out,
                       "usd": usd, "seconds": round(time.perf_counter() - t0, 2), "file": name}
            except Exception as error:  # ghi lỗi, vẫn giữ trần; không thử lại để khỏi chi ngoài dự kiến
                usd, row = 0.0, {"i": i, "language": language, "topic": topic, "error": str(error)[:300]}
            with lock:
                state["reserved"] -= reserve
                state["spent"] += usd
                ledger.append(row)
                print(f"#{i:03d} {language:<19} {row.get('output', '-'):>5} token ra  {usd:.5f} USD  tổng {state['spent']:.4f}",
                      flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for _ in range(args.workers):
            pool.submit(worker)
    finished = datetime.now(timezone.utc)
    summary = {"project": args.project, "model": "gemini-3.1-flash-lite", "label": "doc2roadmap=kiem-tra-credit",
               "started_utc": started.isoformat(), "finished_utc": finished.isoformat(), "calls": len(ledger),
               "errors": sum("error" in row for row in ledger),
               "input_tokens": sum(row.get("input", 0) for row in ledger),
               "output_tokens": sum(row.get("output", 0) for row in ledger),
               "usd_estimate_developer_api_price": round(state["spent"], 6), "price_per_million": PRICE, "rows": ledger}
    (OUTPUT / "so-chi.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
