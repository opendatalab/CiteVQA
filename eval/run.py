#!/usr/bin/env python3
"""CiteVQA Evaluation: Recall / Rel / QA_ACC / Page_Recall / Precision / F1 / SAA

genai judge uses genai SDK (supports base_url proxy)
openai judge uses openai SDK
anthropic judge uses anthropic SDK
"""
import argparse, json, os, re, sys, time, base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"
OUTPUTS = ROOT / "outputs"


# ── bbox regex ──────────────────────────────────────────
BBOX_RE_SINGLE = re.compile(r'<bbox\s+page="(\d+)"\s+x1="([\d.]+)"\s+'
                            r'y1="([\d.]+)"\s+x2="([\d.]+)"\s+y2="([\d.]+)"\s*/?>')
BBOX_RE_MULTI = re.compile(r'<bbox\s+doc="(\d+)"\s+page="(\d+)"\s+x1="([\d.]+)"\s+'
                           r'y1="([\d.]+)"\s+x2="([\d.]+)"\s+y2="([\d.]+)"\s*/?>')


def remove_bbox(text):
    if not text or not isinstance(text, str):
        return ""
    text = BBOX_RE_MULTI.sub('[citation]', text)
    text = BBOX_RE_SINGLE.sub('[citation]', text)
    return text


def extract_bboxes(text, is_multi_doc=False):
    """Extract bboxes, returns [(doc_idx, page, x1, y1, x2, y2), ...]"""
    if not text or not isinstance(text, str):
        return []
    results = []
    for m in BBOX_RE_MULTI.findall(text):
        results.append((int(m[0]), int(m[1]), float(m[2]), float(m[3]), float(m[4]), float(m[5])))
    for m in BBOX_RE_SINGLE.findall(text):
        results.append((1, int(m[0]), float(m[1]), float(m[2]), float(m[3]), float(m[4])))
    return results


# ── PDF helpers ─────────────────────────────────────────
def pdf_to_images(pdf_path, dpi=150):
    from pdf2image import convert_from_path
    return convert_from_path(str(pdf_path), dpi=dpi)


def crop_bbox(img, x1, y1, x2, y2):
    """Convert 0-1000 relative coords to pixels and crop"""
    w, h = img.size
    return img.crop((int(x1 * w / 1000), int(y1 * h / 1000), int(x2 * w / 1000), int(y2 * h / 1000)))


def img_to_base64(img, fmt="PNG"):
    buf = __import__("io").BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


# ── genai client utils ──────────────────────────────────
def _normalize_genai_base_url(url):
    if not url:
        return url
    normalized = url.strip()
    if normalized.endswith("/v1"):
        normalized = normalized[:-3]
    elif normalized.endswith("/v1/"):
        normalized = normalized[:-4]
    if normalized and not normalized.endswith("/"):
        normalized += "/"
    return normalized


def _create_genai_client(api_key, base_url):
    from google import genai
    client = genai.Client(api_key=api_key)
    if base_url:
        normalized = _normalize_genai_base_url(base_url)
        client._api_client.base_url = normalized
    return client


def call_genai(model, question, images, api_key, system_instruction, timeout=120):
    import requests
    proxies = {
        "http": os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy"),
        "https": os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy"),
    }
    proxies = {k: v for k, v in proxies.items() if v}

    if base_url := os.environ.get("GENAI_BASE_URL"):
        normalized = _normalize_genai_base_url(base_url)
        url = f"{normalized}v1beta/models/{model}:generateContent"
        headers = {"Content-Type": "application/json"}
        parts = []
        for img_b64, fmt in images:
            parts.append({"inlineData": {"mimeType": f"image/{fmt}", "data": img_b64}})
        parts.append({"text": question})
        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "systemInstruction": {"parts": [{"text": system_instruction}]}
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout,
                             proxies=proxies if proxies else None)
        resp.raise_for_status()
        result = resp.json()
    else:
        client = _create_genai_client(api_key, None)
        from google.genai.types import Blob
        parts = [Blob(mime_type=f"image/{fmt}", data=base64.b64decode(img_b64)) for img_b64, fmt in images]
        parts.append(model=question)
        response = client.models.generate_content(
            model=model, contents=parts,
            system_instruction=system_instruction)
        return response.text

    candidates = result.get("candidates", [])
    if not candidates:
        return ""
    content = candidates[0].get("content", {})
    content_parts = content.get("parts", [])
    return "".join(p.get("text", "") for p in content_parts)


# ── openai client utils ─────────────────────────────────
def _make_openai_client(api_key, base_url):
    from openai import OpenAI
    return OpenAI(api_key=api_key, base_url=base_url)


def call_openai(model, question, images, api_key, base_url, system_instruction, timeout=120):
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)
    content = []
    for img_b64, fmt in images:
        content.append({"type": "image_url", "image_url": {"url": f"data:image/{fmt};base64,{img_b64}"}})
    content.append({"type": "text", "text": question})
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": content}
        ],
        timeout=timeout
    )
    return response.choices[0].message.content


# ── anthropic client utils ───────────────────────────────
def _make_anthropic_client(api_key, base_url):
    from anthropic import Anthropic
    if base_url:
        return Anthropic(api_key=api_key, base_url=base_url)
    return Anthropic(api_key=api_key)


def call_anthropic(model, question, images, api_key, base_url, system_instruction, timeout=120):
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key, base_url=base_url) if base_url else Anthropic(api_key=api_key)
    media = []
    for img_b64, fmt in images:
        media.append({"type": "image", "source": {"type": "base64", "media_type": f"image/{fmt}", "data": img_b64}})
    with client.messages.timeout(timeout) as t:
        response = client.messages.create(
            model=model,
            system=system_instruction,
            max_tokens=4096,
            messages=[{"role": "user", "content": [{"type": "text", "text": question}] + media}]
        )
    return response.content[0].text


# ── eval helpers ────────────────────────────────────────
def _img_or_pdf(item, api_type):
    if api_type == "openai":
        return item.get("openai_images", [])
    elif api_type == "genai" or api_type == "anthropic":
        return item.get("genai_images", [])
    return []


def eval_recall_single(item, api_type, model, api_key, base_url, timeout):
    gt_bboxes = extract_bboxes(item.get("answer_bboxes", ""), item.get("_is_multi_doc"))
    if not gt_bboxes:
        return None, "No GT bbox"

    pred_text = item.get("model_predict", "")
    pred_bboxes = extract_bboxes(pred_text, item.get("_is_multi_doc"))

    if not pred_bboxes:
        return 0.0, "No prediction bbox"

    hit = 0
    for gt in gt_bboxes:
        doc_idx, page, x1, y1, x2, y2 = gt
        iou_thresh = 0.5
        for pb in pred_bboxes:
            p_doc, p_page, p_x1, p_y1, p_x2, p_y2 = pb
            if doc_idx == p_doc and page == p_page:
                inter_x1 = max(x1, p_x1); inter_y1 = max(y1, p_y1)
                inter_x2 = min(x2, p_x2); inter_y2 = min(y2, p_y2)
                if inter_x2 > inter_x1 and inter_y2 > inter_y1:
                    inter = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
                    area_gt = (x2 - x1) * (y2 - y1)
                    area_pred = (p_x2 - p_x1) * (p_y2 - p_y1)
                    iou = inter / (area_gt + area_pred - inter + 1e-6)
                    if iou >= iou_thresh:
                        hit += 1
                        break
    recall = hit / len(gt_bboxes)
    return recall, f"{hit}/{len(gt_bboxes)} bboxes matched"


def eval_page_recall_single(item, api_type, model, api_key, base_url, timeout):
    gt_pages = set()
    for bbox_raw in item.get("answer_bboxes", "").split("<bbox"):
        ms = BBOX_RE_SINGLE.findall(bbox_raw)
        for m in ms:
            gt_pages.add(int(m[0]))
        ms = BBOX_RE_MULTI.findall(bbox_raw)
        for m in ms:
            gt_pages.add(int(m[1]))

    pred_pages = set()
    for bbox_raw in item.get("model_predict", "").split("<bbox"):
        ms = BBOX_RE_SINGLE.findall(bbox_raw)
        for m in ms:
            pred_pages.add(int(m[0]))
        ms = BBOX_RE_MULTI.findall(bbox_raw)
        for m in ms:
            pred_pages.add(int(m[1]))

    if not gt_pages:
        return None, "No GT page"
    return len(gt_pages & pred_pages) / len(gt_pages), f"{len(gt_pages & pred_pages)}/{len(gt_pages)} pages matched"


def eval_precision_single(item, api_type, model, api_key, base_url, timeout):
    gt_bboxes = extract_bboxes(item.get("answer_bboxes", ""), item.get("_is_multi_doc"))
    pred_text = item.get("model_predict", "")
    pred_bboxes = extract_bboxes(pred_text, item.get("_is_multi_doc"))
    if not pred_bboxes:
        return None, "No prediction bbox"
    hit = 0
    for gt in gt_bboxes:
        doc_idx, page, x1, y1, x2, y2 = gt
        iou_thresh = 0.5
        for pb in pred_bboxes:
            p_doc, p_page, p_x1, p_y1, p_x2, p_y2 = pb
            if doc_idx == p_doc and page == p_page:
                inter_x1 = max(x1, p_x1); inter_y1 = max(y1, p_y1)
                inter_x2 = min(x2, p_x2); inter_y2 = min(y2, p_y2)
                if inter_x2 > inter_x1 and inter_y2 > inter_y1:
                    inter = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
                    area_gt = (x2 - x1) * (y2 - y1)
                    area_pred = (p_x2 - p_x1) * (p_y2 - p_y1)
                    iou = inter / (area_gt + area_pred - inter + 1e-6)
                    if iou >= iou_thresh:
                        hit += 1
                        break
    precision = hit / len(pred_bboxes) if pred_bboxes else 0.0
    return precision, f"{hit}/{len(pred_bboxes)} pred bboxes matched"


def eval_f1_single(item, api_type, model, api_key, base_url, timeout):
    recall, _ = eval_recall_single(item, api_type, model, api_key, base_url, timeout)
    precision, _ = eval_precision_single(item, api_type, model, api_key, base_url, timeout)
    if recall is None or precision is None or (recall + precision) == 0:
        return None, "recall or precision is None"
    return 2 * recall * precision / (recall + precision), f"recall={recall:.3f}, precision={precision:.3f}"


def eval_rel_single(item, judge_api, judge_model, judge_api_key, base_url, timeout):
    rel_sys = (PROMPTS / "eval_rel_system.txt").read_text()
    rel_user_tmpl = (PROMPTS / "eval_rel_user.txt").read_text()

    images = _img_or_pdf(item, judge_api)
    images = [(img_to_base64(img), img.format.lower()) for img in images]

    question = item["Question"]
    standard_answer = remove_bbox(item.get("answer_bboxes", ""))
    pred = item["model_predict"]
    pred_text = remove_bbox(pred)

    user_prompt = rel_user_tmpl.format(
        question=question,
        standard_answer=standard_answer,
        answer_with_images=pred
    )

    if judge_api == "openai":
        raw = call_openai(judge_model, None, images, judge_api_key, base_url,
                           rel_sys + "\n" + user_prompt, timeout)
    elif judge_api == "genai":
        raw = call_genai(judge_model, rel_sys + "\n" + user_prompt, images,
                          judge_api_key, None, timeout)
    elif judge_api == "anthropic":
        raw = call_anthropic(judge_model, None, images, judge_api_key, base_url,
                             rel_sys + "\n" + user_prompt, timeout)
    else:
        raise ValueError(f"Unknown judge_api: {judge_api}")

    m = re.search(r'<relevance_score>(\d+)</relevance_score>', raw)
    score = int(m.group(1)) / 20 if m else None
    return score, raw


def eval_qa_acc_single(item, judge_api, judge_model, judge_api_key, base_url, timeout):
    qa_sys = (PROMPTS / "eval_qa_acc_system.txt").read_text()
    qa_user_tmpl = (PROMPTS / "eval_qa_acc_user.txt").read_text()

    images = _img_or_pdf(item, judge_api)
    images = [(img_to_base64(img), img.format.lower()) for img in images]

    question = item["Question"]
    standard_answer = remove_bbox(item.get("answer_bboxes", ""))
    model_answer_no_bbox = remove_bbox(item.get("model_predict", ""))

    user_prompt = qa_user_tmpl.format(
        question=question,
        standard_answer=standard_answer,
        model_answer_no_bbox=model_answer_no_bbox
    )

    if judge_api == "openai":
        raw = call_openai(judge_model, None, images, judge_api_key, base_url,
                           qa_sys + "\n" + user_prompt, timeout)
    elif judge_api == "genai":
        raw = call_genai(judge_model, qa_sys + "\n" + user_prompt, images,
                          judge_api_key, None, timeout)
    elif judge_api == "anthropic":
        raw = call_anthropic(judge_model, None, images, judge_api_key, base_url,
                             qa_sys + "\n" + user_prompt, timeout)
    else:
        raise ValueError(f"Unknown judge_api: {judge_api}")

    m = re.search(r'<qa_acc>(\d+)</qa_acc>', raw)
    score = int(m.group(1)) / 20 if m else None
    return score, raw


def compute_saa(item):
    rel = item.get("rel_score")
    recall = item.get("recall_score")
    qa_acc = item.get("qa_acc_score")
    if any(v is None for v in [rel, recall, qa_acc]):
        return None, "Missing component scores"
    score = 1.0 if (qa_acc >= 4 and (rel >= 4 or recall >= 0.6)) else 0.0
    return score, f"qa_acc={qa_acc}, rel={rel}, recall={recall}"


# ── main eval logic ─────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="CiteVQA Evaluation Pipeline")
    p.add_argument("--input", required=True, help="Infer output JSON file")
    p.add_argument("--out", default="", help="Output file path")
    p.add_argument("--metrics", default="recall,rel", help="Comma-separated metrics: recall,page_recall,precision,f1,rel,qa_acc,saa")
    p.add_argument("--judge_api", default="openai", help="openai / genai / anthropic")
    p.add_argument("--judge_model", default="gpt-4o", help="Judge model name")
    p.add_argument("--judge_api_key", required=True)
    p.add_argument("--base_url", default="", help="API base URL")
    p.add_argument("--timeout", type=int, default=300, help="API timeout (seconds)")
    p.add_argument("--workers", type=int, default=4, help="Number of concurrent workers")
    p.add_argument("--limit", type=int, default=0, help="Limit number of items to process (0 = all)")
    a = p.parse_args()

    with open(a.input) as f:
        data = json.load(f)
    if a.limit:
        data = data[:a.limit]
    print(f"Loaded {len(data)} items | api={a.judge_api} model={a.judge_model} workers={a.workers}")

    metrics = [m.strip() for m in a.metrics.split(",")]
    print(f"Metrics: {metrics}")

    OUTPUTS.mkdir(exist_ok=True)
    out_path = Path(a.out) if a.out else Path(a.input).with_suffix(".eval.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # ── checkpoint recovery ──────────────────────────────
    done_map = {}
    if out_path.exists():
        try:
            with open(out_path) as f:
                existing = json.load(f)
            for r in existing:
                if r and "index" in r:
                    done_map[r["index"]] = r
            print(f"Checkpoint: loaded {len(done_map)} existing results, will skip them")
        except Exception as e:
            print(f"Failed to load existing results, starting from scratch: {e}")

    pending = [it for it in data if it.get("index") not in done_map]
    print(f"Pending: {len(pending)} items (skipping {len(data) - len(pending)})")
    results = list(done_map.values())

    results_lock = __import__("threading").Lock()
    checkpoint_interval = 50
    processed_count = len(results)

    def save_checkpoint():
        with results_lock:
            snapshot = list(results)
        with open(out_path, "w") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)

    t0 = time.time()

    # ── bbox metrics (computed locally, no API) ──────────
    if any(m in metrics for m in ["recall", "page_recall", "precision", "f1"]):
        print(f"\n-- BBox Metrics (local computation) --")
        for item in tqdm(pending, desc="BBox metrics"):
            if "recall_score" not in item:
                score, reason = eval_recall_single(item, a.judge_api, a.judge_model,
                                                   a.judge_api_key, a.base_url, a.timeout)
                item["recall_score"] = score
                item["recall_reason"] = reason
            if "page_recall_score" not in item:
                score, reason = eval_page_recall_single(item, a.judge_api, a.judge_model,
                                                        a.judge_api_key, a.base_url, a.timeout)
                item["page_recall_score"] = score
                item["page_recall_reason"] = reason
            if "precision_score" not in item:
                score, reason = eval_precision_single(item, a.judge_api, a.judge_model,
                                                      a.judge_api_key, a.base_url, a.timeout)
                item["precision_score"] = score
                item["precision_reason"] = reason
            if "f1_score" not in item:
                score, reason = eval_f1_single(item, a.judge_api, a.judge_model,
                                                a.judge_api_key, a.base_url, a.timeout)
                item["f1_score"] = score
                item["f1_reason"] = reason
            processed_count += 1
            if processed_count % checkpoint_interval == 0:
                save_checkpoint()
                tqdm.write(f"    [checkpoint] saved {processed_count} items")
            results.append(item)
        save_checkpoint()

    # ── Rel ─────────────────────────────────────────────
    if "rel" in metrics:
        print("\n-- Rel (relevance) --")
        for item in tqdm(pending, desc="Rel"):
            if "rel_score" in item:
                continue
            score, raw = eval_rel_single(item, a.judge_api, a.judge_model,
                                         a.judge_api_key, a.base_url, a.timeout)
            item["rel_score"] = score
            item["rel_raw"] = raw
            processed_count += 1
            if processed_count % checkpoint_interval == 0:
                save_checkpoint()
                tqdm.write(f"    [checkpoint] processed {processed_count} items")
        valid = [r["rel_score"] for r in results if r["rel_score"] is not None]
        if valid:
            print(f"  Rel = {sum(valid) / len(valid):.4f}  ({len(valid)}/{len(results)})")
        save_checkpoint()

    # ── QA_ACC ──────────────────────────────────────────
    if "qa_acc" in metrics:
        print("\n-- QA_ACC (answer accuracy) --")
        for item in tqdm(pending, desc="QA_ACC"):
            if "qa_acc_score" in item:
                continue
            score, reason = eval_qa_acc_single(item, a.judge_api, a.judge_model,
                                                a.judge_api_key, a.base_url, a.timeout)
            item["qa_acc_score"] = score
            item["qa_acc_reason"] = reason
            processed_count += 1
            if processed_count % checkpoint_interval == 0:
                save_checkpoint()
                tqdm.write(f"    [checkpoint] processed {processed_count} items")
        valid = [r["qa_acc_score"] for r in results if r["qa_acc_score"] is not None]
        if valid:
            print(f"  QA_ACC = {sum(valid) / len(valid):.4f}  ({len(valid)}/{len(results)})")
        save_checkpoint()

    # ── SAA ─────────────────────────────────────────────
    if "saa" in metrics:
        print("\n-- SAA (QA_ACC>=4 AND (Rel>=4 OR Recall>=0.6)) --")
        for item in tqdm(pending, desc="SAA"):
            if "saa_score" in item:
                continue
            score, reason = compute_saa(item)
            item["saa_score"] = score
            item["saa_reason"] = reason
            processed_count += 1
            if processed_count % checkpoint_interval == 0:
                save_checkpoint()
                tqdm.write(f"    [checkpoint] processed {processed_count} items")
        valid = [r["saa_score"] for r in results if r["saa_score"] is not None]
        if valid:
            print(f"  SAA = {sum(valid) / len(valid):.4f}  ({len(valid)}/{len(results)})")
        save_checkpoint()

    # Re-build results from data + eval scores
    results = []
    idx_map = {r.get("index"): r for r in done_map.values()}
    for item in data:
        idx = item.get("index")
        if idx in idx_map:
            results.append(idx_map[idx])

    dt = time.time() - t0

    save_checkpoint()

    # Recompute final summary
    summary = {}
    for metric in ["recall", "page_recall", "precision", "f1", "rel", "qa_acc", "saa"]:
        key = f"{metric}_score"
        values = [r[key] for r in results if r.get(key) is not None]
        if values:
            summary[metric] = {"mean": sum(values) / len(values), "count": len(values), "total": len(results)}

    print(f"\n{'=' * 60}")
    print(f"Evaluation done  {len(results)} items  {dt:.1f}s")
    print(f"Output: {a.out}")
    print(f"\nOverall metrics:")
    for metric, stats in summary.items():
        print(f"  {metric}: {stats['mean']:.4f} ({stats['count']}/{stats['total']})")


if __name__ == "__main__":
    main()
