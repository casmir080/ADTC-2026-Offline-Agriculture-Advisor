# REPORT.md — ADTC 2026 Submission

## 1. Problem Definition

- **Domain track:** Agriculture
- **Specific problem:** An offline crop advisory assistant for smallholder
  farmers across Sub-Saharan Africa, covering three staple crops (maize,
  cassava, common bean). It identifies likely pest/disease/nutrient
  issues from a description of symptoms and gives an explanation plus
  a season-aware risk assessment, without any cloud connection.
- **Why on-device matters here:** Smallholder farmers are exactly the
  population blocked by cloud-dependent AI tools — unreliable
  connectivity, data costs, and inconsistent power make a cloud API a
  non-starter for daily use in the field. An offline tool that runs on
  a single low-cost laptop removes all three barriers at once.

## 2. Constraints

- **Target hardware:** Intel/AMD x86-64, integrated graphics only, 8GB
  RAM, Ubuntu 22.04 (ADTC Standard Laptop)
- **Hard memory ceiling:** 7GB peak RSS
- **Development environment note:** built and tested on Windows +
  WSL2 (Ubuntu) rather than a single native Ubuntu machine, due to
  available hardware. This introduces a Windows↔WSL network hop that
  does not exist on the true target hardware, which measurably slowed
  generation speed during development (see Known Limitations). All
  functional behavior was verified correct regardless of this overhead.
- **Dev hardware caveat:** development/testing happened on an Intel
  i5-3437U (3rd gen, 2013), well below the ADTC spec floor of 10th-12th
  gen and lacking AVX2 instructions that modern quantized inference
  relies on for speed. Reported tok/s figures below are a conservative
  floor from this hardware, not a reflection of expected performance
  on spec-compliant 10th-12th gen hardware.

## 3. Design Decisions

| Decision | Choice | Why |
|---|---|---|
| Base model | `llama3.2:3b` (Q4_K_M GGUF, 1.87 GiB) | Fits comfortably under the 7GB ceiling with large margin; 3B scale gave consistently correct domain answers in testing across all 3 crops |
| Quantization | Q4_K_M, via Ollama's prebuilt GGUF | Standard quality/memory tradeoff point; no custom quantization needed since Ollama ships this directly |
| Runtime | Ollama (llama.cpp backend) | CPU-only inference, no GPU dependency, matches target hardware exactly |
| RAG approach | TF-IDF retrieval (scikit-learn) over local `.md` corpus | Zero additional model/RAM cost vs. a neural embedding model; verified accurate across all 8 corpus topics in testing (see Benchmarks) |
| Hybrid component | Rule-based agronomic risk engine (`app/risk_model.py`) + LLM | Classical, deterministic, explainable risk logic grounded in real pest/pathogen vector behavior (e.g. fungal spread favored by humidity, whitefly/leafhopper vectors favored by dry heat), paired with the LLM for explanation. The LLM is explicitly instructed to incorporate this computed risk level rather than inventing urgency language itself — verified working end-to-end in testing. |
| Localization | Yoruba menu mode (fixed answers), not free-form generation | Direct testing showed `llama3.2:3b` cannot reliably comprehend or generate Yoruba (it echoed a Yoruba question back unchanged instead of answering — the model's documented supported languages do not include Yoruba). A menu of pre-written, reviewable Yoruba answers sidesteps this entirely and is arguably better UX for a farmer who may prefer selecting from a list to typing. |

## 4. Tools & Frameworks

- Runtime: Ollama (llama.cpp backend), GGUF model format
- Language: Python 3.11
- Key libraries: scikit-learn (TF-IDF retrieval), requests (Ollama API
  client), psutil (memory watchdog), pytest (test suite)
- Testing: 28 automated tests (`pytest -v`) — 2 covering RAG retrieval,
  26 covering the risk engine's topic identification and risk scoring
  across all 8 corpus topics × 2 seasons

## 5. Benchmarks

| Metric | Value | How measured |
|---|---|---|
| Model server memory | 2,442 MiB (model 1,918 + KV cache 448 + compute 76) | Direct from Ollama/llama.cpp's own memory breakdown log during a real run |
| App memory (RAG + Python runtime) | 117.7 MB (120,524 KB) | `/usr/bin/time -v python -m app.main`, Maximum resident set size |
| **Estimated total peak RAM** | **~2.52 GB (~36% of 7GB budget)** | Sum of the above two, measured separately due to the Windows/WSL dev split described in Constraints |
| Generation speed (llama3.2:3b) | 2.4–8.3 tok/s | Ollama's own `eval_count`/`eval_duration` fields, multiple real queries, on dev hardware below ADTC spec |
| Generation speed (llama3.2:1b, dev-only reference) | ~8 tok/s | Same method, used only for faster local iteration, not the submitted model |
| Accuracy | 8/8 topics across 3 crops correctly diagnosed in manual testing; 28/28 automated tests passing | Manual Q&A verification + `pytest -v` |
| Thermal | Not yet measured | Requires the official ADTC profiler tool / target hardware; not measurable reliably in the dev environment described above |

**Note on speed:** because dev/test hardware is well below the ADTC
spec floor (2013-era CPU without AVX2, plus cross-VM network overhead),
the tok/s figures above should be read as a conservative lower bound.
We expect meaningfully higher throughput on actual 10th-12th gen audit
hardware.

## 6. Bonus Claims

- [x] **African language support (Yoruba):** A dedicated menu-driven
  Yoruba mode (`app/yoruba_menu.py`) covers all 4 of the most common
  issues tested (fall armyworm, nitrogen deficiency, cassava mosaic
  disease, anthracnose) with fixed, pre-written Yoruba answers.
  **Caveat: these translations are a first draft and have not yet been
  reviewed by a native Yoruba speaker.** This review is planned before
  final submission; until completed, this should be treated as a
  functional prototype of the localization approach rather than a
  fully verified claim.
- [ ] Budget laptop profile — not yet tested on a separate, lower-spec
  machine matching the $150-250 refurbished tier.

## 7. Known Limitations

- TF-IDF retrieval matches on shared words, not meaning — it will miss
  questions that paraphrase symptoms using entirely different
  vocabulary than the corpus. A future improvement would be a
  lightweight local embedding model, traded carefully against the
  memory budget.
- The corpus currently covers 8 specific issues across 3 crops. It is
  deliberately narrow rather than broad, to keep what's covered
  verified and accurate rather than spreading thin.
- Yoruba content needs native-speaker verification before it can be
  considered submission-ready (see Bonus Claims).
- Memory and speed benchmarks were gathered in a constrained dev
  environment (Windows+WSL split, sub-spec CPU) rather than a single
  ADTC-spec machine; we treat these as directional, not final, and
  expect the official profiler run to supersede them.
- No thermal throttling data has been collected yet.

## 8. Cross-Disciplinary Integration

The required cross-disciplinary integration is the pairing of a
**deterministic, rule-based agronomic risk engine** with the
generative LLM. Rather than letting the LLM invent how urgent a given
pest or disease risk is, `app/risk_model.py` encodes real epidemiological
behavior — for example, that fungal pathogens like anthracnose and bean
rust spread fastest in humid/rainy conditions, while whitefly- and
leafhopper-transmitted viruses (cassava mosaic disease, maize streak
virus) spread fastest when vector insect populations build up in warm,
dry conditions. Given a detected topic and the user-reported season,
this engine computes a risk level and rationale *before* the LLM ever
generates text, and the LLM is instructed to incorporate that computed
risk into its explanation rather than generating its own urgency
framing. This was directly verified in testing: asking about fall
armyworm symptoms in "dry" season triggered a `HIGH risk` rule-engine
output, which then appeared explicitly in the model's final answer
("Given the high risk associated with Fall Armyworm... it's essential
to take action promptly").

---

## Addendum: Web UI, Confidence Warning, and Dev-Environment Tuning

Added after initial benchmarking, to satisfy the brief's explicit call
for "UX that makes the model feel responsive even on constrained
hardware."

### Web UI (`app/web.py`)

A lightweight Flask interface (server-rendered, no JS framework, to
stay light on an 8GB/no-GPU target) wraps the same RAG + risk engine +
LLM pipeline already used by the CLI (`app/main.py`). Both now share
identical prompt-building and generation logic via `app/llm.py`, so
the two interfaces never drift apart in behavior. The UI includes:

- A color-coded risk badge (red/amber/green for HIGH/MEDIUM/LOW) so
  the hybrid risk engine's output is immediately visible, not just
  present in logs.
- A season selector (dry/rainy) feeding directly into the risk engine.
- Source attribution and live tok/s shown per response, for transparency.

### Confidence warning (`LocalRetriever.is_low_confidence`)

If the top RAG match scores below `CONFIDENCE_THRESHOLD` (0.15,
configurable in `app/config.py`), the UI surfaces an explicit warning
recommending the user consult a local agricultural extension officer,
*before* the LLM's answer. This was a deliberate design choice: rather
than letting the model silently answer outside its actual knowledge
base with unwarranted confidence, the system flags when it's reaching
beyond what it can verify.

### Dev-environment tuning: TOP_K reduced from 3 to 2

During web UI testing, requests routed across the Windows-host /
WSL-guest network boundary (an artifact of this specific dev setup,
not the target hardware) were observed to fail consistently around
the 165-180 second mark, regardless of the client-side timeout
configured in our own code. This pointed to an idle-connection limit
in the WSL2 NAT layer itself, external to our application. Reducing
`TOP_K` from 3 to 2 shortened prompt length enough to reliably finish
under that ceiling. **This is a dev-environment workaround, not a
correctness or quality fix** — it was not needed and is not expected
to be needed on a single-OS ADTC Standard Laptop with no equivalent
network hop.

### Model choice for web demo: llama3.2:1b

Given the combination of sub-spec dev hardware (2013-era CPU, no
AVX2) and the WSL/Windows network constraint above, the web UI was
verified end-to-end and is intended for demonstration using
`llama3.2:1b` rather than the `llama3.2:3b` used for the CLI
benchmarks earlier in this report. This is a pragmatic accommodation
for this development environment, not a claim about which model is
recommended for the final ADTC audit — `llama3.2:3b` remains the
primary submitted model, comfortably within the 7GB budget on its own
(see Benchmarks), and is expected to run without these networking
constraints on true single-OS target hardware.

Confirmed working end-to-end via web UI on this dev setup:
194 tokens generated in 35.2s (5.5 tok/s, llama3.2:1b), full request
completing in 1m34s total — comfortably under the dev-environment
network ceiling described above.
