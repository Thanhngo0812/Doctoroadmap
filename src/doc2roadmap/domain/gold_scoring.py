"""Luật chấm cho E1 và E2: thuần, không gọi mô hình, không đọc kho.

Cạnh luôn là cặp có hướng `(prerequisite, target)`: phải hiểu `prerequisite` trước mới hiểu được `target`.
Cặp của bộ sinh là vô hướng, nên so khớp bằng `frozenset`.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict, deque
from itertools import combinations

# Bootstrap cần một dòng số giả ngẫu nhiên **giống nhau trên mọi máy và mọi phiên bản Python**, nên dùng một LCG
# 64 bit viết thẳng ở đây thay vì `random` (tầng domain cũng không được phép nhập thư viện đó).
_MASK64 = (1 << 64) - 1
_MULTIPLIER = 6364136223846793005
_INCREMENT = 1442695040888963407


# Kênh "cứng" là kênh khớp đúng chữ hoặc gắn với provenance; kênh dense chỉ đề cử (spec D4).
HARD_CHANNELS = frozenset({"provenance", "extraction", "exact"})

# Sáu loại vị trí của D14; loại "bắc cầu" tách theo kênh bắt được lần nhắc.
POSITIONS = (
    "same_chunk",
    "same_section",
    "same_chapter",
    "same_cluster",
    "bridge_hard",
    "bridge_soft",
    "implicit",
)

POSITION_LABELS = {
    "same_chunk": "cùng chunk",
    "same_section": "cùng mục",
    "same_chapter": "cùng chương",
    "same_cluster": "cùng cụm chủ đề",
    "bridge_hard": "bắc cầu qua chunk nhắc cả hai (kênh cứng)",
    "bridge_soft": "bắc cầu qua chunk nhắc cả hai (chỉ dense)",
    "implicit": "ngầm",
}


def transitive_closure(edges):
    """Bao đóng bắc cầu, bỏ cạnh tự nối. Đồ thị có chu trình vẫn chạy được."""
    adjacency = defaultdict(set)
    for prerequisite, target in edges:
        adjacency[prerequisite].add(target)
    result = set()
    for start in sorted(adjacency):
        queue, seen = deque(sorted(adjacency[start])), set()
        while queue:
            node = queue.popleft()
            if node in seen:
                continue
            seen.add(node)
            if node != start:
                result.add((start, node))
            queue.extend(sorted(adjacency.get(node, ())))
    return result


def _ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def score_edges(predicted, gold, *, targets=None, closure=False):
    """P/R/F1 của tập cạnh dự đoán so với vàng.

    `targets` giới hạn phạm vi chấm về đúng những khái niệm đích mà người gán được yêu cầu xét: cạnh trỏ tới
    khái niệm ngoài phạm vi đó không tính là dự đoán sai, vì bộ vàng không nói gì về chúng.
    """
    predicted, gold = set(predicted), set(gold)
    if closure:
        predicted, gold = transitive_closure(predicted), transitive_closure(gold)
    if targets is not None:
        scope = set(targets)
        predicted = {edge for edge in predicted if edge[1] in scope}
        gold = {edge for edge in gold if edge[1] in scope}
    true_positive = predicted & gold
    precision = _ratio(len(true_positive), len(predicted))
    recall = _ratio(len(true_positive), len(gold))
    if precision is None or recall is None or precision + recall == 0:
        f1 = None
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "predicted": len(predicted),
        "gold": len(gold),
        "true_positive": len(true_positive),
        "false_positive": len(predicted - gold),
        "false_negative": len(gold - predicted),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _bridge_kind(mention_map, prerequisite, target):
    """Có chunk nào nhắc cả hai đầu không, và nhắc bằng kênh nào."""
    kind = None
    for rows in mention_map.values():
        left, right = rows.get(prerequisite), rows.get(target)
        if not left or not right:
            continue
        if set(left.get("channels", ())) & HARD_CHANNELS and set(right.get("channels", ())) & HARD_CHANNELS:
            return "bridge_hard"
        kind = "bridge_soft"
    return kind


def edge_position(prerequisite, target, *, provenance, section_of_chunk, chapter_of_chunk, cluster_of_node,
                  mention_map):
    """Một cạnh vàng nằm ở đâu trong tài liệu. Xét theo thứ tự hẹp trước, rộng sau; loại đầu tiên khớp thì lấy."""
    left, right = set(provenance.get(prerequisite, ())), set(provenance.get(target, ()))
    if left & right:
        return "same_chunk"
    if {section_of_chunk.get(c) for c in left if c in section_of_chunk} & {
        section_of_chunk.get(c) for c in right if c in section_of_chunk
    }:
        return "same_section"
    if {chapter_of_chunk.get(c) for c in left if c in chapter_of_chunk} & {
        chapter_of_chunk.get(c) for c in right if c in chapter_of_chunk
    }:
        return "same_chapter"
    if (
        prerequisite in cluster_of_node
        and cluster_of_node[prerequisite] == cluster_of_node.get(target)
    ):
        return "same_cluster"
    return _bridge_kind(mention_map, prerequisite, target) or "implicit"


def classify_positions(edges, **context):
    rows = []
    for prerequisite, target in sorted(edges):
        rows.append({
            "prerequisite": prerequisite,
            "target": target,
            "position": edge_position(prerequisite, target, **context),
        })
    return rows


def position_counts(rows):
    counter = Counter(row["position"] for row in rows)
    return {position: counter.get(position, 0) for position in POSITIONS}


def _entropy(labels):
    total = len(labels)
    counter = Counter(labels)
    return -sum((count / total) * math.log(count / total) for count in counter.values() if count) if total else 0.0


def normalized_mutual_information(left, right):
    """NMI chuẩn hoá bằng trung bình cộng hai entropy, tính trên các node có mặt ở cả hai cách chia."""
    keys = sorted(set(left) & set(right))
    if not keys:
        return None
    first = [left[key] for key in keys]
    second = [right[key] for key in keys]
    total = len(keys)
    joint = Counter(zip(first, second, strict=True))
    left_counts, right_counts = Counter(first), Counter(second)
    information = 0.0
    for (a, b), count in joint.items():
        joint_probability = count / total
        information += joint_probability * math.log(
            joint_probability / ((left_counts[a] / total) * (right_counts[b] / total))
        )
    denominator = (_entropy(first) + _entropy(second)) / 2
    if denominator == 0:
        return 1.0
    return information / denominator


def pairs_within(groups):
    """Mọi cặp vô hướng cùng nằm trong ít nhất một nhóm (một phiên, một cụm…)."""
    result = set()
    for members in groups:
        ordered = sorted(set(members))
        result.update(frozenset(pair) for pair in combinations(ordered, 2))
    return result


def undirected(edges):
    return {frozenset(edge) for edge in edges if edge[0] != edge[1]}


def generator_rows(gold_pairs, sources_by_pair, *, generators=None):
    """Mỗi bộ sinh: số cặp nó đề cử, recall cạnh vàng, và phần recall chỉ riêng nó có."""
    gold_pairs = set(gold_pairs)
    names = sorted(generators) if generators is not None else sorted(
        {name for names in sources_by_pair.values() for name in names}
    )
    proposed = {name: {pair for pair, values in sources_by_pair.items() if name in values} for name in names}
    covered = {name: proposed[name] & gold_pairs for name in names}
    rows = []
    for name in names:
        others = set().union(*(covered[other] for other in names if other != name)) if len(names) > 1 else set()
        rows.append({
            "generator": name,
            "pairs": len(proposed[name]),
            "gold_covered": len(covered[name]),
            "recall": _ratio(len(covered[name]), len(gold_pairs)),
            "unique_gold_covered": len(covered[name] - others),
            "unique_recall": _ratio(len(covered[name] - others), len(gold_pairs)),
        })
    return rows


def subset_rows(gold_pairs, sources_by_pair, *, generators=None):
    """Mọi tổ hợp bộ sinh: số cặp phải hỏi và recall đạt được."""
    gold_pairs = set(gold_pairs)
    names = sorted(generators) if generators is not None else sorted(
        {name for names in sources_by_pair.values() for name in names}
    )
    rows = []
    for size in range(1, len(names) + 1):
        for subset in combinations(names, size):
            chosen = {pair for pair, values in sources_by_pair.items() if values & set(subset)}
            rows.append({
                "generators": list(subset),
                "pairs": len(chosen),
                "gold_covered": len(chosen & gold_pairs),
                "recall": _ratio(len(chosen & gold_pairs), len(gold_pairs)),
            })
    rows.sort(key=lambda row: (len(row["generators"]), row["generators"]))
    return rows


def coverage_rows(gold_pairs, coverage_by_name):
    """Recall của từng cấu hình định tuyến: cặp mà cấu hình đó cho pipeline nhìn thấy."""
    gold_pairs = set(gold_pairs)
    return [
        {
            "configuration": name,
            "pairs": len(pairs),
            "gold_covered": len(set(pairs) & gold_pairs),
            "recall": _ratio(len(set(pairs) & gold_pairs), len(gold_pairs)),
        }
        for name, pairs in sorted(coverage_by_name.items())
    ]


def agreement(first, second, *, targets, concepts, transitive=False):
    """Cohen's κ trên toàn bộ không gian cặp ứng viên (đích × mọi khái niệm).

    `transitive=True` tính thêm đồng thuận ngầm: một người ghi cạnh trực tiếp còn người kia ghi đường vòng thì
    coi là cùng khẳng định, đúng cách PREAP xử lý.
    """
    targets, concepts = sorted(set(targets)), sorted(set(concepts))
    space = {(prerequisite, target) for target in targets for prerequisite in concepts if prerequisite != target}
    left, right = set(first), set(second)
    if transitive:
        left, right = transitive_closure(left), transitive_closure(right)
    left, right = left & space, right & space
    both = len(left & right)
    only_first, only_second = len(left - right), len(right - left)
    neither = len(space) - both - only_first - only_second
    total = len(space)
    if not total:
        return None
    observed = (both + neither) / total
    first_yes, second_yes = (both + only_first) / total, (both + only_second) / total
    expected = first_yes * second_yes + (1 - first_yes) * (1 - second_yes)
    kappa = (observed - expected) / (1 - expected) if expected != 1 else None
    return {
        "candidate_pairs": total,
        "both": both,
        "only_first": only_first,
        "only_second": only_second,
        "neither": neither,
        "observed": observed,
        "expected": expected,
        "kappa": kappa,
        "union": len(left | right),
        "intersection": both,
        "transitive": transitive,
    }


def index_stream(seed, count, bound):
    """Dòng chỉ số lấy mẫu, tất định theo seed. Lấy bit cao của LCG vì bit thấp của LCG có chu kỳ ngắn."""
    if bound < 1:
        raise ValueError("bound phải dương")
    state = (int(seed) ^ 0x9E3779B97F4A7C15) & _MASK64
    values = []
    for _ in range(count):
        state = (state * _MULTIPLIER + _INCREMENT) & _MASK64
        values.append((state >> 33) % bound)
    return values


def bootstrap_interval(units, statistic, *, samples=2000, seed=20260918, level=0.95):
    """Khoảng tin cậy bootstrap, **lấy mẫu lại theo đơn vị được truyền vào** (D14: theo khái niệm đích).

    `statistic` nhận một tuple đơn vị (có lặp) và trả về số, hoặc None khi không tính được trên mẫu đó.
    """
    units = list(units)
    point = statistic(tuple(units))
    if not units or samples < 1:
        return {"point": point, "low": None, "high": None, "samples": 0, "unit_count": len(units)}
    draw = index_stream(seed, samples * len(units), len(units))
    values = []
    for start in range(0, samples * len(units), len(units)):
        sample = tuple(units[index] for index in draw[start : start + len(units)])
        value = statistic(sample)
        if value is not None:
            values.append(value)
    if not values:
        return {"point": point, "low": None, "high": None, "samples": 0, "unit_count": len(units)}
    values.sort()
    margin = (1 - level) / 2
    low = values[max(0, math.floor(margin * (len(values) - 1)))]
    high = values[min(len(values) - 1, math.ceil((1 - margin) * (len(values) - 1)))]
    return {"point": point, "low": low, "high": high, "samples": len(values), "unit_count": len(units)}


def share_by_target(rows, position, targets):
    """Tỉ lệ cạnh vàng thuộc một loại vị trí, tính theo mẫu khái niệm đích (dùng cho bootstrap)."""
    by_target = defaultdict(list)
    for row in rows:
        by_target[row["target"]].append(row["position"])
    def statistic(sample):
        chosen = [value for target in sample for value in by_target.get(target, ())]
        return _ratio(sum(value == position for value in chosen), len(chosen))
    return statistic


def recall_by_target(gold_edges, covered_pairs):
    """Recall của một tập cặp, tính theo mẫu khái niệm đích."""
    by_target = defaultdict(list)
    for prerequisite, target in gold_edges:
        by_target[target].append(frozenset((prerequisite, target)))
    covered = set(covered_pairs)
    def statistic(sample):
        chosen = [pair for target in sample for pair in by_target.get(target, ())]
        return _ratio(sum(pair in covered for pair in chosen), len(chosen))
    return statistic


def metric_by_target(predicted, gold, *, metric, closure=False):
    """P/R/F1 tính theo mẫu khái niệm đích, để bootstrap.

    Một khái niệm đích bị lấy trùng trong mẫu thì mọi cạnh của nó được đếm đúng bấy nhiêu lần.
    """
    predicted, gold = set(predicted), set(gold)
    if closure:
        predicted, gold = transitive_closure(predicted), transitive_closure(gold)
    predicted_by_target, gold_by_target = defaultdict(set), defaultdict(set)
    for edge in predicted:
        predicted_by_target[edge[1]].add(edge)
    for edge in gold:
        gold_by_target[edge[1]].add(edge)

    def statistic(sample):
        true_positive = predicted_total = gold_total = 0
        for target, multiplier in Counter(sample).items():
            left, right = predicted_by_target.get(target, set()), gold_by_target.get(target, set())
            true_positive += multiplier * len(left & right)
            predicted_total += multiplier * len(left)
            gold_total += multiplier * len(right)
        precision, recall = _ratio(true_positive, predicted_total), _ratio(true_positive, gold_total)
        if metric == "precision":
            return precision
        if metric == "recall":
            return recall
        if precision is None or recall is None or precision + recall == 0:
            return None
        return 2 * precision * recall / (precision + recall)
    return statistic


def presentation_agreement(stages, presentation_index):
    """τ Kendall giữa thứ tự lộ trình và thứ tự trình bày của giáo trình.

    Hai loại cặp ra khỏi mẫu số vì không bên nào xếp thứ tự cho chúng: cặp nằm cùng một stage (lộ trình không
    xếp) và cặp có cùng vị trí trình bày (sách không xếp). Hai con số ấy **đếm độc lập** và được trả về, vì một
    cặp có thể thuộc cả hai.

    Cảnh báo phải mang theo mỗi khi trích τ: phép đo dùng **một** văn bản tham chiếu duy nhất, trong khi có thể
    có nhiều thứ tự chấp nhận được (Lapata 2006, §5).
    """
    rank = {node_id: index for index, members in enumerate(stages) for node_id in members}
    rows = sorted((rank[node_id], presentation_index[node_id], node_id)
                  for node_id in rank if node_id in presentation_index)
    concordant = discordant = same_stage = same_position = 0
    for (left_stage, left_book, _), (right_stage, right_book, _) in combinations(rows, 2):
        tied_stage, tied_book = left_stage == right_stage, left_book == right_book
        same_stage += tied_stage
        same_position += tied_book
        if tied_stage or tied_book:
            continue
        if (left_stage < right_stage) == (left_book < right_book):
            concordant += 1
        else:
            discordant += 1
    comparable = concordant + discordant
    return {
        "tau": (concordant - discordant) / comparable if comparable else None,
        "concordant": concordant,
        "discordant": discordant,
        "comparable_pairs": comparable,
        "same_stage_pairs": same_stage,
        "same_position_pairs": same_position,
        "concepts": len(rows),
    }


def gold_order_violations(stages, gold_edges, *, names=None):
    """Cạnh vàng nào lộ trình **chưa bảo đảm** học tiên quyết trước khái niệm cần nó.

    Bốn rổ, không chồng nhau: `respected`, `violated` (tiên quyết bị đặt sau), `same_stage` và `out_of_scope`
    (một đầu không nằm trong lộ trình). Stage là tập học **song song**, nên cùng stage cũng chưa bảo đảm học trước.

    `learning_order_error` là chỉ số nghiệm thu: ba rổ lỗi chia cho **toàn bộ** bộ vàng, để việc bỏ node khỏi lộ
    trình không làm mẫu số nhỏ đi. Bộ vàng rỗng cho `None` — chưa đánh giá, không phải đạt. `rate` chỉ tính trên
    cặp đã xếp được thứ tự; giữ lại để so với các số đã báo trước đây, không dùng làm cổng.
    """
    rank = {node_id: index for index, members in enumerate(stages) for node_id in members}
    names = names or {}
    counts = {"respected": 0, "violated": 0, "same_stage": 0, "out_of_scope": 0}
    rows = []
    for prerequisite, target in sorted(gold_edges):
        if prerequisite not in rank or target not in rank:
            bucket = "out_of_scope"
        elif rank[prerequisite] == rank[target]:
            bucket = "same_stage"
        elif rank[prerequisite] < rank[target]:
            bucket = "respected"
        else:
            bucket = "violated"
        counts[bucket] += 1
        if bucket != "respected":
            rows.append({
                "prerequisite": prerequisite,
                "target": target,
                "prerequisite_name": names.get(prerequisite),
                "target_name": names.get(target),
                "prerequisite_stage": rank.get(prerequisite),
                "target_stage": rank.get(target),
                "bucket": bucket,
            })
    ordered = counts["respected"] + counts["violated"]
    total = sum(counts.values())
    errors = counts["violated"] + counts["same_stage"] + counts["out_of_scope"]
    return {
        "rate": counts["violated"] / ordered if ordered else None,
        "learning_order_error": errors / total if total else None,
        **counts,
        "rows": rows,
    }
