# Publishing Plane

**Language / 语言:** English · [中文](../../architecture/publishing-plane.md)

## What it is

TelePress is a **Preview / Publishing Plane**:

```text
Input
  Content / MediaReference
        ↓
TelePress Publishing Plane
        ├─ Renderer
        ├─ Media Resolver
        │    ├─ Proxy
        │    └─ Upload
        └─ Telegraph Publisher
        ↓
Public Preview URL
```

Input may come from any source; the output is always a public Telegraph URL.

## What it is not

- Not a content discovery service
- Not a moderation / review system
- Not a scheduler
- Not a Telegram bot
- Does not hold upstream platform business state
- Does not hold Pixiv / DeviantArt or other source-account credentials

## Long-term invariants

- stateless-ish: no business database
- provider neutral: image hosts and upstreams are interchangeable
- source-platform neutral: no platform-specific core models
- structured failures: callers can attribute by stage / status
- backward compatible: new rich paths never break plain-text / multipart paths

## Telegraph page size

Render the complete Markdown once to preserve formatting across source boundaries.
A single pagination pass applies both the 20,000 text-character target and the
Telegraph client's compact UTF-8 JSON budget of 60 KiB, leaving room for navigation.
Do not paginate source chunks independently: this strands short overflow pages
in the middle of the document. The final page may be short; paragraph and
indivisible media boundaries may also leave space. Oversized bodies split at node boundaries;
oversized paragraphs retain formatting containers and all text. Indivisible
media attributes that exceed the budget fail explicitly. Navigation is checked
against the 64 KiB content limit and uses a compact page index when needed.

Reuse the existing MarkdownConverter and Telegraph Python client. The
[official createPage / editPage contract](https://telegra.ph/api) specifies a
64 KB content limit for both methods; the client uses ensure_ascii=False.

## Agent constraints

See [AGENTS.md](../../../AGENTS.md) for the repository-wide long-term constraints.
