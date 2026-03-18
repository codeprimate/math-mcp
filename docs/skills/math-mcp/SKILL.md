---
name: math-mcp
description: Mathematical computations and word problems, statistical analysis, data visualization, charting, and quantitative data processing tasks. Use when the user requests mathematical calculations, statistical analysis, data visualization, charting, or quantitative data processing.
---

# Math MCP Usage

## Tool Interface (4 tools)

The server exposes **4 tools** via `list_tools`. All math operations go through them.

| Tool | Purpose |
|------|---------|
| **math_ls** | List tools. No args: categories + flat list (name, intent). With `category`: full descriptors (name, description, inputSchema) for that category. |
| **math_man** | Full descriptor for one internal tool. Call `math_man(name)` to get parameters. |
| **math** | Run one internal tool: `math(name, arguments)`. Use names from `math_ls()`. |
| **math_batch** | Run multiple internal tools in one request. Pass `calls`: list of `{name, arguments}` (max 64); results in same order. |

**Discovery flow:** Call `math_ls()` to see all 26 internal tools and categories. Use `math_man(name)` for one tool’s parameters, or `math_ls(category)` for a full category. **Category ids** (use with `math_ls(category)`): `algebra`, `calculus`, `numbers`, `stats`, `ode`, `charts`, `output`. Then call `math(name, arguments)` to run (or `math_batch` for multiple independent calls).

## Problem Classification Guide

**CRITICAL: Users phrase questions as word problems, not mathematical expressions. Interpret the underlying mathematical question.**

**Classify problems into three types (internal tool names; call via `math(name, arguments)`):**

### Statistical Problems
**Indicators:** Questions about distributions, comparisons, averages, percentiles, significance, variability
**Tools:** `describe_data`, `ttest`, `plot_histogram`, `plot_bar`, `moving_average`

### Linear/Regression Problems
**Indicators:** Questions about relationships, correlations, trends, predictions, forecasting
**Tools:** `correlation`, `linear_regression`, `plot_scatter`, `plot_timeseries`

### Symbolic/Algebraic Problems
**Indicators:** Questions about equations, expressions, derivatives, integrals, symbolic manipulation
**Tools:** `solve`, `simplify`, `expand`, `factor`, `derivative`, `integral`, `evaluate`

**For complex problems:** Break into sub-problems, classify each, chain appropriate tools.

## Data Preparation

**MANDATORY - Execute BEFORE any MCP analysis:**

1. **Create timestamped analysis folder + DuckDB database** in project tmp: `{project_root}/tmp/{YYYYMMDD}_{HHMMSS}/`
2. **Use jq** for JSON extraction and reshaping from MCP/API responses
3. **Use DuckDB** as the central data store — load all intermediate data as named tables
4. **Use DuckDB SQL** for aggregation, filtering, and joining — no language-specific scripts
5. **Export CSV/JSON from DuckDB** for Math MCP consumption
6. **Follow data pipeline:** raw source → jq → DuckDB table → SQL → CSV export → Math MCP

For complete data preparation protocol, DuckDB patterns, jq transforms, MCP artifacts pattern, and CLI examples, see [references/data-preparation.md](references/data-preparation.md).

## Analysis Workflow

**NEVER submit all data or perform complex multi-step analysis in a single MCP call.**

Follow discrete step pattern:
1. **Initial Exploration** - Use `describe_data` for summary statistics
2. **Visual Understanding** - Choose ONE appropriate plot based on data type
3. **Targeted Analysis** - Perform ONE specific analysis based on visual patterns
4. **Additional Visualization** - Create final visualization if needed

**Key principles:**
- ONE tool call per step - wait for results before proceeding
- ONE question per step - don't combine multiple analyses
- ONE variable comparison at a time
- Sample large datasets - use DuckDB SAMPLE before exporting
- Use DuckDB SQL for aggregation - not Math MCP

For complete step-by-step analysis protocol, data size management, multi-variable analysis, and complex problem decomposition, see [references/analysis-workflow.md](references/analysis-workflow.md).

## Visualization

**CRITICAL: Design for perception, not preference. Every visualization choice should optimize for accurate, efficient transfer of quantitative understanding.**

**Chart output:** Chart tools (e.g. `math(plot_timeseries, {...})`, `math(plot_bar, {...})`) return a URL. Download the chart with `curl` and save it to `$ANALYSIS_DIR/charts/<descriptive_name>.png` so it is stored with the analysis session.

**Quick reference (internal tool names; call via `math(name, arguments)`):**
- **Time-series** → `plot_timeseries`
- **Categorical comparison** → `plot_bar` (horizontal preferred)
- **Distribution** → `plot_histogram`
- **Correlation (2 vars)** → `plot_scatter`
- **Ranking** → `plot_bar` (sorted by value)

**Critical design rules:**
- Position encodes quantity (most accurate)
- Start bar graphs at zero
- Order data meaningfully (never arbitrary)
- Minimize non-data ink
- Label directly when possible
- Never use pie charts or 3D effects
- **Never use long timestamp strings as labels** — format at DuckDB export time to match the chart's time granularity (e.g. `Jan 15`, `Feb 2026`, `14:00`)
- **Always indicate timezone** on charts with timestamps — use the abbreviation in the time axis label (e.g. `Time (PST)`) or append to the chart title

For complete visualization design principles, graph type selection, color usage rules, encoding hierarchy, and quality assessment checklist, see [references/visualization.md](references/visualization.md).

## Batched Requests

The server supports **batched requests** via the **math_batch** tool. The client runs multiple internal operations in one request.

- **Input:** `calls` — array of objects, each with `name` (internal tool name, required) and optional `arguments` (dict; omit or `{}` for no args).
- **Output:** Results returned in the same order as `calls`.
- **Limits:** At most 64 calls per request. Execution is parallel (concurrency limited by CPU count minus one).

**Use batching when:** Multiple operations are **independent** (no step depends on another’s result). Examples: `math_batch` with several `simplify`/`evaluate`/`factor`/`expand` calls, or multiple `math(name, arguments)` equivalents in one batch.

**Do not use batching when:** A step depends on a previous result (e.g. describe_data → choose plot → run ttest). Keep the analysis workflow sequential; use one `math(...)` call per step and wait for results before proceeding.

## Workflow Patterns

Chain internal tools via `math(name, arguments)` (or `math_batch` when independent):

- **Descriptive:** `describe_data` → `plot_histogram` or `plot_bar`
- **Relationships:** `correlation` or `linear_regression` → `plot_scatter`
- **Time Series:** `moving_average` → `plot_timeseries`
- **Testing:** `ttest` → `plot_bar`
- **ODEs:** `solve_ode` → `plot_ode_solution`

**All operations use `$ANALYSIS_DIR/analysis.duckdb` as the central data store; Math MCP receives CSV exports from DuckDB.**

## Tools Reference

**Discovery:** Call `math_ls()` for categories and tool names; `math_man(name)` or `math_ls(category)` for full parameters. Execute with `math(name, arguments)` or `math_batch` with `calls: [{name, arguments}, ...]`.

Chart tools support optional: `title`, `xlabel`, `ylabel`, `figsize` (width, height in px), `grid`, `xlim`/`ylim`, `output_format` ('png'|'svg'), and often `xlabel_rotation`, `legend_loc`, `colors`/`color`.

---

### 4-tool interface (exposed by list_tools)

| Tool | Parameters | Use cases |
|------|------------|-----------|
| **math_ls** | `category`? (string) | No args: categories + flat list (name, intent). With category: full descriptors for that category. |
| **math_man** | `tool` (string) | Full descriptor (name, description, inputSchema) for one internal tool. |
| **math** | `tool` (string), `arguments`? (object) | Run one internal tool by name with given arguments. |
| **math_batch** | `calls`: array of `{ name, arguments? }` (max 64) | Run multiple independent internal tools; results in same order; parallel execution. |

---

### Internal tools (26) — use with math(name, arguments) or math_batch

*For exact parameters, call `math_man(name)` or `math_ls(category)`.* Category ids: **algebra**, **calculus**, **numbers**, **stats**, **ode**, **charts**, **output**.

---

### algebra

| Tool | Parameters | Use cases |
|------|------------|-----------|
| **simplify** | `expression` (string) | Reduce expressions; verify identities; clean up trig/log; combine like terms. For fractions use expression e.g. `"6/8"`. |
| **solve** | `equation` (string, expr = 0), `variable` (string) | Find roots/zeros; solve for unknown; "solve for x" questions. Linear, quadratic, polynomial, many transcendental. |
| **factor** | `expression` (string) | Factor polynomials; simplify rationals; find roots by factoring; expanded → factored form. |
| **expand** | `expression` (string) | Multiply out parentheses; expand binomials; distribute; factored → standard polynomial form. |

---

### calculus

| Tool | Parameters | Use cases |
|------|------------|-----------|
| **derivative** | `expression`, `variable` | Slope/rate of change; critical points (derivative = 0); increasing/decreasing; partial derivatives. |
| **integral** | `expression`, `variable` | Antiderivatives; areas (combine with evaluate for definite); reverse of derivative. |

---

### numbers

| Tool | Parameters | Use cases |
|------|------------|-----------|
| **evaluate** | `expression` (string), `values`? (object, var → number) | Numeric evaluation; substitute variables; decimal approximations; check equality (evaluate difference). |
| **to_fraction** | `value` (string, decimal or numeric expr) | Decimal → exact rational; avoid float errors; repeating decimals. |
| **convert_unit** | `value` (number), `from_unit`, `to_unit` (e.g. 'meter', 'kilometer', 'celsius', 'fahrenheit') | Unit conversion within category: length, mass, time, temperature, volume, speed. |
| **find_root** | `function` (string, f(x)=0), `initial_guess`?, `bracket`? [a,b], `method`? ('newton'\|'bisection'\|'brentq'\|'secant') | Numerical root when symbolic solve fails or is slow; intersection points; critical points. |

---

### stats

| Tool | Parameters | Use cases |
|------|------------|-----------|
| **describe_data** | `data` (array of numbers) | Summary stats (mean, median, std, percentiles); performance metrics; distribution overview. |
| **ttest** | `sample1` (array), `sample2`? (array or null), `alternative`? ('two-sided'\|'greater'\|'less') | One- or two-sample t-test; A/B tests; before/after; significance of mean difference. |
| **correlation** | `x_data`, `y_data` (arrays, same length), `method`? ('pearson'\|'spearman'\|'kendall') | Linear or rank correlation; relationships between metrics; dependencies. |
| **linear_regression** | `x_data`, `y_data` (arrays) | Fit line; coefficients, R²; capacity/trend/growth forecasting; predict from trend. |
| **moving_average** | `data` (array), `window`? (int, default 7), `method`? ('simple'\|'exponential') | Smooth time series; reduce noise; trends vs spikes; cleaner dashboards. |

---

### ode

| Tool | Parameters | Use cases |
|------|------------|-----------|
| **solve_ode** | `equations` (list of "dx/dt = expr"), `initial_conditions` (object), `time_span` [t_start, t_end], `method`? ('rk45'\|'rk4'\|'euler') | Systems of ODEs; IVPs; physics/engineering simulations; dynamic models. |
| **plot_ode_solution** | `ode_result` (JSON string from solve_ode: `t` + variable arrays) | Visualize ODE solution; dynamical system behavior. |

---

### charts

| Tool | Parameters | Use cases |
|------|------------|-----------|
| **plot_timeseries** | `timestamps` (array of strings), `series` (object: name → array of values); optional `secondary_y`, `show_values`, `value_format`, `linestyles` | Data over time; multiple series; trends; temporal patterns. |
| **plot_bar** | `categories`, `values` (arrays); optional `horizontal`, `show_values`, `value_format` | Categorical comparison; rankings; discrete counts; prefer horizontal for long labels. |
| **plot_histogram** | `data` (array), `bins`? (default 30) | Distribution shape; frequency; outliers; spread. |
| **plot_scatter** | `x_data`, `y_data` (arrays); optional `labels` (point labels) | Correlation; paired measurements; clusters; relationships. |
| **plot_heatmap** | `data` (2D array of rows), `x_labels`?, `y_labels`?; optional `colormap` | Matrices; correlation/confusion matrices; intensity over two dimensions. |
| **plot_stacked_bar** | `categories`, `series` (object: name → array); optional `horizontal`, `show_values`, `show_segment_values`, `show_total`, `value_format` | Part-to-whole by category; component breakdown; use sparingly. |
| **plot_stackplot** | `x_data`, `series` (object); optional `baseline` ('zero'\|'sym'\|'wiggle'), `alpha` | Composition over continuous x (e.g. time); evolution of parts. |
| **plot_pie** | `labels`, `values`; optional `autopct`, `explode`, `startangle`, `shadow` | Proportional composition; **avoid when possible** — prefer plot_bar for accurate perception. |

---

### output

| Tool | Parameters | Use cases |
|------|------------|-----------|
| **latex** | `expression` (string) | Convert expression to LaTeX for docs, markdown, or typeset display. |

---

## Execution Guidelines

1. **Create timestamped analysis folder and DuckDB database:**
   ```bash
   ANALYSIS_DIR="{project_root}/tmp/$(date +%Y%m%d_%H%M%S)"
   mkdir -p "$ANALYSIS_DIR"
   DB="$ANALYSIS_DIR/analysis.duckdb"
   ```
2. **Interpret word problem** - Identify underlying mathematical question
3. **Classify problem type** - Statistical, linear/regression, or symbolic
4. **Extract raw data** - Save ALL raw outputs to `$ANALYSIS_DIR/`:
   - **MCP tools**: Save responses immediately to `$ANALYSIS_DIR/mcp_*.json`
   - **CLI tools (psql, curl)**: Save results to `$ANALYSIS_DIR/cli_*.csv` or `$ANALYSIS_DIR/cli_*.json`
5. **Load into DuckDB** - Transform and store all data as named tables:
   - Use `jq` to reshape complex/nested JSON before loading
   - Use `duckdb "$DB" "CREATE TABLE t AS SELECT * FROM read_csv_auto('...');"` to load
   - Use DuckDB SQL for aggregation, filtering, joining — no one-off scripts
   - **NEVER process MCP results directly in LLM context**
6. **Export for Math MCP** - Run targeted SQL queries, export clean CSV:
   ```bash
   duckdb "$DB" "COPY (SELECT x, y FROM table ORDER BY x) TO '$ANALYSIS_DIR/plot_data.csv' (HEADER);"
   ```
7. **Select and execute Math MCP tools** - Call `math_ls()` to discover tools; use `math_man(name)` or `math_ls(category)` for parameters; then `math(name, arguments)` with exported CSV/JSON data (or `math_batch` for multiple independent calls).
8. **Visualize results** - Always combine analysis with visualization:
   - **Select graph type** using Graph Type Selection by Relationship table
   - **Apply Critical Design Rules** (zero baseline, meaningful ordering, minimal non-data ink, direct labeling)
   - **Use color purposefully** based on data type (sequential/diverging/categorical)
   - **Verify quality** using Quality Assessment Checklist before finalizing
9. **Save chart output** - Chart tools (e.g. `math(plot_timeseries, {...})`) return a URL (e.g. "Chart available at: http://..."). **Always** download the chart and save it into the analysis directory:
   - Create `$ANALYSIS_DIR/charts/` if it does not exist
   - Use `curl -sS -o "$ANALYSIS_DIR/charts/<descriptive_name>.png" "<url>"` to download the image
   - Use a descriptive filename (e.g. `draw_show_production.png`, `p50_p90_timeseries.png`) so charts are identifiable without opening them

**Key principles:**
- **ALWAYS create timestamped folder first** - `{project_root}/tmp/{YYYYMMDD}_{HHMMSS}/`
- **`analysis.duckdb` is the central data store** - all intermediate data lives as DuckDB tables
- **jq for JSON reshaping** - extract and normalize nested JSON before DuckDB loading
- **DuckDB SQL for all transformation** - aggregation, filtering, joining, window functions
- **⚠️ CRITICAL: raw source → jq → DuckDB → SQL → CSV → Math MCP**
- **NEVER process MCP results in LLM context** - load into DuckDB, query with SQL
- Users ask word problems, not math expressions - interpret accordingly
- **Math MCP handles calculations only** - not data extraction, filtering, or transformation
- **Token efficiency:** All data processing via DuckDB SQL and jq, LLM only for orchestration
- **Analysis session integrity:** All artifacts (duckdb file, raw MCP responses, exported CSVs, charts) in the same timestamped folder
- **Charts live in the analysis dir:** Chart MCP responses include a URL; download via curl and save to `$ANALYSIS_DIR/charts/` so the chart is persisted with the rest of the session
