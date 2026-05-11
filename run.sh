#genai/openai/anthropic
API_TYPE=openai
API_KEY=YOUR_OPENAI_KEY
BASE_URL=YOUR_OPENAI_URL

#infer
python infer/run.py \
  --api ${API_TYPE} \
  --model gpt-5.4 \
  --base_url ${BASE_URL} \
  --api_key ${API_KEY} \
  --workers 4 \
  --out outputs/infer/gpt-5.4.json

#eval
python eval/run.py \
  --judge_api ${API_TYPE} \
  --judge_model Qwen3-VL-235B-A22B-Instruct \
  --judge_api_key ${API_KEY} \
  --input outputs/infer/gpt-5.4.json \
  --base_url ${BASE_URL} \
  --out outputs/eval/gpt-5.4.json \
  --workers 24

#final_result
python eval/summarize.py \
  --input outputs/eval/gpt-5.4.json \
  --out_dir outputs/eval/gpt-5.4