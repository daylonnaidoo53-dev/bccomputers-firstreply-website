# BCComputers AI Workspace Starter

**Your first AI workspace.** One folder that turns Claude Code, Codex, Gemini CLI,
Cursor, or Devin into an assistant that knows who you are, what you're building,
and how to stay safe while it works.

Built by **Daylon Naidoo · BCComputers**. Free. Yours to keep, change, and share.

---

## What this is

Drop this folder on any machine, open your AI agent inside it, and the rules load
themselves:

| Thing | What it does |
|---|---|
| `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` | Always-on instructions your agents read in every session (mirrors — keep them in sync) |
| `BRAIN.md` | One page about you, your business, and your rules |
| `directives/` | Playbooks — plain-English "how to do X" the agent follows |
| `execution/` | Small scripts for steps that must never vary |
| `templates/` | Copy-paste starters for projects, daily sheets, playbooks, session pickups |
| `drafts/` | Where client messages get drafted — the human always sends |
| `.env.example` | Where secrets go (never commit the real `.env`) |

## 5-minute setup

1. **Unzip** this folder and move it where you work (e.g. your home folder).
   This folder is now your workspace root.
2. **Fill in `BRAIN.md`** — replace every `[...]` with your real details. This is
   the most important step: it is how your agent knows your world.
3. **Copy `.env.example` to `.env`** and add any API keys. Never share `.env`.
4. **Test the engine:** `python execution/example_new_day.py` (or `python3` on
   Linux/macOS) — creates today's `TODAY.md` daily sheet.
5. **Start your agent** inside this folder and say:
   *"Read my workspace and tell me what's set up."*

## Which file does my agent read?

| Tool | Reads |
|---|---|
| Claude Code | `CLAUDE.md` |
| Codex (OpenAI) | `AGENTS.md` |
| Gemini CLI | `GEMINI.md` |
| Cursor | `AGENTS.md` / `CLAUDE.md` / `.cursor/rules/` |
| Devin | `AGENTS.md` / `CLAUDE.md` |

The three instruction files are mirrors: edit `AGENTS.md`, then copy it over the
other two so they stay in sync.

## The idea (30 seconds)

AI agents are great at judgment and bad at consistency. This kit splits the two:

- **Playbooks** (`directives/`) tell the agent HOW — plain-language steps.
- **Engine** (`execution/`) does the parts that must be identical every time.
- **You** keep the decisions — nothing sends, deploys, or spends without your go.

That last part is the **Hard Gate** in `AGENTS.md`: the one rule that keeps AI
safe to use. If an agent ever ignores it, that is a bug — tell the agent, and
keep the gate.

## Make it yours

- Rename the folder, delete sections, add playbooks — it's yours.
- New project? Copy `templates/project-AGENTS.md` into the project folder.
- New playbook? Copy `templates/playbook.md` into `directives/`.
- License: **CC BY 4.0** — share and adapt freely, keep the attribution.

---

## Kit version

**1.0 — 2026-08-31**

- Initial public release: always-on agent rules, BRAIN template, 3 example
  playbooks, 4 templates, example engine script, secrets + git safety.

---

## BCComputers First-Reply System — Marketing Website

Single-page marketing website built for Daylon Naidoo (BCComputers, Paarl) selling the First-Reply System v1.0.

### Tech Stack
- **HTML5**: Semantic, accessible markup (`lang="en-ZA"`).
- **CSS**: Vanilla CSS in `css/styles.css` with CSS custom properties and modern dark aesthetic.
- **JavaScript**: Hand-authored vanilla JS in `js/main.js` (UI) and `js/quote-form.js` (validation + Firestore).
- **Firebase**: Firestore (collection: `leads`), Firebase Hosting, Security Rules (`firestore.rules`).
- **Preview**: Built-in zero-dependency preview server in `scripts/serve.cjs`.

### File Structure
```
├── index.html                  # Single-page marketing site
├── css/
│   └── styles.css              # Custom properties, dark slate theme, responsive layout
├── js/
│   ├── firebase-config.js      # Firebase SDK v10.12.2 ES modules configuration
│   ├── main.js                 # Navigation, accordion, smooth scroll, sticky quick bar
│   └── quote-form.js           # Form validation & Firestore lead document submission
├── scripts/
│   └── serve.cjs               # Zero-dependency local Node.js preview server
├── firebase.json               # Firebase Hosting & Firestore deployment rules
├── firestore.rules             # Lockdown security rules for public write-only leads
└── firestore.indexes.json      # Firestore indexes configuration
```

### PLACEHOLDERS
The following placeholders are defined and must be replaced before live production deployment:
1. `daylon@bccomputers.co.za` — Flagged in brief as unverified contact email (in `index.html`).
2. `YOUR_FIREBASE_API_KEY` — Web App API key in `js/firebase-config.js`.
3. `YOUR_PROJECT_ID` — Firebase project ID in `js/firebase-config.js` and `firebase.json`.
4. `YOUR_MESSAGING_SENDER_ID` — Firebase messaging sender ID in `js/firebase-config.js`.
5. `YOUR_FIREBASE_APP_ID` — Firebase App ID in `js/firebase-config.js`.
6. `G-YOUR_MEASUREMENT_ID` — Optional Google Analytics 4 measurement ID in `js/firebase-config.js`.

### Running Locally
To preview the website locally without any npm dependencies:
```bash
node scripts/serve.cjs
```
Then visit: `http://localhost:3000`

### Deploying to Firebase
When ready to deploy (Hard Gate — requires human approval):
```bash
firebase login
firebase use <your-firebase-project-id>
firebase deploy
```

