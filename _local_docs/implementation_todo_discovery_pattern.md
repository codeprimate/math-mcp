# Implementation TODO: Directory + Dispatcher Discovery Pattern

## Specification Reference
**Source Document**: [_local_docs/spec_discovery_pattern.md](spec_discovery_pattern.md)
*This specification document must be loaded alongside this plan during execution to provide complete context and requirements.*

## Overview
- **Complexity**: Moderate
- **Risk Level**: Medium (breaking change for direct tool callers; list_tools override couples to MCP SDK)
- **Key Dependencies**: FastMCP `app._tool_manager.get_tool`, `app.call_tool`, `request_handlers[ListToolsRequest]`, `plot_output.maybe_save_plot_output`
- **Estimated Effort**: 2–3 days
- **Specification Sections**: Problem Statement, Requirements (Functional, Consolidations, Category taxonomy, Response shapes, Dispatcher behavior, Meta-tool descriptions, Technical constraints, Edge cases), Technical Approach, Acceptance Criteria, Implementation Tasks, Risk Assessment

## Phase Strategy
Implementation is split into three phases. **Phase 1** performs consolidations and renames (remove simplify_fraction, rename plot tools and batch_tools, update PLOT_TOOL_NAMES and tests) so that the catalog and all call sites use the final tool names. **Phase 2** adds the meta-tools module and list_tools override so that `list_tools` returns only 4 tools and discovery/dispatch work end-to-end. **Phase 3** adds meta-tool tests, updates green-path assertions and shell scripts, and updates README so that acceptance criteria and documentation are complete. Each phase is independently testable; Phase 1 preserves all existing behavior except renames/removals; Phase 2 delivers the core feature; Phase 3 locks it down with tests and docs.

## Progress Indicators
- 📋 **Planned** - Not started
- 🔄 **In Progress** - Currently being worked on
- ✅ **Completed** - Successfully finished
- ❌ **Blocked/Failed** - Encountered issues or dependencies
- ⏸️ **Paused** - Temporarily suspended
- 🔍 **Under Review** - Completed but needs validation

*Progress indicators should be placed at the end of phase, task, and subtask headings with format: "- 📋 Planned"*

---

## Implementation Phases

## Phase 1: Consolidations and Renames - ✅ Completed
*Incremental Goal: Remove simplify_fraction, rename plot_bar_chart → plot_bar, plot_pie_chart → plot_pie, batch_tools → math_batch; update PLOT_TOOL_NAMES and all tests so the codebase uses the final 26 internal tool names and one batch meta-tool name.*

### Task 1.1: Remove simplify_fraction and update sympy_tools - ✅ Completed
*Spec Reference: Consolidations bundled with this change; Technical Approach – Affected Components*

- [x] 1.1.1 **Delete `tool_simplify_fraction` and its registration** - ✅ Completed
  - *Hint*: `register_sympy_tools` in `src/math_mcp/sympy_tools.py` (lines 335–346); remove the function (lines 305–332) and the `mcp.tool(name="simplify_fraction")(tool_simplify_fraction)` line.
  - *Consider*: `simplify("6/8")` already returns `3/4`; no replacement registration needed.
  - *Files*: `src/math_mcp/sympy_tools.py`
  - *Risk*: Callers of `simplify_fraction` must switch to `simplify`; doc/README updated in Phase 3.
  - **IMPLEMENTATION PLAN**:
    - **Remove function and registration**:
      - Delete the entire `tool_simplify_fraction` function (signature through `return str(result)` / error return).
      - In `register_sympy_tools`, remove the line `mcp.tool(name="simplify_fraction")(tool_simplify_fraction)`.
    - **Testing Strategy**:
      - **Code Quality**: `ruff check --fix src/math_mcp/sympy_tools.py`
      - **Unit Testing**: Keep `TestSimplify.test_simplify_fraction` in `tests/test_server.py` (tests `tool_simplify`, not the removed tool). Remove `tool_simplify_fraction` import and the entire `TestSimplifyFraction` class.
      - **Test Cases**: Run `PYTHONPATH=src pytest tests/test_server.py -v`; confirm TestSimplify passes, TestSimplifyFraction is gone.
      - **Coverage**: No new code paths; removal only.

### Task 1.2: Rename plot tools and update PLOT_TOOL_NAMES - ✅ Completed
*Spec Reference: Consolidations – Rename plot_bar_chart → plot_bar, plot_pie_chart → plot_pie; Category taxonomy (charts); Technical Approach – plot_output.py*

- [x] 1.2.1 **Rename registered MCP names in plotting_tools.py** - ✅ Completed
  - *Hint*: `register_plotting_tools` in `src/math_mcp/plotting_tools.py`: `mcp.tool(name="plot_bar_chart")(...)` → `mcp.tool(name="plot_bar")(...)`, `mcp.tool(name="plot_pie_chart")(...)` → `mcp.tool(name="plot_pie")(...)`. Function names `tool_plot_bar_chart` / `tool_plot_pie_chart` can remain for code clarity or be renamed for consistency; spec requires only the registered MCP name change.
  - *Files*: `src/math_mcp/plotting_tools.py`
  - *Risk*: Any client calling `plot_bar_chart` or `plot_pie_chart` by name will break; acceptable per spec.
  - **IMPLEMENTATION PLAN**:
    - In `register_plotting_tools`, change `name="plot_bar_chart"` to `name="plot_bar"` and `name="plot_pie_chart"` to `name="plot_pie"`.
    - **Testing Strategy**: Run plotting tests if present; run full pytest after Phase 1.
  - [x] 1.2.2 **Update PLOT_TOOL_NAMES in plot_output.py** - ✅ Completed
    - *Hint*: `src/math_mcp/plot_output.py` lines 25–35: set `PLOT_TOOL_NAMES` to use `"plot_bar"` and `"plot_pie"` instead of `"plot_bar_chart"` and `"plot_pie_chart"`.
    - *Files*: `src/math_mcp/plot_output.py`
    - *Risk*: Plot URL saving would miss these tools if not updated.
    - **Testing Strategy**: After Phase 2, `math("plot_bar", {...})` acceptance test verifies URL handling.

### Task 1.3: Rename batch_tools → math_batch - ✅ Completed
*Spec Reference: Consolidations – Rename batch_tools → math_batch; Technical Approach – batch_tools.py*

- [x] 1.3.1 **Register batch tool as math_batch in batch_tools.py** - ✅ Completed
  - *Hint*: `register_batch_tools` in `src/math_mcp/batch_tools.py`: change `name="batch_tools"` to `name="math_batch"` in `mcp_app.tool(...)`.
  - *Consider*: Description string can mention "math_batch" for consistency.
  - *Files*: `src/math_mcp/batch_tools.py`
  - *Risk*: Scripts or tests that call the tool by name must use `math_batch`; shell scripts updated in Phase 3.
  - **IMPLEMENTATION PLAN**:
    - In `register_batch_tools`, set `name="math_batch"` in the `mcp_app.tool(name=..., description=...)(handler)` call.
    - **Testing Strategy**:
      - **Unit Testing**: `tests/test_batch_tools.py` uses `create_batch_tool(mcp)` and calls the handler directly; no change to tool name in tests unless a test explicitly invokes by MCP name. If any test or docstring references the string `"batch_tools"` as the public tool name, update to `"math_batch"`.
      - **Integration**: After Phase 2, `math_batch` is one of the 4 list_tools; smoke test in test_meta_tools verifies.

### Task 1.4: Update tests for Phase 1 changes - ✅ Completed
*Spec Reference: Affected Components – tests/test_server.py, tests/test_batch_tools.py*

- [x] 1.4.1 **Update test_server.py: remove simplify_fraction import and TestSimplifyFraction** - ✅ Completed
  - *Hint*: Remove `tool_simplify_fraction` from imports (line 20). Delete the entire `TestSimplifyFraction` class (lines 126–138). Do not remove `TestSimplify.test_simplify_fraction` (line 34) which tests `tool_simplify`.
  - *Files*: `tests/test_server.py`
  - **Testing Strategy**: `PYTHONPATH=src pytest tests/test_server.py -v`
  - [x] 1.4.2 **Update test_batch_tools.py if any MCP name assertions exist** - ✅ Completed
  - *Hint*: Grep for `"batch_tools"` in tests; update to `"math_batch"` only where the registered MCP tool name is asserted or used.
  - *Files*: `tests/test_batch_tools.py`
  - **Testing Strategy**: `PYTHONPATH=src pytest tests/test_batch_tools.py -v`

### Phase 1 Validation - ✅ Completed
- **Acceptance Criteria**: (1) No `simplify_fraction` in codebase except README/docs. (2) Plot tools registered as `plot_bar`, `plot_pie`. (3) Batch tool registered as `math_batch`. (4) PLOT_TOOL_NAMES contains `plot_bar`, `plot_pie`. (5) All existing tool function tests pass; ruff passes.
- **Testing Strategy**: `ruff check --fix src/ tests/`; `PYTHONPATH=src pytest tests/ -v` (excluding any meta_tools tests until Phase 2).
- **Rollback Plan**: Revert commits for Phase 1; re-add `tool_simplify_fraction` and registration; revert renames in plotting_tools, plot_output, batch_tools, test_server.

---

## Phase 2: Meta-Tools Module and list_tools Override - ✅ Completed
*Incremental Goal: list_tools returns exactly 4 tools (math_ls, math_man, math, math_batch); math_ls/math_man provide discovery; math dispatches to internal tools with plot URL handling; math_batch remains as registered in Phase 1.*

### Task 2.1: Create meta_tools.py with CATALOG and discovery/execution - ✅ Completed
*Spec Reference: Requirements (math_ls, math_man, math, math_batch); Category taxonomy; math_ls/math_man response shapes; math dispatcher behavior; Meta-tool MCP description strings; Technical Approach – meta_tools.py; Schema introspection; Dependencies*

- [x] 2.1.1 **Add CATALOG and META_TOOL_NAMES** - ✅ Completed
  - *Hint*: Single source of truth: dict mapping category id → list of tool names; and a flat mapping of tool name → one-line intent. Include all 7 categories and 26 tools per spec table. Define `META_TOOL_NAMES = {"math_ls", "math_man", "math", "math_batch"}` for the list_tools filter.
  - *Files*: `src/math_mcp/meta_tools.py` (new file)
  - *Risk*: Typo in tool name or category id breaks discovery; validate against actual registered tools in tests.
  - **IMPLEMENTATION PLAN**:
    - **CATALOG structure**: e.g. `CATALOG: dict[str, list[str]]` for category id → tool names (ordered). Add a separate structure or derive intent phrases (e.g. dict tool_name → intent) per spec “Tool name → one-line intent phrase”.
    - **Testing Strategy**: Unit tests in test_meta_tools.py will assert category count (7), total tool count (26), and that all names match registered tools.
  - [x] 2.1.2 **Implement tool_math_ls (no args and with category)** - ✅ Completed
  - *Hint*: No args: return `hint`, `categories` (each `{id, tools}`), and `tools` (flat list of `{name, intent}`). With category: return `hint`, `category`, and `tools` (full descriptors: name, description, inputSchema) by calling `app._tool_manager.get_tool(name)` for each tool in that category. Unknown category: return error with `available` list.
  - *Consider*: Use same hint strings as spec. For full descriptors, get Tool’s `.name`, `.description`, `.parameters` (inputSchema).
  - *Files*: `src/math_mcp/meta_tools.py`
  - **IMPLEMENTATION PLAN**:
    - **math_ls()**: Build categories from CATALOG; build flat tools from CATALOG with name + intent. Return JSON-serializable dict.
    - **math_ls(category)**: If category not in CATALOG, return `{"error": "Unknown category: <name>", "available": list(CATALOG.keys())}`. Else for each tool in CATALOG[category], call `app._tool_manager.get_tool(name)` and serialize name, description, parameters (inputSchema). Return hint + category + tools list.
    - **Testing Strategy**: Unit tests: math_ls() has 7 categories and 26 tools with name/intent; math_ls("stats") has 5 tools with name, description, inputSchema; math_ls("unknown") returns error and available list.
  - [x] 2.1.3 **Implement tool_math_man(tool)** - ✅ Completed
  - *Hint*: If tool not in CATALOG (or in META_TOOL_NAMES), return `{"error": "Unknown tool: <name>. Call math_ls() to browse available tools."}`. Else `app._tool_manager.get_tool(name)`; if None, same error. Else return dict with name, description, inputSchema (same shape as one entry in math_ls(category).tools).
  - *Files*: `src/math_mcp/meta_tools.py`
  - **Testing Strategy**: math_man("ttest") returns full descriptor; math_man("math_ls") and math_man("unknown") return error.
  - [x] 2.1.4 **Implement tool_math (dispatcher) with plot URL handling** - ✅ Completed
  - *Hint*: Accept `tool` (str) and `arguments` (dict | None, default None). Normalize arguments to `{}`. If tool not in CATALOG, return `{"error": "Unknown tool: <name>. Call math_ls() to browse available tools."}`. Else call `app.call_tool(tool, arguments)`. If tool in PLOT_TOOL_NAMES, call `plot_output.maybe_save_plot_output(content, app.get_context())` and append URL text content (same pattern as _run_one_tool in batch_tools.py). Return result (with URL appended for plot tools). Python function name: `tool_math` (avoid shadowing `math` module); MCP registered name: `math`.
  - *Consider*: Handle async: `app.call_tool` is async; meta tool handlers may need to be async or run in event loop. Check FastMCP tool signature (sync vs async).
  - *Files*: `src/math_mcp/meta_tools.py`; import `plot_output.PLOT_TOOL_NAMES`, `plot_output.maybe_save_plot_output`
  - *Risk*: Plot URL handling must run after dispatch; _attach_plot_url_handler does not fire for inner call_tool.
  - **IMPLEMENTATION PLAN**:
    - **Dispatcher**: Validate tool in CATALOG; await app.call_tool(tool, arguments); convert result to content list; if tool in PLOT_TOOL_NAMES, call maybe_save_plot_output and append URL; return content (or JSON string for tool result format consistency).
    - **Testing Strategy**: Unit test math("simplify", {"expression": "x + x"}) returns "2*x"; test math("unknown_tool", {}) returns error; integration test math("plot_bar", {...}) returns image + URL (Phase 3 or manual).
  - [x] 2.1.5 **Implement register_meta_tools(mcp, app)** - ✅ Completed
  - *Hint*: Register the 4 tools with MCP descriptions from spec table. Pass `app` (FastMCP instance) into the handlers so they can call `app._tool_manager.get_tool` and `app.call_tool` and `app.get_context`. Register after all other tools so internal tools are present for get_tool/call_tool.
  - *Files*: `src/math_mcp/meta_tools.py`
  - **Testing Strategy**: After server.py wiring, list_tools returns exactly 4 tools; names are math_ls, math_man, math, math_batch.

### Task 2.2: Add list_tools override and register meta tools in server.py - ✅ Completed
*Spec Reference: Technical Approach – list_tools override; Affected Components – server.py*

- [x] 2.2.1 **Implement _override_list_tools_handler(app)** - ✅ Completed
  - *Hint*: Same pattern as _attach_plot_url_handler but for `types.ListToolsRequest`. Get `original_handler = app._mcp_server.request_handlers.get(types.ListToolsRequest)`. Async handler: call `result = await original_handler(req)`, filter `result.root.tools` to tools whose `name` is in META_TOOL_NAMES, then `updated = result.root.model_copy(update={"tools": filtered_tools})`, return `result.model_copy(update={"root": updated})`. Confirm result.root type (ListToolsResult) and that model_copy is available.
  - *Consider*: Spec snippet uses `result.root` and `model_copy`; verify MCP SDK types in environment.
  - *Files*: `src/math_mcp/server.py`
  - *Risk*: SDK change to ListToolsResult or request_handlers could break; isolate in one function with comment.
  - **IMPLEMENTATION PLAN**:
    - **Override**: Store original handler; replace with async handler that invokes original, filters tools by META_TOOL_NAMES, returns new result with filtered tools. Do not mutate result in place; use model_copy.
    - **Testing Strategy**: test_meta_tools smoke test: call list_tools (or equivalent) and assert set of tool names == {"math_ls", "math_man", "math", "math_batch"}.
  - [x] 2.2.2 **Call _override_list_tools_handler and register_meta_tools in server.py** - ✅ Completed
  - *Hint*: Import meta_tools. After all tool registration (sympy, unit, scipy, stats, plotting, _attach_plot_url_handler, batch_tools), call `meta_tools.register_meta_tools(mcp, mcp)` then `meta_tools._override_list_tools_handler(mcp)` (or pass mcp as app). Order: override after registration so list_tools sees only meta tools.
  - *Files*: `src/math_mcp/server.py`
  - **Testing Strategy**: Full server startup; list_tools returns 4 tools; math_ls() and math_man("ttest") and math("simplify", {...}) work.

### Phase 2 Validation - ✅ Completed
- **Acceptance Criteria**: list_tools returns exactly 4 tools. math_ls() returns hint, 7 categories, 26 tools (name + intent). math_ls("stats") returns 5 tools with full descriptors. math_ls("unknown") returns error + available. math_man("ttest") returns full descriptor; math_man("math_ls") returns error. math("simplify", {"expression": "x + x"}) returns "2*x". math("unknown_tool", {}) returns error. math_batch executes and returns results in order.
- **Testing Strategy**: Unit tests in test_meta_tools.py; manual or scripted list_tools + math_ls + math_man + math + math_batch. Optional: HTTP test for math("plot_bar", {...}) to confirm URL.
- **Rollback Plan**: Revert server.py and remove meta_tools.py; restore list_tools to default; Phase 1 state remains.

---

## Phase 3: Tests, Scripts, and Documentation - ✅ Completed
*Incremental Goal: Full test coverage for meta-tools, green-path assertion for list_tools count, shell scripts and README updated for new interface.*

### Task 3.1: Create tests/test_meta_tools.py - ✅ Completed
*Spec Reference: Affected Components – tests/test_meta_tools.py; Acceptance Criteria; Risk – smoke test*

- [x] 3.1.1 **Add smoke test: list_tools returns exactly 4 meta-tools** - ✅ Completed
  - *Hint*: Use MCP client or server’s list_tools handler; assert set of tool names == {"math_ls", "math_man", "math", "math_batch"}.
  - *Files*: `tests/test_meta_tools.py`
  - **IMPLEMENTATION PLAN**:
    - Obtain list of tools from mcp (e.g. await mcp._mcp_server.request_handlers[types.ListToolsRequest](...) or via list_tools if exposed). Assert len(tools) == 4 and set(t.name for t in tools) == META_TOOL_NAMES.
    - **Testing Strategy**: pytest test_meta_tools.py
  - [x] 3.1.2 **Add unit tests for math_ls (no args, with category, unknown category)** - ✅ Completed
  - *Hint*: Call tool_math_ls() and tool_math_ls("stats"), tool_math_ls("unknown"); assert structure and contents per spec.
  - *Testing Strategy*: Assert hint present; categories length 7; tools length 26; stats tools 5 with name, description, inputSchema; unknown returns error and available.
  - [x] 3.1.3 **Add unit tests for math_man (valid tool, meta-tool name, unknown)** - ✅ Completed
  - [x] 3.1.4 **Add unit tests for tool_math (simplify, unknown tool; optional plot_bar with mock)** - ✅ Completed
  - [x] 3.1.5 **Add test for math_batch via dispatcher or direct handler** - ✅ Completed
  - *Consider*: Reuse existing batch logic; assert math_batch is one of the 4 tools and can be invoked (e.g. via math("math_batch", {"calls": [...]}) or direct registration).

### Task 3.2: Update test_server_green_path and shell scripts - ✅ Completed
*Spec Reference: Acceptance Criteria; Breaking change for direct tool callers*

- [x] 3.2.1 **Update test_server_green_path.py if tool count/names are asserted** - ✅ Completed (no assertions found; list_tools test in test_meta_tools)
  - *Files*: `tests/test_server_green_path.py`
  - [x] 3.2.2 **Update tests/test-batch-http.sh and tests/test-plot-http.sh** - ✅ Completed
  - *Hint*: Scripts that call `batch_tools` or `plot_bar_chart` by name will break. Update to call `math_batch` and `math("plot_bar", {...})` (or equivalent) so integration scripts pass. See README and script contents for exact payloads.
  - *Files*: `tests/test-batch-http.sh`, `tests/test-plot-http.sh`
  - *Risk*: Shell script changes depend on how MCP HTTP is invoked (params name vs nested math call).

### Task 3.3: Update README and docs - ✅ Completed
*Spec Reference: Implementation Tasks – Update README tool table*

- [x] 3.3.1 **Update README tool table and usage examples** - ✅ Completed
  - *Hint*: README.md lists tools (e.g. simplify_fraction, plot_bar_chart, plot_pie_chart, batch_tools). Replace with the new interface: list_tools returns math_ls, math_man, math, math_batch; document discovery flow (math_ls → math_man or math_ls(category) → math(name, arguments)); document math_batch; remove simplify_fraction from table; rename plot_bar_chart/plot_pie_chart to plot_bar/plot_pie in internal/catalog references; update example commands that call tools by name.
  - *Files*: `README.md`, `docs/math-mcp.mdc` if present
  - **Testing Strategy**: Read-through; ensure no stale references to old tool names in user-facing docs.

### Phase 3 Validation - ✅ Completed
- **Acceptance Criteria**: All acceptance criteria from spec satisfied; ruff and pytest pass; README reflects 4-tool interface and discovery flow; shell scripts run successfully.
- **Testing Strategy**: `ruff check --fix src/ tests/`; `PYTHONPATH=src pytest tests/ -v`; run `./tests/test-batch-http.sh` and `./tests/test-plot-http.sh` if applicable.
- **Rollback Plan**: Revert doc and script changes; Phase 2 remains functional.

---

## Critical Considerations
- **Performance**: list_tools response is minimal (4 tools); math_ls() builds response from CATALOG + get_tool (sync, fast). No new external dependencies.
- **Security**: No new attack surface; tool names and categories are fixed. Error messages expose available categories/tools (intended for discovery).
- **Scalability**: Catalog is static; adding a tool is a one-line CATALOG update.
- **Monitoring**: Log plot save failures as today; no new logging required.
- **Cross-Phase Dependencies**: Phase 2 depends on Phase 1 (correct tool names in CATALOG and PLOT_TOOL_NAMES). Phase 3 depends on Phase 2 (meta_tools and list_tools override in place).

## Research & Validation Completed
- **Dependencies Verified**: FastMCP `_tool_manager.get_tool(name)` and `request_handlers[ListToolsRequest]` pattern confirmed in spec “Investigation Results”. No new pip dependencies.
- **Patterns Identified**: _attach_plot_url_handler in server.py as template for list_tools override; _run_one_tool in batch_tools.py as template for plot URL handling inside tool_math.
- **Assumptions Validated**: (1) Internal tools remain registered and callable via app.call_tool. (2) list_tools override does not affect call_tool. (3) math_man uses sync get_tool; tool_math may need async bridge if FastMCP tools are async.

---

## Sanity Check Summary (Post-Write)

- **Phase-by-phase**: Phase 1 delivers renames/consolidations and is independently testable; Phase 2 delivers 4-tool list_tools and discovery/dispatch; Phase 3 delivers tests, scripts, and docs. Goals are measurable.
- **Inter-phase**: Phase 2 depends on Phase 1 (final tool names in CATALOG and PLOT_TOOL_NAMES). Phase 3 depends on Phase 2. No circular dependencies.
- **Task-level**: Each task has spec section reference; subtasks are ordered; testing is embedded in each task.
- **Specification coverage**: All spec acceptance criteria and implementation tasks map to phases/tasks (list_tools 4 tools, math_ls no-arg/category/error, math_man valid/meta/unknown, math dispatcher + plot URL, math_batch, simplify_fraction removal, renames, errors, README).
- **Feasibility**: File paths and patterns (server.py handler override, batch_tools _run_one_tool) match the codebase. Risks documented; phases are scoped for 1–2 days each.
