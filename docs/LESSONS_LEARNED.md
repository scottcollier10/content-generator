# Lessons Learned: HubSpot Content Generator

**Date:** February 2026  
**Duration:** ~4 hours  
**Status:** Complete ✅

---

## The Challenge

Build a system that generates brand-aware emails using AI and works with **any client's existing HubSpot template** — not just a custom template we control.

This is the difference between:
- **Demo:** "Cool proof-of-concept with our special template"
- **Product:** "Works with your existing templates, no redesign needed"

---

## Major Bugs Encountered & Fixed

### Bug 1: Template HTML Structure Mismatch

HubSpot's `rich_text` widget strips full HTML documents (`<!DOCTYPE>`, `<html>`, `<body>` tags), leaving nothing visible. The fix: send HTML fragments instead.

```python
# WRONG
body_html = f"<!DOCTYPE html><html><body>{content}</body></html>"

# RIGHT
body_html = f"<p>{content}</p>"  # fragments only
```

### Bug 2: Only First Variation Getting Content

This was the subtle one. When running this as an n8n workflow, Code nodes run **once** with all items — unlike HTTP Request nodes which run **per item**. Using `.first()` in a Code node always grabbed index 0, so all three clones got patched with variation 1's content.

```javascript
// WRONG — always returns item 0, regardless of how many items exist
const variation = $('Split Into Items').first().json;

// RIGHT — loop and match by index
const items = $input.all();
const variations = $('Split Into Items').all();
for (let i = 0; i < items.length; i++) {
  const variation = variations[i].json;
  // ...
}
```

This is a fundamental n8n pattern: always use `$input.all()` and loop in Code nodes.

---

## Design Decisions That Worked

**Clone → Read → Patch:** Rather than recreating the client's template from scratch, we clone it, read back the widget structure, and inject only the body content. The client's footer, colors, and unsubscribe links are preserved automatically.

**Dynamic widget discovery:** Instead of hardcoding a widget ID, we probe for `hs_email_body` first (classic templates), then fall back to scanning for `@hubspot/rich_text` widgets (DnD templates), skipping any that contain "unsubscribe" or "footer".

**Brand file categorization:** Instead of dumping all files into the prompt as one blob, we categorize by filename into four structured sections (voice, positioning, audience, examples). Claude gets structured context rather than a wall of text.

---

## Multi-Model Debugging

Building used Sonnet throughout. When hitting a subtle data flow bug (the `.first()` issue), switching to Opus identified the root cause in minutes. The right mental model:

- **Sonnet** — building, iteration, explanation, documentation
- **Opus** — architecture review, subtle bugs, "why isn't this working?"

Cost-wise, Opus costs more per token. But solving a 2-hour debugging spiral in 2 minutes is a clear win.

---

## What Would've Saved Time

Understanding n8n's execution model earlier would have prevented the `.first()` bug entirely. The key rule: HTTP Request nodes process items individually; Code nodes run once with all items and must loop explicitly.

Testing with multiple template types sooner would have caught the widget discovery edge cases before they became blocking issues.

---

## Patterns for Future Projects

**n8n Code Node template:**
```javascript
const items = $input.all();
const relatedItems = $('OtherNode').all();
const results = [];

for (let i = 0; i < items.length; i++) {
  results.push({
    json: { /* process items[i] and relatedItems[i] */ }
  });
}

return results;
```

**HubSpot email workflow:**
```
Clone template → GET to read structure → PATCH to update content
(never send flexAreas in PATCH — causes API errors)
```
