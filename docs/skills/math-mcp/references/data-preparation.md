# Data Preparation Protocol

**MANDATORY - Execute BEFORE any MCP analysis:**

**CRITICAL: Use DuckDB as the central data store and jq for JSON transformation. Minimize token usage by keeping data out of the LLM context entirely.**

## Core Toolchain

| Tool | Purpose |
|------|---------|
| `duckdb` | Central data store, SQL aggregation, export to CSV/JSON |
| `jq` | JSON extraction and reshaping before DuckDB loading |
| `psql` | PostgreSQL data extraction (output → DuckDB) |
| `curl` | API data fetching (output → jq → DuckDB) |

## File Storage Requirement

**⚠️ MANDATORY - NO EXCEPTIONS:**

Every analysis session gets its own timestamped folder in the **project** tmp directory:

```
{project_root}/tmp/{YYYYMMDD}_{HHMMSS}/
```

**Example:** `{project_root}/tmp/20260112_143052/`

Within this folder:
- `analysis.duckdb` — the central data store for the session
- `mcp_*.json` — raw MCP tool responses (saved immediately)
- `cli_*.csv` / `cli_*.json` — raw CLI extracts
- `*.sql` — any DuckDB SQL scripts written for complex transforms
- `*.png` — generated charts

**NEVER save to:**
- `/tmp` (system temp)
- Project root
- Random locations outside the timestamped folder

## Session Setup

**Always start here:**

```bash
ANALYSIS_DIR="{project_root}/tmp/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$ANALYSIS_DIR"
DB="$ANALYSIS_DIR/analysis.duckdb"
```

`$DB` is the single source of truth for all intermediate data in the session.

## Data Pipeline Pattern

```
Raw source (MCP/DB/API/file)
    → [jq]    reshape/extract JSON
    → [duckdb] load into named table
    → [SQL]    aggregate, filter, join
    → [COPY]   export CSV/JSON for Math MCP
```

### Loading Data into DuckDB

**From PostgreSQL:**
```bash
# Export to CSV, then load into DuckDB table
psql -c "COPY (SELECT id, duration, team_size FROM projects) TO STDOUT CSV HEADER" \
  > "$ANALYSIS_DIR/cli_projects.csv"

duckdb "$DB" "CREATE TABLE projects AS SELECT * FROM read_csv_auto('$ANALYSIS_DIR/cli_projects.csv');"
```

**From JSON (API or MCP output):**
```bash
# Save raw MCP response first
# (MCP tool call → save to file)
# e.g. "$ANALYSIS_DIR/mcp_metrics.json"

# jq to extract and reshape the nested structure
jq '[.data[] | {timestamp: .ts, value: .v, category: .cat}]' \
  "$ANALYSIS_DIR/mcp_metrics.json" > "$ANALYSIS_DIR/metrics.json"

# Load into DuckDB
duckdb "$DB" "CREATE TABLE metrics AS SELECT * FROM read_json_auto('$ANALYSIS_DIR/metrics.json');"
```

**From multiple sources (join in DuckDB):**
```bash
psql -c "COPY (SELECT id, name FROM categories) TO STDOUT CSV HEADER" \
  > "$ANALYSIS_DIR/cli_categories.csv"

duckdb "$DB" "CREATE TABLE categories AS SELECT * FROM read_csv_auto('$ANALYSIS_DIR/cli_categories.csv');"

# Now join inside DuckDB — no script needed
duckdb "$DB" "
  CREATE TABLE enriched AS
  SELECT m.timestamp, m.value, c.name AS category
  FROM metrics m
  JOIN categories c ON m.category = c.id;
"
```

### Transforming Data with DuckDB SQL

Replace one-off processing scripts with SQL:

```bash
# Aggregate
duckdb "$DB" "
  CREATE TABLE daily_summary AS
  SELECT
    DATE_TRUNC('day', timestamp) AS day,
    category,
    AVG(value) AS avg_value,
    STDDEV(value) AS stddev_value,
    COUNT(*) AS n
  FROM metrics
  GROUP BY 1, 2
  ORDER BY 1, 2;
"

# Filter outliers
duckdb "$DB" "
  CREATE TABLE filtered AS
  SELECT * FROM metrics
  WHERE value BETWEEN
    (SELECT PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY value) FROM metrics) AND
    (SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY value) FROM metrics);
"

# Window functions for time series
duckdb "$DB" "
  CREATE TABLE with_rolling AS
  SELECT *,
    AVG(value) OVER (ORDER BY timestamp ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS rolling_7
  FROM metrics
  ORDER BY timestamp;
"
```

### Formatting Timestamps for Labels

**Format timestamps in DuckDB before export — convert to local timezone first, then apply STRFTIME.**

**Step 1: Detect local timezone and set it for the DuckDB session:**
```bash
LOCAL_TZ=$(date +%Z)   # e.g. "PST", "EST" — good for display
# For DuckDB SET TimeZone, use the IANA name (e.g. America/Los_Angeles)
# Detect from system:
LOCAL_IANA=$(readlink /etc/localtime | sed 's|.*/zoneinfo/||')
# e.g. "America/Los_Angeles"

duckdb "$DB" "SET TimeZone = '$LOCAL_IANA';"
```

Once `TimeZone` is set, DuckDB automatically converts `TIMESTAMPTZ` values when displaying or formatting — STRFTIME will operate in local time.

**Step 2: Choose the format that matches the chart's time granularity:**

```bash
# Year-level (multi-year range)  →  '2024', '2025'
duckdb "$DB" "
  SET TimeZone = '$LOCAL_IANA';
  COPY (SELECT STRFTIME(day::TIMESTAMPTZ, '%Y') AS x, value AS y FROM daily ORDER BY day)
  TO '$ANALYSIS_DIR/plot_data.csv' (HEADER);
"

# Month-level within one year  →  'Jan', 'Feb'
duckdb "$DB" "
  SET TimeZone = '$LOCAL_IANA';
  COPY (SELECT STRFTIME(month::TIMESTAMPTZ, '%b') AS x, value AS y FROM monthly ORDER BY month)
  TO '$ANALYSIS_DIR/plot_data.csv' (HEADER);
"

# Month-level across years  →  'Jan 2025', 'Feb 2026'
duckdb "$DB" "
  SET TimeZone = '$LOCAL_IANA';
  COPY (SELECT STRFTIME(month::TIMESTAMPTZ, '%b %Y') AS x, value AS y FROM monthly ORDER BY month)
  TO '$ANALYSIS_DIR/plot_data.csv' (HEADER);
"

# Day-level  →  'Jan 15', 'Jan 16'
duckdb "$DB" "
  SET TimeZone = '$LOCAL_IANA';
  COPY (SELECT STRFTIME(day::TIMESTAMPTZ, '%b %-d') AS x, value AS y FROM daily ORDER BY day)
  TO '$ANALYSIS_DIR/plot_data.csv' (HEADER);
"

# Hour-level within a day  →  '14:00', '15:00'
duckdb "$DB" "
  SET TimeZone = '$LOCAL_IANA';
  COPY (SELECT STRFTIME(hour::TIMESTAMPTZ, '%H:%M') AS x, value AS y FROM hourly ORDER BY hour)
  TO '$ANALYSIS_DIR/plot_data.csv' (HEADER);
"

# Hour-level across days  →  'Jan 15 14:00'
duckdb "$DB" "
  SET TimeZone = '$LOCAL_IANA';
  COPY (SELECT STRFTIME(hour::TIMESTAMPTZ, '%b %-d %H:%M') AS x, value AS y FROM hourly ORDER BY hour)
  TO '$ANALYSIS_DIR/plot_data.csv' (HEADER);
"
```

**Rules:**
- **Always convert to local timezone** — raw UTC timestamps on charts are misleading for humans reading wall-clock time. Use the user's local timezone unless they specify otherwise.
- **The label should contain only the information that *changes*** within the chart's visible range. If all data is from January 2026, `Jan 15` is sufficient — `2026-01-15 00:00:00 UTC` adds noise and causes label overlap.
- **Explicit TZ override:** If the user specifies a timezone (e.g. "show in UTC" or "use New York time"), use that IANA name instead of `$LOCAL_IANA`.

### Exporting for Math MCP

Math MCP reads CSV and JSON files. Export from DuckDB:

```bash
# Export table to CSV (for Math MCP)
duckdb "$DB" "COPY daily_summary TO '$ANALYSIS_DIR/daily_summary.csv' (HEADER);"

# Export query result to JSON
duckdb "$DB" "COPY (SELECT * FROM filtered ORDER BY timestamp) TO '$ANALYSIS_DIR/filtered.json';"

# Export specific columns
duckdb "$DB" "
  COPY (SELECT timestamp AS x, value AS y FROM metrics ORDER BY timestamp)
  TO '$ANALYSIS_DIR/plot_data.csv' (HEADER);
"
```

## MCP Results Artifacts Pattern

**⚠️ CRITICAL: Never process MCP tool responses in LLM context.**

1. **Save MCP outputs to files immediately:**
   - AppSignal MCP, database MCPs, API MCPs → `$ANALYSIS_DIR/mcp_*.json`

2. **Use jq to extract and reshape:**
   ```bash
   jq '[.[] | select(.error == null) | {x: .timestamp, y: .value}]' \
     "$ANALYSIS_DIR/mcp_response.json" > "$ANALYSIS_DIR/series.json"
   ```

3. **Load into DuckDB:**
   ```bash
   duckdb "$DB" "CREATE TABLE series AS SELECT * FROM read_json_auto('$ANALYSIS_DIR/series.json');"
   ```

4. **Transform with SQL, export for Math MCP:**
   ```bash
   duckdb "$DB" "COPY (SELECT x, y FROM series ORDER BY x) TO '$ANALYSIS_DIR/plot_data.csv' (HEADER);"
   ```

**Full example workflow:**
```bash
# Setup
ANALYSIS_DIR="{project_root}/tmp/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$ANALYSIS_DIR"
DB="$ANALYSIS_DIR/analysis.duckdb"

# Step 1: MCP tool saves response to file (e.g. $ANALYSIS_DIR/mcp_appsignal.json)

# Step 2: jq extracts relevant fields
jq '[.data.timeseries[] | {ts: .time, val: .value, host: .tags.hostname}]' \
  "$ANALYSIS_DIR/mcp_appsignal.json" > "$ANALYSIS_DIR/timeseries.json"

# Step 3: Load into DuckDB
duckdb "$DB" "CREATE TABLE timeseries AS SELECT * FROM read_json_auto('$ANALYSIS_DIR/timeseries.json');"

# Step 4: Aggregate with SQL
duckdb "$DB" "
  CREATE TABLE hourly AS
  SELECT DATE_TRUNC('hour', ts::TIMESTAMP) AS hour, AVG(val) AS avg_val
  FROM timeseries GROUP BY 1 ORDER BY 1;
"

# Step 5: Export for Math MCP
duckdb "$DB" "COPY hourly TO '$ANALYSIS_DIR/hourly.csv' (HEADER);"

# Math MCP reads: $ANALYSIS_DIR/hourly.csv
```

## jq Reference for Common Transforms

```bash
# Extract array of objects from nested path
jq '.response.data.items' input.json > output.json

# Reshape object structure
jq '[.[] | {x: .created_at, y: .duration_ms, label: .name}]' input.json > output.json

# Filter by condition
jq '[.[] | select(.status == "completed" and .value > 0)]' input.json > output.json

# Compute derived field
jq '[.[] | . + {rate: (.errors / .requests)}]' input.json > output.json

# Flatten nested array
jq '[.groups[] | .items[] | {group: .parent_name, item: .name, value: .count}]' \
  input.json > output.json

# Newline-delimited JSON (for streaming into DuckDB read_json)
jq -c '.[]' input.json > output.ndjson
```

## Sampling Large Datasets

```bash
# Random sample via PostgreSQL, load into DuckDB
psql -c "COPY (SELECT * FROM events TABLESAMPLE SYSTEM (5) LIMIT 1000) TO STDOUT CSV HEADER" \
  > "$ANALYSIS_DIR/cli_sample.csv"

duckdb "$DB" "CREATE TABLE sample AS SELECT * FROM read_csv_auto('$ANALYSIS_DIR/cli_sample.csv');"

# Or sample inside DuckDB after loading full table
duckdb "$DB" "
  CREATE TABLE sample AS
  SELECT * FROM full_table
  USING SAMPLE 10 PERCENT (bernoulli);
"
```

## Inspecting the DuckDB Database

```bash
# List tables in the session
duckdb "$DB" ".tables"

# Describe a table
duckdb "$DB" "DESCRIBE metrics;"

# Quick row counts
duckdb "$DB" "SELECT COUNT(*) FROM metrics;"

# Preview data
duckdb "$DB" "SELECT * FROM metrics LIMIT 5;"
```

**Key principles:**
- **One `analysis.duckdb` per session** — all intermediate data lives in DuckDB tables, not scattered files
- **jq for JSON reshaping** — handle nested/complex JSON before DuckDB, not in LLM context
- **DuckDB SQL for all transformation** — aggregation, filtering, joining, window functions
- **Export CSV/JSON only for Math MCP** — DuckDB → `COPY TO` → Math MCP reads file
- **Save raw MCP artifacts to files** — always preserve the original response for debugging
- **Math MCP handles calculations only** — not extraction, filtering, or transformation
