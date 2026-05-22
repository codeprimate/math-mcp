# Feature: Directory + Dispatcher Discovery Pattern

## Problem Statement

The MCP server currently exposes 28 tools via `list_tools`, each with large parameter schemas. This creates a wall-of-text payload at connection time that:

- Forces the agent to scan all 28 tool descriptions before acting
- Sends the full schema for every tool on every connection, regardless of what the agent needs
- Grows the payload further with each new tool added
- Provides no structured way to navigate by capability domain

The goal is a **minimal `list_tools` payload** with **full schema richness deferred to on-demand discovery** — analogous to UNIX `ls` (enumerate) and `man` (document), with a dispatcher as the execution entry point.

---

## Requirements

### Functional Requirements

- `list_tools` returns exactly **4 tools**: `math_ls`, `math_man`, `math`, `math_batch`
- `math_ls()` with no arguments returns a top-level **hint** (short instruction for next discovery step), (1) the list of capability categories with their tool arrays, and (2) a full flat listing of all tools with `name` and `intent` only
- `math_ls(category)` returns a top-level **hint** and **full descriptors** for every tool in that category: for each tool, `name`, `description`, and `inputSchema` (same shape as `math_man` per tool). One call gives the agent everything needed to invoke any tool in the category without calling `math_man`
- `math_man(tool)` returns the **full descriptor** for the named tool: `name`, `description`, and `inputSchema` (same shape as each tool in `math_ls(category)`). Only valid for internal (CATALOG) tools, not the 4 meta-tools themselves
- `math(tool, arguments)` dispatches execution to any internal math tool by name
- `math_batch(calls)` dispatches multiple tools in one request (parallel execution); replaces current `batch_tools`
- All 28 (→ 26 internal after consolidation) tool implementations remain fully functional and unchanged in behavior
- Existing unit tests for tool functions continue to pass without modification

### Consolidations bundled with this change

| Action | Tools | Reason |
|---|---|---|
| Remove | `simplify_fraction` | Functionally identical to `simplify`; `simplify('6/8')` already returns `3/4` |
| Rename | `plot_bar_chart` → `plot_bar` | Remove redundant suffix; consistent with `plot_*` family |
| Rename | `plot_pie_chart` → `plot_pie` | Same |
| Rename | `batch_tools` → `math_batch` | Consistent `math_*` prefix for all public MCP tools; becomes one of the 4 public tools, not an internal tool |

Final internal tool count: **26 tools** across 7 categories.

### Category taxonomy

| Category | Tools |
|---|---|
| `algebra` | `simplify`, `solve`, `factor`, `expand` |
| `calculus` | `derivative`, `integral` |
| `numbers` | `evaluate`, `to_fraction`, `convert_unit`, `find_root` |
| `stats` | `describe_data`, `ttest`, `correlation`, `linear_regression`, `moving_average` |
| `ode` | `solve_ode`, `plot_ode_solution` |
| `charts` | `plot_timeseries`, `plot_bar`, `plot_histogram`, `plot_scatter`, `plot_heatmap`, `plot_stacked_bar`, `plot_stackplot`, `plot_pie` |
| `output` | `latex` |

### `math_ls` response shapes

```json
// math_ls() — no args: categories + full flat directory (one call = complete discovery)
{
  "hint": "Match a tool from 'tools' to your task. For one tool's parameters use math_man(name). For all tools in a category use math_ls(category). Then call math(name, arguments) to run.",
  "categories": [
    { "id": "algebra",  "tools": ["simplify", "solve", "factor", "expand"] },
    { "id": "calculus",  "tools": ["derivative", "integral"] },
    { "id": "numbers",   "tools": ["evaluate", "to_fraction", "convert_unit", "find_root"] },
    { "id": "stats",     "tools": ["describe_data", "ttest", "correlation", "linear_regression", "moving_average"] },
    { "id": "ode",       "tools": ["solve_ode", "plot_ode_solution"] },
    { "id": "charts",    "tools": ["plot_timeseries", "plot_bar", "plot_histogram", "plot_scatter", "plot_heatmap", "plot_stacked_bar", "plot_stackplot", "plot_pie"] },
    { "id": "output",    "tools": ["latex"] }
  ],
  "tools": [
    { "name": "simplify", "intent": "Simplify or reduce a symbolic expression." },
    { "name": "solve", "intent": "Solve an equation for a variable; all exact solutions." },
    { "name": "ttest", "intent": "Compare means; A/B testing and before/after analysis." },
    { "name": "plot_timeseries", "intent": "Line chart of one or more series over time or sequence." }
  ]
}
```
Note: `tools` above is the full set of 26 entries (one per internal tool). Agent can match the user task to one entry, then call `math_man(name)` for schema and `math(name, arguments)` to run. Alternatively, call `math_ls(category)` to get full descriptors for the whole category and skip `math_man`.

```json
// math_ls("stats") — with category: full descriptors (name, description, inputSchema) for every tool in the category
{
  "hint": "Call math(name, arguments) to run any tool listed above.",
  "category": "stats",
  "tools": [
    {
      "name": "describe_data",
      "description": "Compute comprehensive descriptive statistics for a dataset.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "data": { "type": "array", "items": { "type": "number" }, "description": "Array of numeric values to analyze." }
        },
        "required": ["data"]
      }
    },
    {
      "name": "ttest",
      "description": "Perform t-test for comparing means (one-sample or two-sample).",
      "inputSchema": {
        "type": "object",
        "properties": {
          "sample1": { "type": "array", "items": { "type": "number" }, "description": "First sample data." },
          "sample2": { "type": ["array", "null"], "items": { "type": "number" }, "description": "Optional second sample for two-sample t-test." },
          "alternative": { "type": "string", "default": "two-sided", "description": "Alternative hypothesis." }
        },
        "required": ["sample1"]
      }
    }
  ]
}
```
Each element of `tools` has the same shape as a single `math_man(tool)` response. The array contains all tools in the category (e.g. for stats: describe_data, ttest, correlation, linear_regression, moving_average). Implementation: for each tool name in CATALOG[category], call `app._tool_manager.get_tool(name)` and serialize name, description, parameters (inputSchema).

### `math_man` response shape

`math_man` returns a **full descriptor** for the requested tool: the same structure as each element of `math_ls(category).tools` (name, description, inputSchema).

```json
// math_man("ttest")
{
  "name": "ttest",
  "description": "Perform t-test for comparing means (one-sample or two-sample).",
  "inputSchema": {
    "type": "object",
    "properties": {
      "sample1": { "type": "array", "items": { "type": "number" }, "description": "..." },
      "sample2": { "type": ["array", "null"], "items": { "type": "number" }, "description": "..." },
      "alternative": { "type": "string", "default": "two-sided", "description": "..." }
    },
    "required": ["sample1"]
  }
}
```

`math_man` is scoped to internal (CATALOG) tools only. Calling it with a meta-tool name (`math_ls`, `math_man`, `math`, `math_batch`) returns the same unknown-tool error — those tools are already fully described in `list_tools`.

The `inputSchema` is retrieved via a live synchronous lookup: `app._tool_manager.get_tool(name)` returns `None` for unknown names, which maps to the error response.

### `math` dispatcher behavior

- Python function name: `tool_math` (avoids shadowing the `math` stdlib module)
- MCP registered name: `math`
- Accepts `tool` (str) and `arguments` (`dict[str, Any] | None`, default `None`; normalized to `{}` internally)
- Dispatches via `app.call_tool(tool, arguments)` — works because all internal tools remain registered with FastMCP even though hidden from `list_tools`
- **Plot URL handling**: after dispatching to a plot tool, the dispatcher checks `tool in PLOT_TOOL_NAMES` and if true calls `plot_output.maybe_save_plot_output(content, context)`, then appends the URL as a text content item. This is the same pattern used by `_run_one_tool` in `batch_tools.py`. `_attach_plot_url_handler` is **not** modified.
- Returns the result from the dispatched tool (with URL appended for plot tools)
- On unknown tool name: returns a JSON error string `{"error": "Unknown tool: <name>. Call math_ls() to browse available tools."}`

### Meta-tool MCP description strings

These are the strings that appear in `list_tools` — the agent's first point of contact. **Discovery instructions live here** so the agent sees next steps when choosing tools; the in-response `hint` is secondary.

| Tool | Description |
|---|---|
| `math_ls` | `"List available math tools. Call with no args to get categories and a flat list of all tools (name, intent). Then: use math_man(name) for one tool's parameters, or math_ls(category) for full descriptors (name, description, inputSchema) for every tool in that category. Finally call math(name, arguments) to run."` |
| `math_man` | `"Return the full descriptor (name, description, inputSchema) for a named math tool. Use after math_ls() to get parameters for a chosen tool, then call math(name, arguments) to run."` |
| `math` | `"Execute a math tool by name. Discovery: call math_ls() first to get tool names and intents; get parameters via math_man(name) or math_ls(category); then call math(name, arguments) with the chosen tool name and its arguments."` |
| `math_batch` | `"Execute multiple math tools in one request; results returned in call order. Each call: {name, arguments}. Use tool names from math_ls()."` |

### Technical Constraints

- No change to any tool function implementation (all `tool_*` functions in `sympy_tools.py`, `stats_tools.py`, etc. are untouched)
- No change to the transport layer, HTTP endpoints, or session management
- No change to `_attach_plot_url_handler` — plot URL logic for `math` dispatcher is handled inside `tool_math` itself
- All existing tests for tool functions must continue to pass without modification
- `math_batch` reuses the existing `batch_tools` implementation; only the registered MCP name changes
- The internal tools remain registered with FastMCP so `app.call_tool()` continues to work for dispatch

### Edge Cases & Error Handling

- `math_ls(category)` with unknown category: returns `{"error": "Unknown category: <name>", "available": ["algebra", "calculus", ...]}`
- `math_man(tool)` with unknown tool name or meta-tool name: returns `{"error": "Unknown tool: <name>. Call math_ls() to browse available tools."}`
- `math(tool, arguments)` with unknown tool: returns `{"error": "Unknown tool: <name>. Call math_ls() to browse available tools."}`
- `math(tool, arguments)` where arguments are wrong type/missing required: error propagates from the underlying tool (consistent with current behavior)
- `math_batch` with empty calls list: returns `[]` (consistent with current `batch_tools` behavior)

---

## Technical Approach

### Implementation Strategy

The key insight: **all 26 internal tools remain registered with FastMCP** (`app.call_tool` continues to work), but the `list_tools` response is overridden to return only the 4 meta-tools.

FastMCP does not natively support hidden tools. The `list_tools` override is done by intercepting the `ListToolsRequest` handler at the MCP protocol level — the same pattern already used in `_attach_plot_url_handler` for `CallToolRequest`.

Plot URL handling for the `math` dispatcher: `app.call_tool` bypasses the MCP request handler layer, so `_attach_plot_url_handler` never fires for inner dispatched calls. The `tool_math` function handles this directly by checking `tool in PLOT_TOOL_NAMES` after calling `app.call_tool`, then calling `plot_output.maybe_save_plot_output`. This mirrors `_run_one_tool` in `batch_tools.py`, which already uses the same pattern.

### Affected Components

| File | Change |
|---|---|
| `src/math_mcp/server.py` | Add `_override_list_tools_handler(app)` to filter `list_tools` to meta-tools only; update tool registration block to call `register_meta_tools` last |
| `src/math_mcp/meta_tools.py` | **New file.** `CATALOG` dict (categories + intent phrases). `tool_math_ls`, `tool_math_man`, `tool_math` implementations. `register_meta_tools(mcp, app)` function. `tool_math` handles plot URL post-processing internally. |
| `src/math_mcp/sympy_tools.py` | Remove `tool_simplify_fraction` function and its `mcp.tool` registration |
| `src/math_mcp/plotting_tools.py` | Rename registered tool names: `plot_bar_chart` → `plot_bar`, `plot_pie_chart` → `plot_pie` in `register_plotting_tools` |
| `src/math_mcp/batch_tools.py` | Change registered MCP name from `"batch_tools"` to `"math_batch"` in `register_batch_tools` |
| `src/math_mcp/plot_output.py` | Update `PLOT_TOOL_NAMES` set: replace `"plot_bar_chart"` with `"plot_bar"`, `"plot_pie_chart"` with `"plot_pie"` |
| `tests/test_server.py` | Remove `tool_simplify_fraction` import (line 20) and `TestSimplifyFraction` class (lines 127–138). **Preserve** `TestSimplify.test_simplify_fraction` (line 34) — it tests `tool_simplify`, not `tool_simplify_fraction`. |
| `tests/test_server_green_path.py` | Update tool count/name assertions for new registration state |
| `tests/test_batch_tools.py` | Update references to `"batch_tools"` tool name → `"math_batch"` |
| `tests/test_meta_tools.py` | **New file.** Tests for `math_ls`, `math_man`, `tool_math` dispatcher |

### Category and Intent Catalog Location

A static `CATALOG` dict lives in `meta_tools.py`. It is the single source of truth for:
- Category → tool membership (id, ordered tool list)
- Tool name → one-line intent phrase

Both `math_ls` and `math_man` read from `CATALOG`. Adding a new tool is a one-line change to `CATALOG`. The flat `tools` array in `math_ls()` is derived from `CATALOG` (one entry per tool with name and intent; category is already in `categories`).

### Schema Introspection for `math_man`

`math_man` uses a live synchronous lookup: `app._tool_manager.get_tool(name)` returns the internal `Tool` object (`.name`, `.description`, `.parameters`) or `None` if the name is unknown. No pre-caching needed — `get_tool` is a dict lookup. If the name is not in `CATALOG`, return the unknown-tool error before calling `get_tool`.

### Dependencies & Integration

- No new external dependencies
- `meta_tools.py` receives the FastMCP `app` reference at registration time (same pattern as `batch_tools.create_batch_tool(app)`)
- `meta_tools.py` imports `plot_output.PLOT_TOOL_NAMES` and `plot_output.maybe_save_plot_output` for plot URL handling inside `tool_math`

---

## Acceptance Criteria

- [ ] `list_tools` returns exactly 4 tools: `math_ls`, `math_man`, `math`, `math_batch`
- [ ] `math_ls()` returns a top-level `hint`, all 7 categories (each with `tools` array), and a top-level `tools` array of all 26 tools with `name` and `intent` only
- [ ] `math_ls("stats")` returns a top-level `hint` and all 5 stat tools with full descriptors: each has `name`, `description`, and `inputSchema` (same shape as `math_man` per tool)
- [ ] `math_ls("unknown")` returns an error with `available` list of valid category ids
- [ ] `math_man("ttest")` returns the full descriptor: `name`, `description`, and `inputSchema` (same shape as one tool in `math_ls(category).tools`)
- [ ] `math_man("math_ls")` returns unknown-tool error (meta-tools excluded from CATALOG)
- [ ] `math_man("unknown")` returns a descriptive error
- [ ] `math("simplify", {"expression": "x + x"})` returns `"2*x"`
- [ ] `math("plot_bar", {...})` returns an image and a URL text item (plot URL saving works)
- [ ] `math("unknown_tool", {})` returns a descriptive error
- [ ] `math_batch` executes parallel calls and returns results in call order
- [ ] `simplify_fraction` is removed; `simplify("6/8")` returns `"3/4"` (already true)
- [ ] All existing `tool_*` unit tests pass unmodified
- [ ] Ruff lint passes
- [ ] Pytest passes

---

## Implementation Tasks

- [ ] Create `src/math_mcp/meta_tools.py` with `CATALOG`, `tool_math_ls`, `tool_math_man`, `tool_math`, `register_meta_tools(mcp, app)`
- [ ] Add `_override_list_tools_handler(app)` to `server.py`; call after all tools are registered
- [ ] Remove `tool_simplify_fraction` function and registration from `sympy_tools.py`
- [ ] Rename `plot_bar_chart` → `plot_bar` and `plot_pie_chart` → `plot_pie` in `plotting_tools.py` registration
- [ ] Update `PLOT_TOOL_NAMES` in `plot_output.py` for renamed plot tools
- [ ] Rename registered MCP name in `batch_tools.py` from `"batch_tools"` → `"math_batch"`
- [ ] Update `server.py` registration block: call `register_meta_tools(mcp, mcp)` last
- [ ] Create `tests/test_meta_tools.py` with unit tests for all meta-tools
- [ ] Update `tests/test_server.py`: remove `tool_simplify_fraction` import and `TestSimplifyFraction` class; preserve `TestSimplify.test_simplify_fraction`
- [ ] Update `tests/test_server_green_path.py`: update tool count/name assertions
- [ ] Update `tests/test_batch_tools.py`: `"batch_tools"` → `"math_batch"`
- [ ] Run full test suite and lint; fix any failures
- [ ] Update README tool table to reflect new interface

---

## Risk Assessment

### Potential Issues

- **Breaking change for direct tool callers.** Any client currently calling `ttest`, `plot_timeseries`, etc. directly will get a "tool not found" error. For AI agent clients (the primary consumers), this is not a concern — they re-discover tools per connection. For scripted integrations or test harnesses calling tools by name directly, those need updating.

- **Plot URL handling for `math` dispatcher.** `app.call_tool` bypasses the MCP request handler layer, so `_attach_plot_url_handler` does not fire for inner calls made by `tool_math`. Handled by `tool_math` itself using `plot_output.maybe_save_plot_output` directly — the same pattern as `_run_one_tool` in `batch_tools.py`. `math_batch` is unaffected (already uses this pattern).

- **FastMCP internal API for schema lookup.** `app._tool_manager.get_tool(name)` is a semi-public API. If FastMCP renames or removes it, `math_man` breaks. **Mitigation:** isolate in a single helper function in `meta_tools.py`; easy to update in one place. Pin FastMCP version.

- **`list_tools` override coupling.** Overriding `ListToolsRequest` at the protocol level ties implementation to FastMCP/MCP SDK internals. **Mitigation:** isolate in `_override_list_tools_handler` in `server.py` with a clear comment; easy to update if the SDK changes.

### Mitigation Strategies

- Test `math("plot_bar", {...})` end-to-end in HTTP mode to confirm plot URL saving works before merging
- Add a smoke test to `test_meta_tools.py` asserting `list_tools` returns exactly `{"math_ls", "math_man", "math", "math_batch"}`
- Pin FastMCP version in `pyproject.toml` if not already pinned

### Investigation Results

**1. FastMCP schema introspection API — confirmed.**

- **`app._tool_manager.get_tool(name)`** — synchronous dict lookup, returns `mcp.server.fastmcp.tools.base.Tool` with `.name`, `.description`, and `.parameters` (the inputSchema dict). Returns `None` for unknown names. This is the chosen approach for `math_man`.
- **`await app.list_tools()`** — async alternative, returns `list[mcp.types.Tool]` with `.inputSchema`. Same data, confirmed identity-equal. Not used (sync preferred).

No pre-caching needed. No try/except needed — `None` return is the explicit unknown-name signal.

**2. `ListToolsRequest` handler override — confirmed, pattern identical to `CallToolRequest`.**

`app._mcp_server.request_handlers` contains a `ListToolsRequest` key. The override pattern is:

```python
original_handler = app._mcp_server.request_handlers[types.ListToolsRequest]

async def filtered_handler(req: types.ListToolsRequest):
    result = await original_handler(req)
    filtered_tools = [t for t in result.root.tools if t.name in META_TOOL_NAMES]
    updated = result.root.model_copy(update={"tools": filtered_tools})
    return result.model_copy(update={"root": updated})

app._mcp_server.request_handlers[types.ListToolsRequest] = filtered_handler
```

`result.root` is a `ListToolsResult` (Pydantic model). `model_copy(update=...)` produces a new instance without mutating the original. Hidden internal tools remain fully callable via `app.call_tool(name, args)` — confirmed experimentally.

No conflicts with `_attach_plot_url_handler` — they override different handler keys.
