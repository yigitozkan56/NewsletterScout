# 📬 NewsletterScout

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi&logoColor=white)
![Legal Data Flow](https://img.shields.io/badge/Data%20Flow-Public%20RSS%20%2B%20Creator%20Opt--In-success)

**NewsletterScout** is an open-source directory and sponsor-matching engine that connects developer tool makers and sponsors with niche newsletters by analyzing public RSS cadence and creator opt-in metadata.

---

## ⚖️ Legal Data Architecture & Compliance

- **Public RSS & Voluntary Opt-In Only:** Consumes strictly public RSS feeds and metadata voluntarily registered by newsletter publishers (`/api/opt-in`).
- **Zero Paywall Bypassing:** Never scrapes paid Substack/Beehiiv archives or harvests private subscriber emails.
- **Local SQLite Cache:** Stores opt-in newsletter profiles locally in `newsletterscout_cache.db`.

---

## 📊 Sample Output

```text
Newsletter                           | Cadence    | Subscribers  | Sponsor Fit
------------------------------------------------------------------------------
Indie AI & Micro-SaaS Builders Diges | Bi-Weekly  | 12,400       | 100.0%
Pragmatic DevOps & Cloud Native Week | Weekly     | 18,500       | 0.0%
Modern TypeScript & UI Engineering B | Weekly     | 24,000       | 0.0%
```

| Newsletter | Niche Tags | Cadence | Opt-In Subscribers | Sponsor Fit |
| :--- | :--- | :---: | :---: | :---: |
| **Indie AI & Micro-SaaS Builders Digest** | `ai,llm,micro-saas,python` | Bi-Weekly | 12,400 | **100.0%** |
| **Pragmatic DevOps & Cloud Native Weekly** | `devops,kubernetes,cloud,sre` | Weekly | 18,500 | **66.7%** |
| **Modern TypeScript & UI Engineering Bytes** | `typescript,react,frontend` | Weekly | 24,000 | **33.3%** |

---

## 🚀 Step-by-Step Installation

```bash
git clone https://github.com/yigitozkan56/NewsletterScout.git
cd NewsletterScout
cp .env.example .env
pip install -r requirements.txt
```

---

## 💻 Usage Examples

### CLI Mode
```bash
# Match sponsor campaign keywords against opt-in newsletters
python app.py match --tags "ai,python,micro-saas"
```

### Web Dashboard & REST API Mode
```bash
python app.py serve --port 8008
```
Visit `http://127.0.0.1:8008` or `POST http://127.0.0.1:8008/api/opt-in`.

### Running Unit Tests
```bash
pytest tests/
```

---

## 🗺️ Roadmap

- [x] Public RSS 2.0 cadence & issue frequency analyzer
- [x] Voluntary publisher opt-in registration endpoint (`/api/opt-in`)
- [x] Sponsor niche-fit scoring & SQLite cache
- [ ] OPML bundle import/export for curated developer reading lists
- [ ] Automated RSS dead-link health check
