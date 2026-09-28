"""So vector embedding qua Developer API (bộ gọi hiện tại) và qua Vertex AI — công cụ thử cho vé 19.

Câu hỏi: đổi nguồn embedding sang Vertex có giữ nguyên vector không? Nếu giữ nguyên (cosine ≈ 1), đường gọi có thể trung tính với
khoá cache như lời gọi sinh văn bản; nếu không, trộn vector hai nguồn trong cùng tài liệu sẽ làm sai phép so độ giống.
Văn bản thử là câu tự đặt, không có nội dung giáo trình. API key đọc qua Settings như luồng chính, không in ra.

Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/thu-vertex/so_embedding.py [--project ID] [--location global]
"""
import argparse
import math
import sys

sys.path.insert(0, "src")
from doc2roadmap.application.ports.embedding import EmbeddingRequest  # noqa: E402
from doc2roadmap.config import Settings  # noqa: E402
from doc2roadmap.infrastructure.embedding.gemini import GeminiEmbedding  # noqa: E402

TEXTS = ["Một không gian véc tơ là tập hợp có phép cộng và phép nhân với vô hướng.",
         "A retrieval system ranks documents by relevance to a query.",
         "矩阵乘法满足结合律。"]
TASKS = ["SEMANTIC_SIMILARITY", "RETRIEVAL_DOCUMENT"]


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", default="gen-lang-client-0947038321")
    parser.add_argument("--location", default="global")
    args = parser.parse_args()
    settings = Settings()
    if settings.gemini_api_key is None:
        raise SystemExit("Thiếu API key Developer API trong cấu hình; không so được.")
    dimensions = settings.embedding_dimensions
    developer = GeminiEmbedding(settings.gemini_api_key.get_secret_value(), model=settings.embedding_model_id,
                                output_dimensionality=dimensions)

    from google import genai
    from google.genai import types
    client = genai.Client(vertexai=True, project=args.project, location=args.location)

    worst = 1.0
    for task in TASKS:
        ours = developer.embed([EmbeddingRequest(text, task) for text in TEXTS])
        theirs = [client.models.embed_content(
            model=settings.embedding_model_id, contents=text,
            config=types.EmbedContentConfig(task_type=task, output_dimensionality=dimensions)).embeddings[0].values
            for text in TEXTS]
        for text, a, b in zip(TEXTS, ours, theirs):
            similarity = cosine(a, b)
            worst = min(worst, similarity)
            norm_a, norm_b = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
            diff = max(abs(x / norm_a - y / norm_b) for x, y in zip(a, b))
            print(f"{task:<20} {len(a)}/{len(b)} chiều  độ dài {norm_a:.4f}/{norm_b:.4f}  cosine {similarity:.8f}"
                  f"  lệch sau chuẩn hoá {diff:.1e}  | {text[:30]}")
    print(f"cosine thấp nhất: {worst:.8f} (Developer API/Vertex; Vertex chưa chuẩn hoá vector khi giảm số chiều)")


if __name__ == "__main__":
    main()
