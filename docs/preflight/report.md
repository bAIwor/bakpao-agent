TASK: 00 — Preflight
STATUS: PARTIAL
P1_muse_image: PASS | long_string:result(len=575308) saved=p1_image.webp(431480B) | $0.01
P2_spark_vision_json: PASS | {"confidence": 0.99, "detected_amount": 13185, "detected_reference": "TRX20261029ABC"}
P3_sam31_api: PASS | empty=True
P4_sam21_modal: NOT_RUN
P5_voice: FAIL | POST /audio/transcriptions http=404
P6_wonder: PASS | {"in": 112, "out": 122, "rea": 112} $0.0028
P7_harga_bahan: PASS | Badan Pangan Nasional — data.badanpangan.go.id/datasetpublications/5up/rata-rata-harga-pangan-bulanan-konsumen-provinsi | 2026-10-28
TOTAL_COST: $0.0152 (belum termasuk GPU P4)
FILES: scripts/preflight.py, docs/preflight/harga_bahan.json
BLOCKERS: none

DETAIL_JSON:
{
 "p1": {
  "status": "PASS",
  "http": 200,
  "seconds": 20.2,
  "top_keys": [
   "created_at",
   "error",
   "id",
   "incomplete_details",
   "instructions",
   "model",
   "object",
   "output",
   "parallel_tool_calls",
   "status",
   "usage"
  ],
  "image_evidence": "long_string:result(len=575308) saved=p1_image.webp(431480B)",
  "usage": {
   "in": 11092,
   "out": 1144,
   "rea": 338
  },
  "usd": 0.01,
  "raw_trunc": "{\"model\": \"muse-image-1.0\", \"id\": \"resp_6ae24a6ae720e179f0214287\", \"object\": \"response\", \"status\": \"completed\", \"created_at\": 1793215082.0, \"error\": null, \"incomplete_details\": null, \"output\": [{\"type\": \"reasoning\", \"id\": \"rs_6ae24a6aab0609ecfcdf4c72\", \"summary\": [{\"type\": \"summary_text\", \"text\": \"**Drafting premium bakpao poster**\\nI'm planning a realistic product photo with steamed bakpao, some cut open to show the filling, set on cream-brown rustic tones with bamboo and kraft accents, and leaving clear empty space for price and product name.\\n**Designing premium bakpao poster**\\nI'm planning a 1:1 poster with realistic bakpao shots, whole and cut open with chocolate filling, plus space at the bottom for \\\"NAMA PRODUK\\\" and \\\"RP \\u2014\\u2014\\u2014\\\" and a top header \\\"KATALOG BAKPAO PREMIUM\\\".\"}], \"status\": \"completed\"}, {\"type\": \"message\", \"id\": \"msg_6ae24a6a42e4fc675cdf4623\", \"role\": \"assistant\", \"content\": [{\"type\": \"output_text\", \"text\": \"\", \"annotations\": [], \"logprobs\": []}], \"status\": \"completed\"}, {\"type\": \"image_generation_call\", \"id\": \"ig_eyJwZXJtYW5lbnRfdXJsIjoiR0puMEF6U2tQOTRJaFpjREFBWUlNaGNlRlV0ZWJnMWlBUUJlIiwicmVzdW1lX2lkIjoiczoxYmI2YzMwYS1lMjA0LTQ0MTAtOTEzZC03NzQxMjhlZGRiOWI6R0hsSUJqUUg2YlptNGo4R0FBbEhiUnJQWU5ZdWJnMWlBUUJqIiwiYmluZGluZyI6eyJhcHBfaWQiOjI2Mzk1NzM1NDY0OTk5NDksIm1vZGVsIjoibXVzZS1pbWFnZS0xLjAifSwidmVyc2lvbiI6MSwiY3JlYXRlZF9hdCI6MTc5MzIxNTA4Mn0.Q8WLFwEgsw-CsflAimGXSmHV6yIS\", \"status\": \"completed\", \"result\": \"UklGRnCVBgBXRUJQVlA4WAoAAAAEAAAAPwYAPwYA"
 },
 "p2": {
  "status": "PASS",
  "http": 200,
  "seconds": 5.6,
  "parsed": {
   "confidence": 0.99,
   "detected_amount": 13185,
   "detected_reference": "TRX20261029ABC"
  },
  "usage": {
   "in": 590,
   "out": 446,
   "rea": 407
  },
  "usd": 0.0024
 },
 "p3": {
  "status": "PASS",
  "http": 200,
  "seconds": 4.7,
  "empty_confirmed": true,
  "usage": {
   "input_tokens": 0,
   "input_tokens_details": {
    "cached_tokens": 0
   },
   "output_tokens": 0,
   "output_tokens_details": {
    "reasoning_tokens": 0
   },
   "total_tokens": 0,
   "images_processed": 1
  },
  "usd": 0.0,
  "raw_trunc": "{\"top_logprobs\": 0, \"temperature\": 1.0, \"top_p\": 1.0, \"service_tier\": \"auto\", \"model\": \"sam-3.1\", \"background\": false, \"tools\": [], \"tool_choice\": \"auto\", \"truncation\": \"disabled\", \"id\": \"resp_6ae24a757d02ea7b2c8847ed\", \"object\": \"response\", \"status\": \"completed\", \"created_at\": 1793215093.0, \"completed_at\": 1793215093.0, \"error\": null, \"incomplete_details\": null, \"output\": [{\"type\": \"message\", \"id\": \"msg_263a480d-8758-4972-8cae-b6b8f21db2ea\", \"role\": \"assistant\", \"content\": [{\"type\": \"output_text\", \"text\": \"\", \"annotations\": [], \"logprobs\": []}], \"status\": \"completed\"}], \"instructions\": null, \"usage\": {\"input_tokens\": 0, \"input_tokens_details\": {\"cached_tokens\": 0}, \"output_tokens\": 0, \"output_tokens_details\": {\"reasoning_tokens\": 0}, \"total_tokens\": 0, \"images_processed\": 1}, \"parallel_to"
 },
 "p5": {
  "status": "FAIL",
  "voice_in_models": true,
  "transcribe_endpoint": "POST /audio/transcriptions",
  "http": 404,
  "seconds": 6.7,
  "response_trunc": ""
 },
 "p6": {
  "status": "PASS",
  "http": 200,
  "seconds": 6.2,
  "text": "OK",
  "usage": {
   "in": 112,
   "out": 122,
   "rea": 112
  },
  "usd": 0.0028
 },
 "p7": {
  "status": "PASS",
  "sumber": "Badan Pangan Nasional — data.badanpangan.go.id/datasetpublications/5up/rata-rata-harga-pangan-bulanan-konsumen-provinsi",
  "tanggal_data": "2026-10-28",
  "items": {
   "Daging Ayam Ras": "Rp35,919",
   "Garam Konsumsi": "Rp10,867",
   "Gula Pasir Lokal/Curah": "Rp17,469",
   "Minyak Goreng Curah": "Rp18,053",
   "Minyak Goreng Kemasan": "Rp19,084",
   "Telur Ayam Ras": "Rp26,971",
   "Tepung Terigu Curah": "Rp8,765",
   "Tepung Terigu Kemasan": "Rp11,774"
  }
 },
 "p4": {
  "status": "NOT_RUN"
 }
}