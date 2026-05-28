# MASTER PROMPT — SyntaxSentinel / PipelineMedic

## Agen AI Otonom untuk Menyembuhkan Kegagalan CI/CD Pipeline

Saya sedang membangun project hackathon bernama **SyntaxSentinel** atau **PipelineMedic**.

Project ini adalah **AI agent otonom** yang dapat mendeteksi kegagalan CI/CD pipeline di GitLab, membaca error log, menganalisis penyebab kegagalan menggunakan Gemini di Google Cloud, lalu membuat perbaikan otomatis dalam bentuk branch baru dan Merge Request.

Project ini dibuat untuk **Google Cloud Rapid Agent Hackathon** pada **GitLab Track**.

---
CARA MENGGUNAKAN MASTER PROMPT INI:
1. Jangan jalankan semua sprint sekaligus.
2. Saya akan memberikan instruksi per SPRINT.
3. Tunggu instruksi saya sebelum Anda mulai menulis kode untuk sprint selanjutnya.
4. Jika ada error, kita akan debugging di dalam konteks sprint yang sedang berjalan.

## TUJUAN PROJECT

Bantu saya membangun project ini secara bertahap, rapi, aman, dan realistis untuk solo developer.

Tujuan utama:

1. Membuat AI agent yang bukan sekadar chatbot.
2. Agent berjalan otomatis ketika GitLab pipeline gagal.
3. Agent mampu melakukan multi-step reasoning.
4. Agent mampu memakai tools untuk membaca log, membaca file, membuat branch, commit, dan Merge Request.
5. Reasoning AI harus menggunakan Gemini / Google Cloud AI.
6. Integrasi GitLab harus terlihat jelas melalui GitLab MCP atau MCP-style tool wrapper.
7. Agent tidak boleh auto-merge.
8. Agent hanya membuat Merge Request agar manusia tetap bisa review.
9. Fokus MVP hanya pada error sederhana:

   * Python syntax error
   * dependency error di `requirements.txt`
   * import error sederhana
   * test assertion typo sederhana

---

## POSISI PROJECT

Nama utama:
**SyntaxSentinel — Autonomous CI/CD Pipeline Healing Agent**

Nama alternatif:
**PipelineMedic — AI Self-Healing CI/CD Agent**

Tagline:
**Your autonomous first responder for broken CI/CD pipelines.**

Positioning:
Project ini bukan chatbot karena tidak menunggu manusia mengetik prompt. Agent ini otomatis aktif ketika GitLab CI/CD pipeline gagal, membaca job trace dan source code, menganalisis penyebab dengan Gemini, lalu melakukan aksi nyata melalui GitLab tools dengan membuat branch, commit patch, dan membuka Merge Request.

---

## BATASAN PENTING

Dalam membangun project ini, ikuti batasan berikut:

1. Produk akhir harus menggunakan Google Cloud AI / Gemini untuk reasoning.
2. Gunakan Google Cloud Agent Builder, Agent Development Kit, Agent Engine, Vertex AI, atau tooling agent Google Cloud yang tersedia.
3. Track yang dipilih adalah GitLab.
4. Jika official GitLab MCP tersedia, gunakan itu.
5. Jika official GitLab MCP sulit digunakan, buat MCP-style wrapper untuk GitLab tools dengan interface:

   * `read_job_trace`
   * `list_pipeline_jobs`
   * `get_file_content`
   * `create_branch`
   * `commit_file_changes`
   * `create_merge_request`
6. Jangan gunakan OpenAI, Claude, atau AI non-Google sebagai bagian dari produk akhir.
7. Codex/Cursor/Copilot boleh dipakai hanya sebagai coding assistant selama development.
8. Agent tidak boleh auto-merge.
9. Agent hanya boleh membuat branch dan Merge Request.
10. Jangan buat frontend dulu.
11. Prioritaskan demo 3 menit yang stabil daripada fitur yang terlalu banyak.

---

## ARSITEKTUR TARGET

Alur sistem:

GitLab Repository
→ GitLab CI/CD Pipeline gagal
→ GitLab Webhook mengirim event ke Cloud Run
→ FastAPI menerima webhook
→ Orchestrator mengambil failed pipeline jobs
→ GitLab MCP-style client membaca failed job trace
→ Agent mengambil file path dan konteks error
→ Gemini menganalisis root cause dan membuat patch minimal
→ Safety validator mengecek confidence dan scope file
→ GitLab tool client membuat branch baru
→ GitLab tool client melakukan commit fix
→ GitLab tool client membuka Merge Request
→ Developer melakukan review manual

Stack yang digunakan:

* Python 3.10+
* FastAPI
* Uvicorn
* Pydantic
* Pydantic Settings
* httpx
* Google Cloud Vertex AI / Gemini SDK
* Google Agent Development Kit atau framework agent Google Cloud yang tersedia
* GitLab REST API sebagai fallback MCP-style tools
* Google Cloud Run
* Google Secret Manager
* GitLab CI/CD
* Pytest
* Docker

---

## STRUKTUR PROJECT YANG DIINGINKAN

Buat struktur seperti ini:

```txt
syntaxsentinel/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── endpoints/
│   │       ├── webhook.py
│   │       └── manual.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── models/
│   │   ├── gitlab.py
│   │   ├── agent.py
│   │   └── response.py
│   ├── services/
│   │   ├── gitlab_mcp_client.py
│   │   ├── agent_engine.py
│   │   ├── orchestrator.py
│   │   ├── safety.py
│   │   └── patcher.py
│   └── utils/
│       ├── traceback_parser.py
│       └── text.py
├── tests/
│   ├── test_webhook.py
│   ├── test_gitlab_client.py
│   ├── test_agent_engine.py
│   ├── test_patcher.py
│   └── fixtures/
│       ├── failed_job_trace_python.txt
│       ├── broken_app.py
│       └── fixed_app.py
├── demo-repo/
│   ├── app.py
│   ├── test_app.py
│   ├── requirements.txt
│   └── .gitlab-ci.yml
├── Dockerfile
├── .dockerignore
├── .env.example
├── requirements.txt
├── README.md
└── verify_env.py
```

---

# SPRINT 0 — SETUP AWAL

## PROMPT S0-A — Buat Kerangka Project

Bantu saya membuat kerangka awal project **SyntaxSentinel**, sebuah AI agent otonom untuk Google Cloud Rapid Agent Hackathon GitLab Track.

Tujuan sprint ini:
Membuat struktur awal backend FastAPI yang nanti akan menerima GitLab CI/CD webhook event dan menjalankan workflow self-healing dengan Gemini.

Ketentuan:

1. Jangan buat frontend.
2. Fokus pada backend yang rapi dan modular.
3. Gunakan async jika sesuai.
4. Gunakan struktur production-minded tapi tetap sederhana untuk MVP.
5. Tambahkan komentar hanya jika diperlukan.

Buat:

1. FastAPI app di `app/main.py`
2. Router di `app/api/endpoints/`
3. Pydantic settings di `app/core/config.py`
4. Logging setup di `app/core/logging.py`
5. Security helper di `app/core/security.py`
6. Folder models
7. Folder services
8. Folder tests
9. `requirements.txt`
10. `.env.example`
11. `README.md` awal

Dependencies:

* fastapi
* uvicorn[standard]
* pydantic
* pydantic-settings
* python-dotenv
* httpx
* google-cloud-aiplatform
* pytest
* pytest-asyncio
* respx
* python-multipart

Jika package Google ADK tersedia, tambahkan. Jika tidak tersedia, desain layer agent agar Google ADK bisa ditambahkan nanti.

Environment variables di `.env.example`:

* APP_ENV=development
* LOG_LEVEL=INFO
* GITLAB_BASE_URL=https://gitlab.com
* GITLAB_PERSONAL_ACCESS_TOKEN=
* GITLAB_WEBHOOK_SECRET=
* GITLAB_PROJECT_ID=
* GITLAB_DEFAULT_BRANCH=main
* GCP_PROJECT_ID=
* GCP_LOCATION=us-central1
* GEMINI_MODEL=
* DRY_RUN=true
* MAX_TRACE_CHARS=4000
* AGENT_MIN_CONFIDENCE=0.75

Tambahkan endpoint:

* `GET /`
* `GET /health`

README harus berisi:

* cara setup virtual environment
* cara install dependencies
* cara membuat `.env`
* cara menjalankan server lokal

---

## PROMPT S0-B — Verifikasi Environment dan Credential

Lanjutkan dari project yang sudah dibuat.

Buat file `verify_env.py` di root folder.

Script ini harus:

1. Load settings dari `app/core/config.py`.
2. Mengecek environment variables yang wajib ada.
3. Melakukan GET request ke `https://gitlab.com/api/v4/user` menggunakan `GITLAB_PERSONAL_ACCESS_TOKEN`.
4. Menampilkan apakah token GitLab valid.
5. Melakukan inisialisasi konfigurasi Google Cloud / Vertex AI jika memungkinkan.
6. Menampilkan apakah GCP project dan location sudah tersedia.
7. Jangan pernah print secret/token ke terminal.
8. Exit dengan kode non-zero jika credential penting belum ada.
9. Output terminal harus jelas dengan indikator sukses/gagal.

Update README dengan:

* cara membuat `.env`
* cara menjalankan `python verify_env.py`
* cara troubleshooting token GitLab yang invalid

---

# SPRINT 1 — DEMO REPOSITORY GITLAB

## PROMPT S1-A — Buat Demo Repository untuk GitLab CI

Buat folder `demo-repo/` sebagai repository contoh yang akan dipakai untuk demo.

Isi folder:

1. `app.py`
2. `test_app.py`
3. `requirements.txt`
4. `.gitlab-ci.yml`
5. `README.md`

Gunakan Python + pytest.

Versi sehat harus:

* install requirements
* menjalankan pytest
* pipeline berhasil

Tambahkan dokumentasi cara membuat error terkontrol:

1. Python syntax error
2. Missing dependency
3. Test assertion typo

Jangan buat file utama rusak secara default. File default harus sehat dan pipeline harus hijau.

GitLab CI harus:

* memakai Docker image Python
* install dependencies
* menjalankan pytest
* selesai cepat

README demo-repo harus menjelaskan:

* cara push repo ini ke GitLab
* cara membuat pipeline gagal
* cara menghubungkan webhook ke backend SyntaxSentinel

---

# SPRINT 2 — WEBHOOK LISTENER

## PROMPT S2-A — Implementasi GitLab Webhook Endpoint

Implementasikan webhook listener GitLab.

File:

* `app/api/endpoints/webhook.py`
* `app/models/gitlab.py`
* update `app/main.py`

Endpoint:
`POST /api/v1/webhook/gitlab`

Requirement:

1. Verifikasi GitLab webhook secret menggunakan header `X-Gitlab-Token`.
2. Jika secret salah, return HTTP 401.
3. Terima payload GitLab pipeline webhook.
4. Parse data:

   * `object_kind`
   * `project.id`
   * `project.web_url`
   * `object_attributes.id` sebagai `pipeline_id`
   * `object_attributes.status`
   * `object_attributes.ref`
   * `object_attributes.sha`
   * `object_attributes.source`
5. Jika status bukan `failed`, return:
   `{ "message": "Ignored: Pipeline not failed" }`
6. Jika status `failed`, return HTTP 202:
   `{ "message": "Pipeline failure detected", "pipeline_id": ..., "project_id": ... }`
7. Gunakan `FastAPI BackgroundTasks` untuk menjalankan healing process secara async.
8. Jangan anggap `job_id` ada di payload webhook. Orchestrator nanti harus mengambil failed jobs dari pipeline.
9. Tambahkan structured logging:

   * event received
   * project_id
   * pipeline_id
   * ref
   * status
   * event ignored atau accepted
10. Tambahkan tests untuk:

* invalid token
* pipeline success diabaikan
* pipeline failed diterima

Webhook harus cepat merespons. Healing process tidak boleh membuat webhook menunggu lama.

---

## PROMPT S2-B — Tambahkan Manual Fallback Endpoint

Tambahkan endpoint manual untuk demo fallback.

Endpoint:
`POST /api/v1/manual/heal-pipeline`

Tujuan:
Jika GitLab webhook gagal saat demo, saya tetap bisa memicu workflow healing secara manual.

Request body:

```json
{
  "project_id": 123,
  "pipeline_id": 456,
  "ref": "main"
}
```

Requirement:

1. Gunakan orchestrator yang sama dengan webhook.
2. Lindungi endpoint dengan header:
   `X-Demo-Token`
3. Return HTTP 202 jika diterima.
4. Log bahwa manual fallback digunakan.
5. Tambahkan tests.

---

# SPRINT 3 — GITLAB MCP-STYLE TOOL CLIENT

## PROMPT S3-A — Implementasi GitLab MCP-Style Client

Buat file `app/services/gitlab_mcp_client.py`.

Class:
`GitLabMCPClient`

Class ini mewakili layer tools GitLab berbasis MCP-style. Jika official GitLab MCP tersedia, implementasi ini bisa diganti nanti. Untuk sekarang, gunakan GitLab REST API v4 sebagai implementasi fungsional.

Method yang wajib:

1. `async def list_pipeline_jobs(project_id: int, pipeline_id: int) -> list[dict]`
2. `async def get_failed_jobs(project_id: int, pipeline_id: int) -> list[dict]`
3. `async def read_job_trace(project_id: int, job_id: int) -> str`
4. `async def get_file_content(project_id: int, file_path: str, ref: str) -> str`
5. `async def create_branch(project_id: int, branch_name: str, ref: str) -> dict`
6. `async def commit_file_changes(project_id: int, branch: str, commit_message: str, actions: list[dict]) -> dict`
7. `async def create_merge_request(project_id: int, source_branch: str, target_branch: str, title: str, description: str) -> dict`
8. `async def add_merge_request_note(project_id: int, mr_iid: int, body: str) -> dict`
9. `async def get_project(project_id: int) -> dict`

Requirement:

* Gunakan `httpx.AsyncClient`.
* Gunakan GitLab token dari config.
* Error handling harus kuat.
* Buat custom exceptions untuk:

  * GitLab authentication error
  * GitLab not found
  * GitLab rate limit
  * GitLab API generic failure
* Jangan pernah log token.
* Tambahkan request timeout.
* Tambahkan retry sederhana untuk error 5xx jika memungkinkan.
* Tambahkan dry-run mode untuk write operation.
* Dalam dry-run mode, jangan benar-benar membuat branch, commit, atau MR. Return simulated response dan log aksi yang seharusnya dilakukan.
* Tambahkan unit tests dengan mocked response.

Update README untuk menjelaskan bahwa ini adalah MCP-style GitLab tool layer dan bisa diganti dengan official GitLab MCP jika tersedia.

---

# SPRINT 4 — TRACEBACK PARSER DAN PATCHER

## PROMPT S4-A — Implementasi Traceback Parser

Buat file `app/utils/traceback_parser.py`.

Tujuan:
Mengambil informasi penting dari failed CI job trace.

Implementasikan:

1. `extract_candidate_file_paths(trace: str) -> list[str]`
2. `extract_python_error_summary(trace: str) -> dict`
3. `trim_trace(trace: str, max_chars: int) -> str`

Parser harus bisa menangani:

* Python SyntaxError
* ModuleNotFoundError
* ImportError
* pytest assertion failure
* generic traceback fallback

Contoh output:

```json
{
  "error_type": "SyntaxError",
  "file_path": "app.py",
  "line_number": 12,
  "message": "invalid syntax"
}
```

Requirement:

* Prioritaskan file yang ada di repository.
* Abaikan path dari `site-packages` jika memungkinkan.
* Tambahkan tests dengan fixture job trace.

---

## PROMPT S4-B — Implementasi Safe Patcher

Buat file `app/services/patcher.py`.

Tujuan:
Menerapkan perubahan kode secara minimal dan aman.

Implementasikan:

1. `replace_exact_snippet(file_content: str, original_snippet: str, fixed_snippet: str) -> str`
2. `validate_file_scope(file_path: str) -> bool`
3. `validate_patch_size(original_content: str, fixed_content: str) -> bool`
4. `build_gitlab_update_action(file_path: str, fixed_content: str) -> dict`

Safety rules:

* Hanya boleh memodifikasi:

  * `.py`
  * `requirements.txt`
  * `package.json`
  * `pyproject.toml`
* Tolak rewrite besar.
* Tolak perubahan jika original snippet tidak ditemukan.
* Tolak fixed content kosong.
* Tolak binary file.
* Tolak file di luar scope.
* Return pesan error yang jelas.

Tambahkan tests.

---

# SPRINT 5 — GEMINI AGENT ENGINE

## PROMPT S5-A — Bangun Gemini Reasoning Module

Buat file `app/services/agent_engine.py`.

Tujuan:
Menggunakan Gemini melalui Google Cloud / Vertex AI untuk menganalisis failed CI job trace dan mengusulkan perbaikan kecil yang aman.

Function:
`async def analyze_and_plan_fix(job_trace_log: str, source_file_path: str, source_code: str) -> FixPlan`

Buat Pydantic model `FixPlan` di `app/models/agent.py` dengan field:

* `root_cause: str`
* `error_type: str`
* `file_to_modify: str`
* `original_snippet: str`
* `fixed_snippet: str`
* `full_fixed_file_content: str | None`
* `confidence_score: float`
* `explanation: str`
* `risk_level: str`
* `should_create_merge_request: bool`

System instruction untuk Gemini:
Kamu adalah SyntaxSentinel, AI DevOps Engineer otonom. Tugasmu adalah memperbaiki CI/CD pipeline yang gagal secara aman.

Aturan:

1. Kamu hanya boleh memperbaiki Python syntax error kecil, missing dependency, import typo, atau test assertion mismatch sederhana.
2. Jangan melakukan refactor business logic.
3. Jangan rewrite seluruh project.
4. Jangan membuat file baru yang tidak ada.
5. Kamu hanya boleh memodifikasi file yang diberikan.
6. Patch harus minimal.
7. Jika tidak yakin, set `should_create_merge_request` ke false.
8. Jika fix membutuhkan pemahaman business logic yang besar, tolak.
9. Selalu jelaskan root cause secara singkat.
10. Return hanya JSON terstruktur sesuai schema.

User prompt harus memuat:

* trimmed job trace
* candidate file path
* source code
* allowed fix types
* output JSON schema

Requirement:

* Gunakan Gemini model melalui Google Cloud / Vertex AI.
* Jangan gunakan OpenAI atau AI non-Google.
* Parse structured output ke `FixPlan`.
* Validasi confidence score.
* Jika parsing gagal, return safe failure.
* Tambahkan mocked tests untuk successful fix dan rejected fix.
* Logging boleh mencatat ringkasan aksi, tetapi jangan menampilkan chain-of-thought tersembunyi.

---

# SPRINT 6 — ORCHESTRATOR SELF-HEALING LOOP

## PROMPT S6-A — Implementasi Healing Orchestrator

Buat file `app/services/orchestrator.py`.

Function:
`async def run_healing_process(project_id: int, pipeline_id: int, ref: str) -> dict`

Workflow:

1. Log bahwa healing process dimulai.
2. Gunakan `GitLabMCPClient.get_failed_jobs` untuk mencari failed jobs dari pipeline.
3. Jika tidak ada failed jobs, stop dengan aman.
4. Pilih failed job yang paling relevan.
5. Baca job trace.
6. Trim trace sesuai max length dari config.
7. Ekstrak candidate file path dari trace.
8. Ambil isi source file dari GitLab.
9. Panggil `analyze_and_plan_fix`.
10. Validasi:

    * confidence score >= minimum threshold
    * `should_create_merge_request` bernilai true
    * scope file diizinkan
    * ukuran patch aman
11. Buat fixed content.
12. Buat branch:
    `syntaxsentinel/fix-pipeline-{pipeline_id}`
13. Commit file update.
14. Buat Merge Request ke branch asli/default branch.
15. Deskripsi MR harus berisi:

    * root cause
    * penjelasan fix
    * confidence score
    * safety note
    * original pipeline ID
    * disclaimer: generated by SyntaxSentinel and requires human review
16. Tambahkan label MR jika memungkinkan:
    `ai-auto-fix`
17. Return structured result.

Penting:

* Dalam dry-run mode, lakukan semua proses kecuali write operation.
* Agent tidak boleh auto-merge.
* Jika safety validation gagal, stop dan log alasan yang jelas.
* Gunakan try/except agar background task tidak crash diam-diam.
* Tambahkan tests dengan mocked GitLab client dan mocked Gemini agent.

---

# SPRINT 7 — END-TO-END DEMO

## PROMPT S7-A — Buat Skenario Demo yang Stabil

Buat skenario demo end-to-end untuk SyntaxSentinel.

Tujuan:
Demo harus stabil untuk direkam dalam video 3 menit.

Buat:

1. Demo repo Python yang sehat.
2. Controlled commit yang memasukkan syntax error kecil.
3. GitLab CI pipeline gagal.
4. Webhook event ke backend SyntaxSentinel.
5. Agent-generated MR yang memperbaiki syntax error.
6. Pipeline di MR branch berubah hijau.

Tambahkan dokumentasi:

* Step 1: Prepare demo repo
* Step 2: Connect GitLab webhook
* Step 3: Break the pipeline
* Step 4: Wait for agent
* Step 5: Show generated MR
* Step 6: Show pipeline recovery

Tambahkan fallback:

* Jika webhook gagal, gunakan manual endpoint.
* Jika output Gemini tidak stabil, gunakan pre-tested controlled error trace.
* Jika Cloud Run cold start lambat, panggil health endpoint sebelum rekaman.

Buat file `DEMO_SCRIPT.md` berisi:

* narasi video 3 menit
* urutan layar yang harus ditampilkan
* apa yang ditampilkan di terminal
* apa yang ditampilkan di GitLab
* apa yang tidak boleh ditampilkan, seperti secret/token

---

# SPRINT 8 — CLOUD RUN DEPLOYMENT

## PROMPT S8-A — Dockerize dan Deploy ke Cloud Run

Siapkan backend untuk deployment ke Google Cloud Run.

Buat:

1. `Dockerfile` menggunakan `python:3.10-slim`
2. `.dockerignore`
3. optional `cloudbuild.yaml`
4. bagian deployment di README

Dockerfile requirement:

* install dependencies
* expose port 8080
* run uvicorn di `0.0.0.0:8080`
* jangan copy file yang tidak perlu
* gunakan non-root user jika mudah
* compatible dengan Cloud Run

Tambahkan health check:
`GET /health`

Cloud Run deployment requirement:

* service name: `syntaxsentinel-agent`
* region: `us-central1`
* allow unauthenticated requests karena GitLab webhook harus bisa mengakses endpoint
* validasi keamanan tetap memakai GitLab webhook secret
* set min instances = 0
* dokumentasikan cara set environment variables
* rekomendasikan menyimpan secret di Google Secret Manager
* ingatkan untuk tidak commit `.env`

Berikan command untuk:

1. build dan deploy dengan gcloud
2. update env vars
3. melihat logs
4. delete service setelah hackathon jika perlu

---

# SPRINT 9 — README, DEVPOST, DAN SUBMISSION

## PROMPT S9-A — Buat README Final

Tulis README yang profesional untuk project ini.

README harus berisi:

1. Nama project dan tagline
2. Problem statement
3. Kenapa ini bukan chatbot
4. Cara kerja sistem
5. Architecture diagram dalam bentuk teks
6. Tech stack
7. Penggunaan Google Cloud
8. Integrasi GitLab MCP / MCP-style tools
9. Safety design
10. Demo flow
11. Local setup
12. Environment variables
13. Running tests
14. Cloud Run deployment
15. Limitations
16. Future improvements
17. License
18. Hackathon submission note

Tone:

* profesional
* ringkas
* cocok untuk Devpost dan GitHub portfolio

---

## PROMPT S9-B — Draft Submission Devpost

Tulis draft submission Devpost untuk SyntaxSentinel.

Isi:

1. Inspiration
2. What it does
3. How we built it
4. How we used Google Cloud
5. How we used GitLab partner integration
6. Challenges we ran into
7. Accomplishments we are proud of
8. What we learned
9. What's next
10. Why it is not just a chatbot

Poin penting:

* Triggered by GitLab pipeline failure.
* Reads job traces.
* Reasons with Gemini.
* Creates a fix branch.
* Commits code changes.
* Opens a Merge Request.
* Keeps humans in the loop.
* Never auto-merges.
* Only handles safe, small fixes in MVP.

Tulisan harus jelas, impressive, dan jujur.

---

# SPRINT 10 — FINAL POLISH DAN SAFETY

## PROMPT S10-A — Final Code Review dan Hardening

Lakukan review final untuk seluruh codebase.

Cek:

1. Tidak ada secret yang ter-commit.
2. `.env` masuk `.gitignore`.
3. `.env.example` aman.
4. Webhook token diverifikasi.
5. Dry-run mode berjalan.
6. Agent tidak pernah auto-merge.
7. Agent menolak fix dengan confidence rendah.
8. Logs berguna tapi tidak membocorkan secret.
9. README jelas.
10. Tests pass.
11. Docker build berhasil.
12. Instruksi Cloud Run benar.
13. Demo script realistis.
14. GitLab API errors tertangani.
15. Background tasks tidak crash diam-diam.
16. Project jelas menggunakan Gemini/Google Cloud.
17. GitLab tool layer jelas terdokumentasi sebagai MCP-style integration atau official MCP jika tersedia.

Buat final checklist:

* Local run passed
* Verify env passed
* Test suite passed
* Docker build passed
* Cloud Run deployed
* GitLab webhook configured
* Demo scenario tested
* GitHub repo public
* MIT License added
* Demo video recorded
* Devpost form completed

---

# SCRIPT DEMO 3 MENIT

Gunakan narasi ini sebagai dasar.

0:00–0:30 — Masalah
“Modern software teams rely on CI/CD pipelines, but small syntax errors or dependency issues can break delivery and force developers to context-switch into logs. SyntaxSentinel is an autonomous AI agent that acts as the first responder for broken GitLab pipelines.”

0:30–1:00 — Trigger
“I will intentionally introduce a small syntax error into this Python repository and push it to GitLab. The pipeline starts and fails.”

1:00–1:40 — Reasoning dan Tool Use
“The failure triggers a GitLab webhook to my Cloud Run service. The agent reads the failed job trace through GitLab tools, extracts the relevant file, and asks Gemini on Google Cloud to produce a safe minimal fix.”

1:40–2:20 — Action
“This is not a chatbot. It does not only suggest a fix. It creates a new branch, commits the patch, and opens a Merge Request with a root-cause explanation and confidence score.”

2:20–3:00 — Result
“Here is the generated Merge Request. The fix is isolated, reviewable, and human-approved. When the pipeline runs again, it turns green. SyntaxSentinel turns CI downtime into an automated self-healing workflow.”

---

# MVP RULES

Wajib ada:

1. GitLab pipeline failure detection.
2. GitLab webhook.
3. Gemini analysis.
4. Read failed job trace.
5. Read source file.
6. Generate minimal fix.
7. Create branch.
8. Commit fix.
9. Open Merge Request.
10. Safety validation.

Wajib dibuang:

1. React frontend.
2. Auto-merge.
3. Fix complex logic bugs.
4. Multi-language support.
5. Dashboard besar.
6. User authentication.
7. Multi-agent architecture.
8. Full production-grade observability.
9. Complex security scanning.
10. Broad arbitrary code repair.

Success definition:
Project dianggap berhasil jika bisa menunjukkan satu loop penuh secara stabil:

failed pipeline → webhook → Gemini analysis → GitLab tool actions → Merge Request → fixed pipeline.

---

# INSTRUKSI AKHIR UNTUK AI CODING ASSISTANT

Saat mengimplementasikan project ini, selalu prioritaskan:

1. Demo yang stabil.
2. Logs yang jelas.
3. Fix kecil dan aman.
4. Human-in-the-loop melalui Merge Request.
5. Compliance dengan Google Cloud/Gemini.
6. Integrasi GitLab partner.
7. Storytelling hackathon.
8. README yang layak untuk portfolio.

Jangan over-engineer. Bangun agent paling kecil yang bisa memberikan “wow moment” paling kuat dalam demo 3 menit.
