<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

## Local UI verification

- Demo mode command: `npm run dev -- -p 3100` (always use port **3100**).
- Before a UI run, remove `frontend/.next`, stop stale Next processes, then start exactly one server at `http://127.0.0.1:3100`.
- Never claim a UI task is complete without a passing Playwright check against the live server and saved screenshots.
