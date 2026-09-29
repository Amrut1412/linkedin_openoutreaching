# Outreach Guide — communicate.so with OpenOutreach + LinkedIn DMs

> The complete playbook: what OpenOutreach is, how to set it up for Communicate
> (AI customer support agent), and how to run the LinkedIn DM layer on the same
> lead list.

---

## ⚠️ Read this first: OpenOutreach sends **email**, not LinkedIn DMs

OpenOutreach is deliberately **browserless, with no LinkedIn account and no
scraping** — zero platform-ToS surface, nothing to get banned. It will never log
into LinkedIn or type a DM for you.

What it does for your LinkedIn play is arguably more valuable: every lead it
exports carries **`linkedin_url` + `reason`** (why this person fits), and with
`--json` also **`profile_text`** (the raw profile text it qualified on).

So the real workflow is:

```
OpenOutreach  →  qualified leads with LinkedIn URLs + written reasons
                 ├── EMAIL goes out automatically (OpenOutreach send)
                 └── LinkedIn DMs go out on that same list, separately
                     (manual, or semi-automated with the linkedin-growth tooling)
```

Email is automated end-to-end. LinkedIn is a second touch on the same list.

---

## The flow, end to end

**You provide 4 things → it runs 6 steps.**

| # | You provide | Why |
|---|---|---|
| 1 | **Product description** (pages of markdown) | This *is* the ICP. The AI learns your target from this |
| 2 | **Target market** description | Where to hunt |
| 3 | **LLM API key** (OpenAI / Anthropic / OpenAI-compatible) | Qualification + email writing |
| 4 | **BetterContact API key** — free account = **40 verified emails, no card** | Powers discovery (free) + email finding (1 credit per verified hit) |
| 5 | **A mailbox + app password** | Where mail sends from (Google Workspace works out of the box; any other provider names its SMTP/IMAP host and port) |

Then:

```
Discover → Qualify → Confidence gate → Buy address → Write opener → Send
```

What matters about each step:

- **Discovery + qualification are free** (discovery uses the BetterContact Lead
  Finder, billed nothing; qualification costs only your own LLM key).
- **Only verified email lookups cost credits** — 1 credit per hit — and only for
  leads that already cleared the AI's fit gate. Your 40 free credits get spent
  on the *best* fits, not the first ones found.
- Every lead ships with a written `reason` you can read and disagree with.
  **Fixing your product/target description is how you fix the verdicts.**
- Sending has guards: a sending window, a daily cap and pacing between messages.

---

## Setup for communicate.so (≈30 minutes)

Communicate.so = AI support agent that answers from existing help docs and hands
off to a human mid-thread. That gives a razor-sharp ICP. Write two files:

### `product.md` (copy, then tune)

```markdown
# Communicate — AI customer support agent

Communicate is an AI customer support agent that trains on a company's own
help center, docs and past tickets. It answers repeat customer questions
instantly, in the company's voice, and hands off to a human inside the same
conversation thread when it is unsure — no hallucinated answers.

It embeds as a widget on the site and goes live in one day, with no
integration project. Operators can customize the agent's name, voice and
instructions, and see analytics on exactly where the agent struggles.
Pricing is credit-based with a $1 activation (includes 100 test credits).

Best fit: teams handling many repeatable customer questions that already
have answers documented in help articles, guides or past replies.
Poor fit: teams where every request is unique and needs human judgment.
```

### `target.md` (copy, then tune)

```markdown
# Target market

Heads of Support, CX Leads, Support Operations Managers, and founders at
SaaS and e-commerce companies (10–500 employees) that run a documented help
center and a shared support inbox (Zendesk, Intercom, Freshdesk, Crisp,
Tidio, Help Scout).

Strong signals:
- Actively hiring support agents (headcount cost pain)
- Publicly complaining about ticket volume, first-response time or deflection
- Running a help center / docs site with real content already

Weak signals:
- Enterprise teams with a custom-built internal AI
- Companies with no help documentation at all (Communicate trains on docs —
  without docs there is nothing to train on)
```

### Install + onboard

```bash
uv tool install openoutreach

openoutreach init --product-docs product.md --target target.md
```

The wizard asks for whatever is still missing (LLM key, BetterContact key,
your country, mailbox address + **app password** — not your login password).
The LLM key is verified at the prompt; the mailbox by a real SMTP login before
setup finishes. It stops **before spending anything**.

### First runs

```bash
openoutreach status            # confirm: onboarding complete, credit balance, next_action

openoutreach find 10           # FREE — 10 qualified leads as CSV on stdout, cannot spend
openoutreach find 10 emails    # the paid form — buys addresses for whatever cleared
                               # the gate (≤10 credits)
```

**Audit before you spend.** Read the `reason` column on the first 10 rows like
a buyer, not a seller. If the reasoning is off, your target file is off —
sharpen it and rerun (free). Only when the reasons read right do you spend
credits on emails.

### Export columns

```
email, first_name, last_name, company, title, website, linkedin_url, reason, lead_id, qualified_at
```

- Column names are the **importers'** — Instantly and Smartlead read the file
  without column mapping. Do not rename them.
- `reason` is prose (commas and quotes) — parse with a real CSV reader, never
  by splitting on `,`.
- `linkedin_url` is your DM worklist. `reason` is your personalization angle.
- **Turn on import dedupe** in whichever sequencer you import into (opt-in on
  Smartlead, undocumented on Instantly), or a re-exported lead gets contacted
  twice.

### Sending

```bash
openoutreach send              # one pass: mail whatever the guards allow right now
openoutreach send 5            # keep going until five conversations are open
openoutreach run 5             # find five leads carrying an address, then send (spends credits)
```

Or hand the CSV to Instantly/Smartlead/Lemlist and send from there.

**Consent rule (the repo enforces it too):** `find` is free work; `find …
emails`, `send` and `run` spend money or put mail in strangers' inboxes. Only
run them when sending is actually asked for.

---

## The LinkedIn DM layer — the playbook

### Route A — Manual DMs (do this for your first 40 leads)

Low volume, zero ban risk, highest reply rate. For each row in the CSV: open
`linkedin_url`, skim the profile, send a connection note. At 10–15/day this
takes ~15 minutes.

**Connection note (≤300 chars, no link, no demo ask):**

> Hi {first} — saw you run support at {company}. I spend my days with CX teams
> buried in repeat tickets (order status, "where's my refund" tier), so I
> follow a lot of support leads here. No pitch — just growing my CX circle.

**DM only after they accept.** First DM = one question, under 60 words, still
no link:

> Thanks for connecting, {first}! Quick one: is your team bot-free on purpose,
> or has nothing you've tried handled the repeat questions well? We built an AI
> agent that answers from a company's existing help docs and hands off to a
> human mid-thread — but I only recommend it where the docs already exist.
> How's {company} set up today?

**Angle selection from `reason`:** hiring signal → cost/headcount angle;
help-center-heavy → deflection angle; inbox tool in profile → migration angle.

### Route B — Semi-automated (scale to 100+/week)

The `linkedin-growth` pipeline (installed in this environment) imports leads
from a search URL, qualifies them against an ICP, and runs connection invites
per account with daily caps and stale-pending withdrawal. That is the sane
shape of LinkedIn automation.

The honest trade-off, said plainly:

- **Automating LinkedIn violates LinkedIn's User Agreement.** Accounts do get
  restricted. The variable is not the tool — it is the velocity and the age of
  the account.
- Rules that keep accounts alive:
  - Profile fully built + regular posting activity for 2–4 weeks **before** any
    outreach.
  - Never automate an account younger than ~30 days.
  - **10–15 invites/day max** (newer account = fewer).
  - DMs only to people who accepted.
  - No links in first touches.
  - Keep pending invites under ~100; withdraw stale ones.
  - Never point automation at a LinkedIn account you cannot afford to lose.

### The multichannel cadence (where email + LinkedIn compound)

| Day | Touch | Channel |
|---|---|---|
| 1 | Email #1 (OpenOutreach `send` writes it from your product docs) | Email |
| 2 | Connection note (personalized from `reason`) | LinkedIn |
| 4 | If accepted → the DM above | LinkedIn |
| 5 | Email #2, new angle | Email |
| 10 | Breakup email | Email |

Same person, two channels, each touch referencing a real, stated reason they
fit. A reply on **either** channel means they engaged — log it and drop the
other channel for that person.

---

## Suggested first week

| When | Action |
|---|---|
| **Today** | Write `product.md` + `target.md`, run `openoutreach init`, run free `find 10` |
| **Day 2–3** | Audit the `reason` column; fix `target.md` if the verdicts are off |
| **Day 3** | `openoutreach find 20 emails` — spends ≤20 of the 40 free credits, only once quality is proven |
| **Day 3–4** | LinkedIn Route A on those exact people: 10–15 connection notes/day |
| **Week 2** | If replies are coming: wire the CSV into `linkedin-growth` for invites at scale; let OpenOutreach `send` own the email lane |

---

---

## OpenOutFind — the finder, explained

OpenOutFind is the child package that does **discovery → qualification →
enrichment → export**. OpenOutreach installs it (and OpenOutSend) and puts one
wizard in front of both. Its identity in one sentence: **you don't bring a
list — you bring a description, and it returns people plus a written reason for
each.** It never sends anything. Its boundary is one-way: leads leave as CSV,
nothing comes back.

```
product.md + target.md
        │
        ▼
  ① DISCOVER    LLM turns your description into search keywords → pages
                profiles from BetterContact's licensed index   (free)
        ▼
  ② QUALIFY     an LLM judges each profile against your ICP and writes
                the `reason`; a small ML model learns from the verdicts
                                                               (your LLM key)
        ▼
  ③ GATE        a confidence gate rations who deserves a paid lookup
        ▼
  ④ RESOLVE     buy the work email — free sources first, then 1 credit
                per verified hit                               (the ONLY paid step)
        ▼
  ⑤ EXPORT      CSV in Instantly/Smartlead column names — done
```

### ① Discovery — a keyword walk, not a keyword guess

`product.md`/`target.md` go to an LLM, which emits opening search keywords.
Then the clever part: **discovery walks the keyword index by counting.** It adds
one word at a time to a query, watches the accepted-lead counts come back, and
spends its next query where the best leads came from — a frontier search over
the index.

The search axes are few and *measured* — each verified to actually steer
results against the live index, with a nonsense-word control:

| Axis | Rule | Why |
|---|---|---|
| `lead_job_title` | up to 2 words, AND-ed ("founder cto") | the measured best narrowing move (~9k results at near-perfect precision) |
| `lead_seniority` | exactly 1 closed value (`owner`, `founder`, `c_suite`, `vp`, `head`, `director`, `manager`…) | values match whole-only; two values query a person nobody has |
| `lead_location` | exactly 1 ("California, United States", not "California") | a state without its country returns 0 |

Three other axes (`industry`, `function`, `department`) were **removed** —
measured as inert or unreachable. That discipline is why the walk doesn't waste
queries. For communicate.so, this is why `target.md` wording matters:
*"Support Operations Manager"*, *"Head of Customer Experience"*, *founder* —
real `lead_job_title` tokens are what the walk builds from.

### ② Qualification — an LLM judge with a learning loop

Two layers:

1. **The LLM makes every verdict.** Each profile's firmographic text
   (`profile_text`) + your product docs + target go into a prompt; the agent
   returns structured `{qualified: bool, reason: str}`. The reason is
   first-class output, not a log line — it is the `reason` column in your CSV.
2. **A Gaussian Process learns from the verdicts.** Every profile is embedded
   (384-dim FastEmbed, cached on the Lead row). A GP regression fits over past
   verdicts and then decides **who to qualify next**: exploit profiles with the
   highest predicted fit probability, explore the ones where the model is most
   uncertain (BALD). Cold start is seeded with synthetic "ideal profile" rows,
   flagged `synthetic` and never exported.

Honesty note the README itself makes: **the learning loop is an experiment, not
a proven edge** — no claim it beats random picking yet. The part that *is*
load-bearing: the GP's predicted probability is the **spend gate** for step ④.

### ③④ The money path — one paid step, opt-in at every layer

The per-action engine is an ordered priority list — the first actionable row
wins, everything below waits:

```
1  check the email address we ordered   (poll an in-flight lookup — free)
2  rank the qualified leads             (GP scores the pool, promotes past the gate — free)
3  buy an email address                 (the ONLY money-spending row)
4  find & qualify new leads             (top up discovery — always runs)
```

The design rule that matters to your wallet: **spending is opt-in at every
layer.** Row 3 is skipped entirely unless the caller passed `--emails` / used
the `emails` unit — a bare `find 10` *cannot* spend a credit no matter how many
leads queue past the gate. Even inside row 3, free sources come first: an email
already on the lead, then the hub's cross-operator cache; the paid
BetterContact lookup is the last resort. What bounds total spend is the number
you typed — one credit = one verified address.

Each lead is a `Deal` with a state machine:

```
QUALIFIED → READY_TO_FIND_EMAIL → FINDING_EMAIL → RESOLVED ✓
                                       │
                                       ├── NO_EMAIL_FOUND   (terminal, costs nothing)
                                       └── FAILED           (terminal, costs nothing)
```

Terminal states rest for free — nothing re-iterates them. A run ends when the
goal is met or nothing can advance (`goal_unreached`), and it is fully
resumable. There is deliberately **no daemon, no scheduler** — that existed
once and was deleted.

### ⑤ CRM + export

Everything lands in SQLite (`~/.openoutfind/data`): `Lead` / `Company` /
`Deal` models browsable in Django Admin. Export is `find 0` or any run's
stdout — every lead in the store, newest file supersedes all. Rejected leads
and opt-outs **never** export; there is deliberately **no score column**
(confidence is a spend gate, not a quality signal — the `reason` is the quality
signal).

### Finder CLI + config

```bash
uvx --from openoutfind outfind check        # verify config, create DB, spend nothing
uvx --from openoutfind outfind find 10      # free qualified leads → CSV
uvx --from openoutfind outfind find 10 emails
uvx --from openoutfind outfind status [--json]
```

Flags that matter:

- `--emails` — permit spending (implied by the `emails` unit).
- `--exclude FILE` — LinkedIn URLs to skip; your suppression list lives here.
- `--debug` — the discovery walk's reasoning; use this if a run finds nothing.
- `--json` — JSON Lines with `profile_text` on stdout, run metadata on stderr.

Config is entirely `OPENOUTFIND_*` env variables — which is why OpenOutreach's
wizard exists: the children read env and remember nothing; the parent remembers
your answers.

### What this means for the communicate.so campaign

- **`find 10` (free) is the iteration loop.** Discovery + qualification cost
  nothing but LLM tokens. Wrong verdicts → edit `target.md` → rerun. Spend
  hours here before spending any credits.
- **The spend gate is your friend**: the 40 free BetterContact credits are
  offered only to leads the GP is confident about — not to marginal fits.
- **`--exclude` is your LinkedIn dedupe**: everyone already DM'd goes in that
  file, so a rerun never re-finds them.
- **`profile_text` (via `--json`) is your DM research**: the same text the
  judge read — what they do, seniority, company shape. Write the connection
  note from it.
- **The `emails` unit is the budget knob**: `find 20 emails` is capped at 20
  credits by construction.

---

## Command cheat sheet

```bash
# Setup / state
openoutreach status                    # config, counts, credits, next_action — never spends
openoutreach init --product-docs product.md --target target.md   # onboard, spends nothing

# Finding
openoutreach find 10                   # 10 MORE qualified leads — free, cannot spend
openoutreach find 10 emails            # ...carrying a verified address (≤10 credits)
openoutreach find 0                    # no work — re-print everything stored
openoutreach find 10 --json            # JSON Lines incl. profile_text (for automation)

# Sending (only when sending is asked for)
openoutreach send                      # one guard-paced pass
openoutreach send 5                    # until five conversations are open
openoutreach run 5                     # find (emails unit) + send in one pass — spends
```

Notes:

- `N` is how many **more**, not a total — reruns continue, never restart.
- Exit 0 = goal met. Any non-zero exit still prints its rows on stdout and says
  why it stopped on stderr — treat it as partial success with a stated reason.
- Everything lives in `~/.openoutreach`; stopping and starting loses nothing.
