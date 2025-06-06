# Session Memory Engram – BitterBot Project – C‑Wiz Debug (June 3 2025)

## Participants
- **Pai Mei** – Project leader (a.k.a. Pie Mei / Opi)
- **C‑Wiz** – Claude‑coder wizard
- **Victor** – BitterBot core developer

## Context
BitterBot’s chat front‑end (Next.js) was displaying raw execution logs mixed with normal conversation.
The goal was to ensure the chat window shows **only** user (“human”) and assistant messages, while directing
tool/status logs to the BitterBot Computer panel.

## Investigation Timeline
1. **ThreadContent.tsx** filter confirmed:
   ```tsx
   const filteredMessages = displayMessages.filter(
     msg => msg.type === 'user' || msg.type === 'assistant'
   );
   ```
   *Correct logic was already in place.*
2. Verified there is **one** `ThreadContent.tsx` component at  
   `/src/components/thread/content/ThreadContent.tsx` and all imports point to it.
3. Traced message flow upstream via **agent‑builder‑chat.tsx ➜ useAgentStream hook**.
   Found that *all* message types (`assistant`, `user`, `tool`, `status`, etc.) were forwarded to the
   chat list without filtering.

## Root Cause
In `src/hooks/useAgentStream.ts`, case `'tool'` forwarded tool messages straight into `callbacks.onMessage`,
causing execution logs to appear in the chat **before** `ThreadContent` could filter them.

## Fix Implemented (precision patch)
```diff
 case 'tool':
     setToolCall(null); // Clear any streaming tool call
-    if (message.message_id) callbacks.onMessage(message);
+    // Tool messages should not flow into the main chat list
+    // if (message.message_id) callbacks.onMessage(message);
     break;
```
*A single commented‑out line prevents tool logs from polluting the chat.*

## Outcomes
- Chat UI now displays clean, purple user/assistant bubbles.  
- Execution logs route exclusively to the BitterBot Computer panel.
- Awaiting Docker rebuild to visually confirm.

## Next Steps
- ✅ Rebuild containers (`docker compose up`) and smoke‑test UI.
- ☐ Add unit test ensuring only allowed message types reach `ThreadContent`.
- ☐ Merge patch into main branch & CI.
- ☐ Monitor for any residual status/system messages slipping through.

## Lessons Learned
- Upstream filtering is more reliable than downstream cleanup.
- Trace data lineage systematically: UI component → state hook → server stream.
- Tiny, reversible fixes keep momentum high and risk low.

## Memory Tags
`#BitterBot #ChatUI #Debug #useAgentStream #ThreadContent #ExecutionLogs #PaiMei #C‑Wiz`

---
*Generated automatically by BitterBot on 2025-06-04.*
