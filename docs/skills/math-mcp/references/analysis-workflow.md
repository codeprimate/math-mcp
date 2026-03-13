# Analysis Workflow

**CRITICAL: Breaking Down Analysis Into Steps**

**NEVER submit all data or perform complex multi-step analysis in a single MCP call.**

## Step-by-Step Analysis Protocol

**For ANY analysis task, follow this discrete step pattern:**

1. **Initial Exploration (First Step)**
   - Use `describe_data` on the full dataset to understand basic statistics
   - Purpose: Get summary statistics (mean, median, std dev, min/max, quartiles)
   - **Wait for results before proceeding**

2. **Visual Understanding (Second Step)**
   - Based on describe_data results, choose ONE appropriate plot using Graph Type Selection principles:
     - `plot_histogram` for distribution shape
     - `plot_bar_chart` for categorical comparisons, rankings, or deviations from reference
     - `plot_scatter` for relationships/correlations between two variables
     - `plot_timeseries` for temporal patterns and trends
     - `plot_stacked_bar` for part-to-whole relationships (use sparingly)
   - **Apply Critical Design Rules:** Zero baseline for bars, meaningful ordering, minimal non-data ink, direct labeling
   - Purpose: Visual confirmation of data patterns
   - **Wait for results before proceeding**

3. **Targeted Analysis (Third Step)**
   - Based on visual patterns, perform ONE specific analysis:
     - `correlation` for relationships
     - `ttest` for comparing groups
     - `linear_regression` for trend prediction
     - `moving_average` for smoothing time series
   - Purpose: Answer the specific question identified
   - **Wait for results before proceeding**

4. **Additional Visualization (Fourth Step, if needed)**
   - Create final visualization showing analysis results
   - Purpose: Communicate findings clearly

## Data Size Management

**For large datasets (>1000 rows):**

1. **Create analysis folder and DuckDB database:**
   ```bash
   ANALYSIS_DIR="{project_root}/tmp/$(date +%Y%m%d_%H%M%S)"
   mkdir -p "$ANALYSIS_DIR"
   DB="$ANALYSIS_DIR/analysis.duckdb"
   ```

2. **Sample first using DuckDB:**
   ```bash
   # Load full data into DuckDB, then sample
   duckdb "$DB" "CREATE TABLE events AS SELECT * FROM read_csv_auto('$ANALYSIS_DIR/cli_events.csv');"

   duckdb "$DB" "
     CREATE TABLE sample AS
     SELECT * FROM events USING SAMPLE 10 PERCENT (bernoulli) LIMIT 1000;
   "
   duckdb "$DB" "COPY sample TO '$ANALYSIS_DIR/sample.csv' (HEADER);"
   ```

3. **Analyze sample:** Run initial analysis on the exported sample CSV

4. **Segment by time period or category using DuckDB:**
   ```bash
   # Analyze by month — query DuckDB, export each segment
   duckdb "$DB" "
     COPY (SELECT * FROM events WHERE created_at >= '2026-01-01' AND created_at < '2026-02-01')
     TO '$ANALYSIS_DIR/jan_data.csv' (HEADER);
   "
   duckdb "$DB" "
     COPY (SELECT * FROM events WHERE created_at >= '2026-02-01' AND created_at < '2026-03-01')
     TO '$ANALYSIS_DIR/feb_data.csv' (HEADER);
   "
   ```

5. **Aggregate using DuckDB SQL:**
   ```bash
   # Pre-aggregate before Math MCP analysis
   duckdb "$DB" "
     COPY (
       SELECT category, AVG(value) AS mean, STDDEV(value) AS stddev, COUNT(*) AS n
       FROM events GROUP BY category ORDER BY mean DESC
     ) TO '$ANALYSIS_DIR/aggregated.csv' (HEADER);
   "
   ```

## Multi-Variable Analysis

**For comparing multiple variables, use ONE variable per step:**

❌ **WRONG - Don't do this:**
```
Analyze correlation between A, B, C, D, E, F all at once
```

✅ **CORRECT - Do this:**
```
Step 1: Analyze A vs B correlation
Step 2: Analyze A vs C correlation
Step 3: Analyze B vs C correlation
(Only continue if patterns warrant further investigation)
```

**Prepare each pair from DuckDB:**
```bash
# Export each pair from the same DuckDB session
duckdb "$DB" "COPY (SELECT a, b FROM data) TO '$ANALYSIS_DIR/pair_ab.csv' (HEADER);"
duckdb "$DB" "COPY (SELECT a, c FROM data) TO '$ANALYSIS_DIR/pair_ac.csv' (HEADER);"
```

## Complex Problem Decomposition

**For complex questions, break into atomic sub-questions:**

**Example: "What factors affect project completion time?"**

❌ **WRONG:** Submit all project data and try to analyze everything at once

✅ **CORRECT:**
```bash
# Step 0: Create analysis folder and load all data into DuckDB
ANALYSIS_DIR="{project_root}/tmp/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$ANALYSIS_DIR"
DB="$ANALYSIS_DIR/analysis.duckdb"

# Load from PostgreSQL into DuckDB
psql -c "COPY (SELECT duration, team_size, budget, scope_changes FROM projects) TO STDOUT CSV HEADER" \
  > "$ANALYSIS_DIR/cli_projects.csv"

duckdb "$DB" "CREATE TABLE projects AS SELECT * FROM read_csv_auto('$ANALYSIS_DIR/cli_projects.csv');"

# Export the base dataset for initial describe_data
duckdb "$DB" "COPY projects TO '$ANALYSIS_DIR/projects.csv' (HEADER);"
```

1. **Describe project duration data** → `describe_data` on `$ANALYSIS_DIR/projects.csv` → understand distribution
2. **Plot duration histogram** → identify outliers

3. **Correlate duration with team size:**
   ```bash
   duckdb "$DB" "COPY (SELECT duration, team_size FROM projects) TO '$ANALYSIS_DIR/dur_vs_team.csv' (HEADER);"
   ```
   → `correlation` on `$ANALYSIS_DIR/dur_vs_team.csv`

4. **Correlate duration with budget:**
   ```bash
   duckdb "$DB" "COPY (SELECT duration, budget FROM projects) TO '$ANALYSIS_DIR/dur_vs_budget.csv' (HEADER);"
   ```
   → `correlation` on `$ANALYSIS_DIR/dur_vs_budget.csv`

5. **Correlate duration with scope changes:**
   ```bash
   duckdb "$DB" "COPY (SELECT duration, scope_changes FROM projects) TO '$ANALYSIS_DIR/dur_vs_scope.csv' (HEADER);"
   ```
   → `correlation` on `$ANALYSIS_DIR/dur_vs_scope.csv`

6. Only continue with additional factors if clear patterns emerge

**Result:** All analysis artifacts in `{project_root}/tmp/20260112_143052/` — one `analysis.duckdb` containing all tables plus CSV exports for Math MCP.

## Key Principles

- **ONE tool call per step** - wait for results before next step
- **ONE question per step** - don't combine multiple analyses
- **ONE variable comparison at a time** - no mass correlation matrices
- **Sample large datasets** - use DuckDB SAMPLE before exporting to Math MCP
- **Use DuckDB SQL for aggregation** - not Math MCP, not LLM loops
- **Each step informs the next** - let data guide analysis path

**Rationale:**
- Prevents MCP server overload
- Allows interpretation between steps
- Enables early termination if patterns are clear
- Reduces token usage and processing time
- Makes analysis reproducible and debuggable (inspect `analysis.duckdb` at any point)
