// Code of the "Fetch window" node (Run Once for All Items). tools/build_workflows.py
// pastes this file into the node, so edit it here and rebuild rather than editing in n8n.
// Works out how far back this run looks: 3 hours 5 minutes (the timer period plus a
// 5-minute overlap). If the previous timed run was longer ago than that, because the
// laptop was off, it looks back to 5 minutes before that run instead, but never more
// than 24 hours. Set CATCH_UP to false for a strict 3 h 5 min window every time.
const WINDOW_MIN = 185;
const OVERLAP_MIN = 5;
const MAX_MIN = 24 * 60;
const CATCH_UP = true;
const store = $getWorkflowStaticData('global');
const now = Date.now();
let since = now - WINDOW_MIN * 60000;
if (CATCH_UP && store.lastRun && store.lastRun - OVERLAP_MIN * 60000 < since) since = Math.max(store.lastRun - OVERLAP_MIN * 60000, now - MAX_MIN * 60000);
store.lastRun = now;
return [{ json: { after: Math.floor(since / 1000), sinceMs: since, since: new Date(since).toISOString() } }];
