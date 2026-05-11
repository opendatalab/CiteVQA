#!/usr/bin/env python3
"""CiteVQA Inference: supports openai / genai / anthropic APIs

genai uses genai SDK (supports base_url proxy)
openai uses openai SDK
anthropic uses anthropic SDK
"""
import argparse, json, os, re, sys, tempfile, time, base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"
BENCHMARK = ROOT / "data" / "data_items.json"
OUTPUTS = ROOT / "outputs"

# ── bbox regex ──────────────────────────────────────────
BBOX_RE_SINGLE = re.compile(r'<bbox\s+page="(\d+)"\s+x1="([\d.]+)"\s+'
                            r'y1="([\d.]+)"\s+x2="([\d.]+)"\s+y2="([\d.]+)"\s*/?>')
BBOX_RE_MULTI = re.compile(r'<bbox\s+doc="(\d+)"\s+page="(\d+)"\s+x1="([\d.]+)"\s+'
                           r'y1="([\d.]+)"\s+x2="([\d.]+)"\s+y2="([\d.]+)"\s*/?>')


def remove_bbox(text):
    text = BBOX_RE_MULTI.sub('[citation]', text)
    text = BBOX_RE_SINGLE.sub('[citation]', text)
    return text


# ── PDF helpers ─────────────────────────────────────────
def compress_pdf_bytes(pdf_bytes, max_mb=10):
    """Compress PDF bytes using ghostscript, returns bytes"""
    size = len(pdf_bytes) / 1024 / 1024
    if size <= max_mb:
        return pdf_bytes
    try:
        import subprocess
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_in:
            tmp_in.write(pdf_bytes)
            tmp_in_path = tmp_in.name
        tmp_out_path = tmp_in_path + ".compressed.pdf"
        subprocess.run(
            ["gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
             "-dPDFSETTINGS=/ebook", "-dNOPAUSE", "-dQUIET", "-dBATCH",
             "-sOutputFile=" + tmp_out_path, tmp_in_path],
            check=True, capture_output=True)
        with open(tmp_out_path, "rb") as f:
            result = f.read()
        os.unlink(tmp_in_path)
        os.unlink(tmp_out_path)
        return result
    except Exception as e:
        return pdf_bytes


def pdf_to_images(pdf_path, dpi=150):
    from pdf2image import convert_from_path
    return convert_from_path(str(pdf_path), dpi=dpi)


# ── genai client utils ──────────────────────────────────
def _normalize_genai_base_url(url):
    """genai SDK needs gateway base URL (http://host:port/), strip /v1"""
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
    from google.genai import types
    return genai.Client(
        http_options=types.HttpOptions(
            base_url=_normalize_genai_base_url(base_url),
            timeout=240000,
        ),
        api_key=api_key,
    )


# ── genai file API (multi-doc) ─────────────────────────
def call_genai_file(model, question, pdf_paths, api_key, base_url, system_prompt, user_tmpl, is_multi_doc=False):
    """Upload PDF via genai File API and call"""
    from google import genai
    from google.genai import types

    client = _create_genai_client(api_key, base_url)

    parts = []
    for i, pdf_path in enumerate(pdf_paths, 1):
        if is_multi_doc:
            parts.append(f'doc="{i}"')

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        pdf_bytes = compress_pdf_bytes(pdf_bytes)

        parts.append(types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"))

    parts.append(user_tmpl.format(question=question))

    r = client.models.generate_content(
        model=model,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
        contents=parts
    )

    return r.text


# ── genai PDF direct (single-doc) ─────────────────────
def call_genai_pdf_direct(model, question, pdf_path, api_key, base_url, system_prompt, user_tmpl):
    """Direct PDF bytes call (single-doc, no File API)"""
    from google import genai
    from google.genai import types

    client = _create_genai_client(api_key, base_url)

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    pdf_bytes = compress_pdf_bytes(pdf_bytes)

    parts = [
        types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
        user_tmpl.format(question=question)
    ]

    r = client.models.generate_content(
        model=model,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
        contents=parts
    )
    return r.text


# ── openai call ────────────────────────────────────────
def compress_image_to_target(img, target_mb=45, current_total_mb=0):
    """Compress image to target size, return base64 encoded string"""
    import io

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    original_size_mb = len(buf.getvalue()) / 1024 / 1024

    target_single_mb = target_mb - current_total_mb
    if target_single_mb <= 0:
        target_single_mb = 1

    if original_size_mb <= target_single_mb:
        return base64.b64encode(buf.getvalue()).decode()

    buf_jpeg = io.BytesIO()

    if img.mode == 'RGBA':
        img_rgb = img.convert('RGB')
    else:
        img_rgb = img

    for quality in [85, 70, 50, 30, 20, 10]:
        buf_jpeg.seek(0)
        buf_jpeg.truncate(0)
        img_rgb.save(buf_jpeg, format="JPEG", quality=quality)
        size_mb = len(buf_jpeg.getvalue()) / 1024 / 1024
        if size_mb <= target_single_mb:
            return base64.b64encode(buf_jpeg.getvalue()).decode()

    w, h = img.size
    for scale in [0.8, 0.6, 0.5, 0.4, 0.3]:
        new_size = (int(w * scale), int(h * scale))
        img_resized = img_rgb.resize(new_size, __import__("PIL").Image.Resampling.LANCZOS)
        buf_jpeg.seek(0)
        buf_jpeg.truncate(0)
        img_resized.save(buf_jpeg, format="JPEG", quality=10)
        size_mb = len(buf_jpeg.getvalue()) / 1024 / 1024
        if size_mb <= target_single_mb:
            return base64.b64encode(buf_jpeg.getvalue()).decode()

    return base64.b64encode(buf_jpeg.getvalue()).decode()


def call_openai(model, question, pdf_paths, api_key, base_url, system_prompt, user_tmpl, is_multi_doc=False, timeout=300):
    import openai
    from openai import APITimeoutError, APIError

    client = openai.OpenAI(api_key=api_key, base_url=base_url or None, timeout=timeout)

    content = [{"type": "text", "text": "Here are the document page images："}]

    all_images = []
    for doc_idx, pdf_path in enumerate(pdf_paths, 1):
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        pdf_bytes = compress_pdf_bytes(pdf_bytes)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_single:
            tmp_single.write(pdf_bytes)
            tmp_single_path = tmp_single.name

        try:
            images = pdf_to_images(tmp_single_path)
            for img in images:
                all_images.append((doc_idx, img))
        finally:
            os.unlink(tmp_single_path)

    total_size_mb = 0
    for _, img in all_images:
        buf = __import__("io").BytesIO()
        img.save(buf, format="PNG")
        total_size_mb += len(buf.getvalue()) / 1024 / 1024

    need_compress = total_size_mb > 30
    current_total_mb = 0
    target_mb = 30 if need_compress else 50

    for doc_idx, img in all_images:
        if is_multi_doc:
            is_first_of_doc = all_images[all_images.index((doc_idx, img))][0] != all_images[all_images.index((doc_idx, img)) - 1][0] if all_images.index((doc_idx, img)) > 0 else True
            if is_first_of_doc or all_images.index((doc_idx, img)) == 0:
                content.append({"type": "text", "text": f'doc="{doc_idx}"'})

        if need_compress:
            b64 = compress_image_to_target(img, target_mb=target_mb, current_total_mb=current_total_mb)
        else:
            buf = __import__("io").BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()

        current_total_mb += len(base64.b64decode(b64)) / 1024 / 1024
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})

    content.append({"type": "text", "text": user_tmpl.format(question=question)})

    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                temperature=1,
                max_tokens=4096
            )
            return r.choices[0].message.content
        except APITimeoutError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                import time
                time.sleep(wait_time)
            else:
                raise e
        except APIError as e:
            if attempt < max_retries - 1 and "timeout" in str(e).lower():
                wait_time = 2 ** attempt
                import time
                time.sleep(wait_time)
            else:
                raise e


# ── anthropic call ──────────────────────────────────────
def call_anthropic(model, question, pdf_paths, api_key, base_url, system_prompt, user_tmpl, is_multi_doc=False, timeout=300):
    """Anthropic API call - direct PDF base64"""
    import anthropic
    from anthropic import APITimeoutError, APIError

    client = anthropic.Anthropic(api_key=api_key, base_url=base_url or None, timeout=timeout)

    content = []
    for doc_idx, pdf_path in enumerate(pdf_paths, 1):
        if is_multi_doc:
            content.append({"type": "text", "text": f'doc="{doc_idx}"'})

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        pdf_bytes = compress_pdf_bytes(pdf_bytes)
        pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

        content.append({
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": pdf_b64,
            },
        })

    content.append({"type": "text", "text": user_tmpl.format(question=question)})

    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = client.messages.create(
                model=model,
                system=system_prompt,
                messages=[{"role": "user", "content": content}],
                max_tokens=4096
            )
            for block in r.content:
                if hasattr(block, 'text'):
                    return block.text
            return ""
        except APITimeoutError as e:
            if attempt < max_retries - 1:
                import time
                time.sleep(2 ** attempt)
            else:
                raise e
        except APIError as e:
            if attempt < max_retries - 1 and "timeout" in str(e).lower():
                import time
                time.sleep(2 ** attempt)
            else:
                raise e


def infer_one(item, api, model, api_key, base_url, sys_prompt_single, user_tmpl_single,
              sys_prompt_multi, user_tmpl_multi, use_file_api=False, timeout=300, max_retries=3):
    """Run inference on a single data item

    Returns:
        dict: result dict on success
        None: on failure (caller should skip saving)
    """
    q = item["Question"]
    pdf_paths = [ROOT / pp if not Path(pp).is_absolute() else Path(pp) for pp in item["PDF_Source"]]
    dataset = item.get("dataset_type", "Single-Doc")
    is_multi_doc = dataset in ["Multi (N-Gold)", "Multi (1-Gold)"]

    if isinstance(pdf_paths, str):
        pdf_paths = [pdf_paths]

    last_error = None
    for attempt in range(max_retries):
        try:
            if api == "genai":
                if is_multi_doc:
                    ans = call_genai_file(model, q, pdf_paths, api_key, base_url, sys_prompt_multi, user_tmpl_multi, is_multi_doc=True)
                else:
                    if use_file_api:
                        ans = call_genai_file(model, q, pdf_paths, api_key, base_url, sys_prompt_single, user_tmpl_single, is_multi_doc=False)
                    else:
                        ans = call_genai_pdf_direct(model, q, pdf_paths[0], api_key, base_url, sys_prompt_single, user_tmpl_single)
            elif api == "openai":
                ans = call_openai(model, q, pdf_paths, api_key, base_url,
                                sys_prompt_multi if is_multi_doc else sys_prompt_single,
                                user_tmpl_multi if is_multi_doc else user_tmpl_single,
                                is_multi_doc, timeout)
            elif api == "anthropic":
                ans = call_anthropic(model, q, pdf_paths, api_key, base_url,
                                   sys_prompt_multi if is_multi_doc else sys_prompt_single,
                                   user_tmpl_multi if is_multi_doc else user_tmpl_single,
                                   is_multi_doc, timeout)
            else:
                raise ValueError(f"Unknown api: {api}")

            return dict(item, model_predict=ans, infer_model=model)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"    Retry {attempt + 1} failed, waiting {wait_time}s... Error: {e}")
                import time
                time.sleep(wait_time)
            else:
                print(f"    Final failure (retried {max_retries} times): {e}")
                import traceback; traceback.print_exc()
                return None

    return None


# ── main ────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="CiteVQA Inference")
    p.add_argument("--api",      required=True, choices=["openai","genai","anthropic"])
    p.add_argument("--model",    required=True)
    p.add_argument("--api_key",  required=True)
    p.add_argument("--base_url", default="")
    p.add_argument("--workers",  type=int, default=4)
    p.add_argument("--out",      default="")
    p.add_argument("--benchmark", default=str(BENCHMARK))
    p.add_argument("--limit",    type=int, default=0)
    p.add_argument("--max_pdf_mb", type=float, default=10.0)
    p.add_argument("--use_file_api", action="store_true", help="Use genai File API")
    p.add_argument("--timeout", type=int, default=500, help="API timeout (seconds), default 500")
    p.add_argument("--max_retries", type=int, default=10, help="Max API retries, default 3")
    a = p.parse_args()

    with open(a.benchmark) as f:
        data = json.load(f)
    if a.limit:
        data = data[:a.limit]
    print(f"Loaded {len(data)} items | api={a.api} model={a.model} workers={a.workers}")

    sys_p_single = (PROMPTS / "infer_system.txt").read_text()
    u_tmpl_single = (PROMPTS / "infer_user.txt").read_text()
    sys_p_multi = (PROMPTS / "infer_system_multi_doc.txt").read_text()
    u_tmpl_multi = (PROMPTS / "infer_user.txt").read_text()

    OUTPUTS.mkdir(exist_ok=True)
    if not a.out:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        a.out = str(OUTPUTS / f"{a.api}_{a.model}_{ts}.json")

    out_path = Path(a.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # ── checkpoint recovery: load existing, skip done ──────
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
    checkpoint_interval = 100

    def save_checkpoint():
        with results_lock:
            snapshot = list(results)
        with open(out_path, "w") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)

    t0 = time.time()
    failed_count = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(infer_one, it, a.api, a.model, a.api_key, a.base_url,
                          sys_p_single, u_tmpl_single, sys_p_multi, u_tmpl_multi, a.use_file_api, a.timeout, a.max_retries): it
                for it in pending}
        for fut in tqdm(as_completed(futs), total=len(pending), desc="Inference"):
            try:
                result = fut.result()
                if result is not None:
                    with results_lock:
                        results.append(result)
                        do_save = len(results) % checkpoint_interval == 0
                    if do_save:
                        save_checkpoint()
                        tqdm.write(f"    [checkpoint] saved {len(results)} items")
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1

    dt = time.time() - t0

    with open(out_path, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n{'='*60}")
    print(f"Inference done  success: {len(results)}  failed: {failed_count}  time: {dt:.1f}s")
    print(f"Output: {a.out}")


if __name__ == "__main__":
    main()
