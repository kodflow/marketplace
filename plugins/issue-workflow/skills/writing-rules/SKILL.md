---
name: writing-rules
description: >-
  Conventions for writing GitLab issues under .drafts/: mandatory "Vue d'Ensemble" header
  and "Out of scope / Deferred" section, French narrative with proper accents, English
  section titles, technical jargon NEVER Frenchified (logger not journaliser), no
  em-dashes, no markdown file links (GitLab strips relative paths), concise code snippets
  (< 400 lines per issue), reference links for advanced concepts, pre-freeze scoping gate
  and plan-only dry run. Apply when drafting or reviewing issue files.
allowed-tools: Read, Grep, Glob
---

## Output Requirements (CRITICAL)

Before writing anything:

1. Inspect existing files under `.drafts/`
2. Infer and reuse:
   - Naming conventions
   - File structure
   - Headings
   - Labels
   - Sections (Context, Goal, Acceptance Criteria, etc.)
3. Follow the same patterns exactly

**Do not invent a new format.**

## Issue Structure

Every issue MUST start with a "Vue d'Ensemble" section that allows a developer to understand the essential information in 30-60 seconds, followed by the detailed sections.

```markdown
# Issue #XXX : [Titre]

## Vue d'Ensemble

**En bref :** [1-2 phrases décrivant ce qu'on fait et pourquoi c'est important]

**Critère de succès :** [Métrique mesurable concrète]

**Effort estimé :** X heures/jours | **Phase :** X | **Priorité :** Haute/Moyenne/Basse

**Dépendances :** Requiert #XXX, #YYY | Bloque #ZZZ (ou "None")

**Actions clés :**
- [ ] Action concrète 1
- [ ] Action concrète 2
- [ ] Action concrète 3

---

## Summary
## Improvements
## Risks
## Involved components
## Implementation
## Acceptance tests
## Out of scope / Deferred
```

Avant que l'issue ait un numéro réel (elle n'existe pas encore sur GitLab), `XXX` est un
repère local : soit le numéro du draft (voir « Reporté au draft NNN » ci-dessous), soit
`?` en attendant. La commande `post-issue` de ce plugin, au moment de publier, remplace ce
repère par le numéro réel renvoyé par GitLab.

### Out of scope / Deferred (MANDATORY)

Every issue carries this section — required by this skill, and by the project's own
scoping/Definition-of-Done docs if it has them (this skill does not presume their name;
`docs/development/00N-*.md` is a common Kodflow convention but not a hard requirement).

**Each line names its destination.** One of:

- `Reporté à #XXXX`, when a numbered issue owns it
- `Reporté au draft NNN`, when the target is drafted but unnumbered
- `À drafter`, when nothing owns it yet

A line with no destination is not a deferral, it is a verbal promise. Those are the ones that get lost, which is exactly why the section exists.

Two rules that follow from it:

- **Never write "on verra plus tard" or "hors périmètre" alone.** Say what is out, why, and who takes it.
- **Say what is broken, not just what is missing.** "Rules directory needs cleanup" hides a duplicate alert firing twice in production. A reviewer decides differently once they know.

Also state deferrals the issue creates knowingly. An issue that ships a known deviation from an ADR it depends on must say so here, or the deviation reads as an oversight to the next person.

## Language

- **Narrative in natural, conversational French**, as if explaining to a colleague
- **Always use proper French accentuated characters** (é, è, ê, à, ù, ç, etc.). Never strip accents. Example: "créer", "nécessaire", "réseau", not "creer", "necessaire", "reseau".
- Use "on" instead of impersonal forms: "On va créer..." not "Création de..."
- **Section titles in English** (Summary, Implementation, Risks, etc.)
- **Code and comments** in English
- **Mermaid diagrams** in English (for labels, conditions, etc.)

### NEVER Frenchify technical terms (CRITICAL)

Technical jargon stays as an **anglicisme**, in French prose, always. Translating it does not make the text more French, it makes it unsearchable and ambiguous: the reader has to translate back to know which concept is meant, and the translated form matches nothing in the code, the specs or the logs.

| Write this | NEVER this |
|---|---|
| logger, logging | journaliser, journalisation |
| wrappé, wrapper | enveloppé, encapsuleur |
| peer | pair, homologue |
| subscription | souscription, abonnement |
| aggregate (DDD) | agrégat |
| endpoint | point de terminaison |
| handler | gestionnaire |
| adapter | adaptateur |
| store | magasin, entrepôt |
| timeout | délai d'expiration |
| cache | antémémoire |
| label | étiquette |
| span | travée, portée |
| readiness, liveness | disponibilité, vivacité |
| load balancer | répartiteur de charge |
| heartbeat | battement de coeur |
| scrape | moissonnage |
| check | garde, garde-fou |
| fallback | repli |
| container | conteneur |
| user plane, control plane | plan utilisateur, plan de contrôle |
| binding | liant, liaison |

The list is illustrative, not exhaustive. The rule is general.

**`check`, not `garde`.** A "garde d'unicité" is a `checkInvariants` in the code. Naming it "garde" translates away a term the reader can grep for, and it is vaguer than what it describes.

**Conjugating and pluralising the anglicisme is correct and expected**: "le message est wrappé", "on gate la readiness", "les endpoints sont scrapés", "une requête mockée". Keeping the term does not mean keeping English grammar.

**When a term is genuinely ambiguous**, grep the existing docs under `docs/` and `.drafts/` and follow the majority usage. Do not invent a third form.

Two cautions on that count. Scope it to comparable prose: counting an English document or a Go identifier inflates the English side and settles nothing. And **when the counts are close, the jargon rule breaks the tie**, because a French word that also has an everyday meaning (`repli`, `garde`, `charge`) inflates its own side with occurrences that have nothing to do with the concept.

## Style

- Favor short, direct sentences
- Explain the "why" not just the "what"
- Avoid unnecessary jargon
- **Do NOT use long or double hyphens** (— or --). They are an obvious indicator of AI-generated text. Rephrase sentences to avoid them.
- **Do NOT use markdown links to reference source code files** (e.g., `[queue.go](libs/configuration/queue.go)`). GitLab does not handle relative paths properly in issue descriptions. Use simple backtick references instead: `` `libs/configuration/queue.go` ``
- **Add references for complex concepts**: When introducing an advanced technical concept (e.g., "coarse-grained time," "lock-free," "atomic operations"), include references to justify the benefit and avoid giving developers the impression that it came out of nowhere. Acceptable sources: official Go documentation, Medium articles, Reddit/StackOverflow posts, academic papers, recognized blog posts.

## Code in Issues (CRITICAL)

Issues are **guidelines for developers**, not source files. The goal is that a mid-level developer understands what to do and how to approach it, not that they copy-paste production-ready code.

**Rules:**

- **Show only the key snippet** that illustrates the approach or the tricky part (signatures, patterns, critical logic). Never write out the full implementation.
- **Prefer pseudocode or abbreviated code** for repetitive logic. Example: write `Reset()` for one struct and add "On applique la même logique sur XxxInfo, YyyInfo, etc.". Do NOT repeat the pattern for every struct.
- **Never include boilerplate**: if the pattern is standard Go (pool acquire/release, Prometheus counters, basic benchmark scaffolding), describe what to do instead of writing the full code.
- **Benchmarks in Acceptance tests**: describe what to benchmark and the expected results. A short example is OK; do NOT write 5+ benchmark functions in full.
- **Target: < 400 lines per issue.** If an issue exceeds this, it's a sign that too much code was inlined. Trim code blocks and replace with concise explanations.

**Examples:**

Instead of writing a full `Reset()` for every sub-struct:
```go
func (b *BillingInfo) Reset() {
    b.ID = ""
    b.SessionID = ""
    // ... reset all top-level fields ...

    // Reset each pre-allocated sub-struct
    if b.RcvRequest != nil { b.RcvRequest.Reset() }
    if b.Routing != nil    { b.Routing.Reset() }
    // Same pattern for SndRequest, RcvResponse, SndResponse,
    // Location, GTPCTunnel
}
```

Instead of writing 7 full benchmark functions:
> **Benchmarks attendus :**
> - `BenchmarkBuildBillingInfo_Current` vs `_WithPool` : mesurer la réduction d'allocs/op (objectif: -80%)
> - `BenchmarkTeidStringOrZero_Sprintf` vs `_Optimized` : valider le gain 2-3x
> - `BenchmarkBuildBillingInfo_Parallel` : vérifier l'absence de contention sous forte charge

## Before Freezing an Issue

Writing the issue is not the last step. Two passes come between the first draft and the frozen one, and skipping them is how scope surprises reach the middle of an implementation, where they can invalidate a design that is already written.

### 1. The scoping gate (three lenses)

Run this pre-plan gate — the project's own scoping checklist doc if it has one, otherwise these three lenses directly:

- **3GPP conformance** (only when the issue touches a 3GPP/telecom surface, and only if useful context is available — the `3gpp-expert` plugin's `3gpp-expert` skill, if installed): literal table walk of every message built or parsed, requests AND responses, presence conditions read rather than assumed, and the right reference point (an IE valid on one interface may be invalid on another).
- **Architecture, composition, lifecycle**: does the design hold at N peers, N replicas, N pods? Shared resources, startup and graceful shutdown, failure modes, timeout layering, return routing.
- **Cross-cutting**: metrics and spans against the project's metrics catalogue if it has one, idempotence and dedup, restart and persistence, PII masking, config keys and their defaults, store read-copy contract.

### 2. The plan-only dry run

Invoke the `implement-issue` skill (same plugin) on the draft with an explicit plan-only instruction: produce the step plan, stop before any edit, and list every inconsistency and open decision found.

The point is not to start implementing. It is that generating an implementation plan forces contact with the actual code, and that contact is what exposes claims the issue asserts but the repository contradicts, and decisions the issue leaves for whoever picks it up. **A decision left open in an issue is a decision made alone, inside a merge request, with no trace.**

Fold the findings back into the draft, then freeze. It is quick on documentation-only issues and it earns its cost on any issue touching existing code.

## Final Validation Checklist

Before completing:

- All files are valid Markdown
- Output matches existing `.drafts/` conventions
- Recommendations prioritize latency and throughput
- No suggestion contradicts Go performance best practices
- The output is directly usable in GitLab without manual edits
- **The "Vue d'Ensemble" section allows understanding the essential in 30-60 seconds**
- **Code blocks are concise: guidelines, not production-ready source**
- **Issue is under 400 lines**
- **Complex concepts have references** (Go docs, articles, StackOverflow, etc.)
- **No technical term has been Frenchified** (logger, not journaliser)
- **The "Out of scope / Deferred" section is present, and every line names a destination**
- **The three scoping lenses have been run**
- **The plan-only dry run has been run and its findings folded back in**

## Publier l'issue

Une fois le draft gelé, la commande `/issue-workflow:post-issue <chemin-du-draft>`
(ce plugin) le publie sur GitLab par `curl` — le serveur MCP `gitlab` est en lecture seule
chez Kodflow. Voir [`post-issue`](../../commands/post-issue.md).
