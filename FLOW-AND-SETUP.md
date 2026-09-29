# Flow & Setup — communicate.so outreach, complete picture

> Everything runs on your machine. Nothing was pushed anywhere. Last cross-checked:
> 2026-09-28 — all suites green, one wiring regression found and fixed (see §6).

---

## 1. What you have

```
E:\OpenOutreach\OpenOutFind   the FINDER  (local commits, unpushed):
                                · BetterContact key is now OPTIONAL — a keyless
                                  install qualifies leads it brings itself
                                · new verb: outfind import leads.csv
                                · pydantic-ai fix (glm-5.3 / z.ai works)
E:\OpenOutreach               the ORCHESTRATOR: wizard asks BetterContact as
                                optional (blank = skip discovery); its venv runs
                                the local finder checkout (see §6)
E:\OpenOutDM                  the LINKEDIN SENDER (new, working): LinkedIn search
                                → connect-with-note → DM after acceptance,
                                Playwright, guarded, free
~\.openoutreach\data\communicate.sqlite3   your communicate.so campaign
                                (10 qualified leads already inside)
E:\OpenOutreach\OUTREACH-GUIDE.md          the deep guide (ICP, cadence, templates)
E:\OpenOutDM\README.md                     the DM tool's own guide
```

**Both channels, one pipeline:**

```
LinkedIn search ──► outdm find ──► qualify ──► outdm send ──► outdm dm
      (free)          candidates      (you)      invites+notes   DMs on accept
      │
      └──► outfind import ──► find N ──► leads.csv ──► (email channel)
           (same people,     AI reason
            OpenOutFind)     per lead
```

---

## 2. One-time setup (most is already done)

| Step | State |
|---|---|
| OpenOutreach onboarded, communicate.so DB created | ✅ done |
| 10 free qualified leads in the DB | ✅ done |
| OpenOutDM venv + Chromium installed | ✅ done |
| **Mailbox: store the Google app password** | ⏳ **you — 2 min** (§5, Step 0) |
| **OpenOutDM: log in to LinkedIn once** | ⏳ **you — 3 min** (§3, Step 1) |

### The two pending steps, in full

**Step A — mailbox password** (unblocks email sending; your `.env` already holds it):

```powershell
cd E:\OpenOutreach
.venv\Scripts\python.exe store_mailbox_password.py      # reads .env, writes both DBs, prints nothing
$env:OPENOUTFIND_ACCEPT_LEGAL_NOTICE = "true"
.venv\Scripts\python.exe manage.py --db "$env:USERPROFILE\.openoutreach\data\communicate.sqlite3" init --product-docs product.md --target target.md
# ends silently = mailbox verified. If it says auth rejected (534), the .env value is
# not an app password — create one at myaccount.google.com/apppasswords (2FA required).
```

**Step B — LinkedIn session** (the browser login):

```powershell
E:\OpenOutDM\.venv\Scripts\python.exe -m openoutdm setup
# a Chrome window opens → log in to LinkedIn in it → press Enter in the terminal.
# The tool never sees your credentials. Session persists in ~\.outdm\chrome-profile.
```

---

## 3. The flow you run (PowerShell)

### Shorthand for every terminal session

```powershell
# Every NEW PowerShell window needs these three lines first:
$env:Path += ";E:\OpenOutDM\.venv\Scripts"       # makes `outdm` a command
$env:OPENOUTFIND_ACCEPT_LEGAL_NOTICE = "true"    # the finder asks for this every run
cd E:\OpenOutreach
# ($oo/$odb are no longer used as strings — see the email channel below)
```

### The LinkedIn DM channel (daily)

```powershell
# 1. FIND — describe the ICP as a LinkedIn search (free, reads only)
outdm find 25 --title "Head of Support" --location "United States"

# 2. QUALIFY — automatic: the LLM judges every lead against your product
outdm qualify --llm --product-docs E:\OpenOutreach\product.md --target-docs E:\OpenOutreach\target.md
#    (or review by hand: outdm qualify, or pick ids: outdm qualify --ids 4,9,11)

# 3. PREVIEW — see every note before anything is clicked (no, really: nothing clicks)
outdm send --dry-run

# 4. INVITE — guarded: ≤15/day, ≥20 min apart (jittered), 09:00–18:00 local only
outdm send --limit 10

#    Note quota exhausted (LinkedIn caps personalized invites monthly)?
#    Fall back to bare connection requests — the DM carries the pitch after acceptance:
outdm send --bare --limit 10

# 5. DM — checks who accepted; DMs them (run each morning)
outdm dm

# 6. HOUSEKEEPING — withdraw invites pending > 14 days (weekly is fine)
outdm withdraw

# any time
outdm status
```

**Your own words:** create `E:\OpenOutDM\note.txt` / `message.txt` with
`{first_name}` `{name}` `{title}` `{company}` merge fields, then:

```powershell
outdm send --limit 10 --note-file E:\OpenOutDM\note.txt
outdm dm --message-file E:\OpenOutDM\message.txt
```

Good defaults are already built in (tuned for communicate.so) — the files are optional.

### The email channel (no BetterContact, when you want it)

```powershell
# One path, three commands — run from E:\OpenOutreach:
$py = ".venv\Scripts\python.exe"; $db = "$env:USERPROFILE\.openoutreach\data\communicate.sqlite3"

# Bring leads in — your existing CSVs import as-is (linkedin_url, name, title, company…)
& $py manage.py --db $db import E:\OpenOutreach\data\leads-india-hq-5.csv

# The AI judges every imported lead and writes the reason each fits (your LLM key only)
& $py manage.py --db $db find 10

# Export — columns are Instantly/Smartlead-ready
& $py manage.py --db $db find 0 > leads.csv
```

Never run `find … emails` (buys addresses) or `openoutreach send` (mails people)
unless that spend/send is exactly what you decided in that moment.

---

## 4. Rules of the road

1. **Week one: ≤10 invites/day.** The guard defaults (15/day · 20 min · 09–18h) are
   ceilings, not targets. Warm the profile with normal human activity first.
2. **Kill switch:** a LinkedIn checkpoint stops the whole run with a screenshot in
   `~\.outdm\screenshots\`. Clear it by hand in the browser window, then re-run.
   Nothing is ever clicked past a challenge.
3. **First live run is selector shakedown.** LinkedIn's HTML drifts. If `find`
   reads 0 rows or `send` misses a button, the printed screenshot shows what changed —
   the selectors to adjust live in `openoutdm\search.py` and `openoutdm\actors.py`.
4. **DMs only after acceptance** — the tool enforces this structurally (the `dm`
   verb only touches leads LinkedIn itself marked connected).
5. **Env overrides for the pace** (optional): `OUTDM_DAILY_INVITE_LIMIT`,
   `OUTDM_MIN_INTERVAL_MINUTES`, `OUTDM_ACTIVE_START_HOUR`, `OUTDM_ACTIVE_END_HOUR`,
   `OUTDM_DAILY_DM_LIMIT`, `OUTDM_WITHDRAW_AFTER_DAYS`, `OUTDM_HOME`.

---

## 5. State & what is intentionally NOT done

| Item | State |
|---|---|
| All test suites | ✅ OpenOutFind 591 pass (2 pre-existing Windows-only failures on clean main too) · OpenOutreach 28 pass |
| Git | 🔒 **local only, per your instruction** — `OpenOutFind` has 2 unpushed commits (`44bd939`, `779be04`); push was denied (no write access to `eracle/*`) |
| BetterContact | ⛔ not needed anywhere in this flow; only unlocks licensed discovery + paid email lookups if ever wanted |
| Not yet built | LLM-drafted notes/DMs in OpenOutDM (templates today) · multi-account · scheduler |
| Pending on you | §2 Step A (mailbox) · §2 Step B (LinkedIn login) |

## 6. The one regression the cross-check caught (fixed)

An earlier stray `pip install` reinstalled stock `openoutfind 0.1.22` over the local
checkout wiring, which silently removed the `import` verb. Repaired by reinstalling
`pip install -e E:/OpenOutreach/OpenOutFind --no-deps`. **If `manage.py import` ever
says "Unknown command", that reinstall is the one-line fix.**
