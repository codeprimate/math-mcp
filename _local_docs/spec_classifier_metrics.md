# [Feature]: Binary Classifier Performance and Accuracy Metrics

## Problem Statement

Users need to perform **performance and accuracy analysis of binary classifiers**. Standard metrics and curves—confusion matrix, precision, recall, F1, ROC/PR curves, AUC, Brier score, log loss, Matthews correlation coefficient, and Cohen's kappa—are not provided by the math-mcp server. NumPy and SciPy do not implement these; they are implemented in **scikit-learn** (`sklearn.metrics`). The service should be augmented so that classifier evaluation can be requested via MCP tools without requiring the client to implement or call sklearn directly.

## Requirements

### Functional Requirements

- Expose classifier evaluation metrics as MCP tools callable with ground-truth and predicted labels (and, where applicable, scores/probabilities).
- **Label-based metrics** (from `y_true`, `y_pred`): confusion matrix, accuracy, precision, recall, F1 (and Fβ), Matthews correlation coefficient, Cohen's kappa.
- **Score/probability-based metrics** (from `y_true`, `y_score`/`y_prob`): ROC curve (FPR, TPR, thresholds), AUC-ROC, precision–recall curve, average precision (AUC-PR), Brier score, log loss.
- All tools must accept **binary** labels (e.g. 0/1); `pos_label` must be configurable where relevant (default 1).
- Tool outputs must be **JSON-serializable** (scalars and arrays as lists) for easy consumption by MCP clients.
- Behavior and naming must align with `sklearn.metrics` so that documentation and prior knowledge transfer directly.

### Technical Constraints

- Add **scikit-learn** as a dependency (e.g. `scikit-learn>=1.3`) in `pyproject.toml`; no other new runtime dependencies.
- Follow existing server patterns: one module for the new tools, a single `register_*_tools(mcp)` function, tools implemented as plain functions returning `str` (JSON), parameters via `Annotated` and Pydantic `Field`.
- Preserve Python >=3.10 and existing tool registration order/conventions in `server.py`.
- No change to transport, auth, or HTTP/stdio behavior.

### Edge Cases & Error Handling

- **Empty or length-mismatched arrays**: Return clear error messages (e.g. "y_true and y_pred must have the same length"); do not raise uncaught exceptions to the client.
- **Non-binary labels**: Document that inputs are expected to be binary; optionally validate and return an error if more than two distinct values appear (or document binary-only behavior and defer multiclass to a later phase).
- **Constant y_true** (e.g. all 0 or all 1): `roc_curve`/`roc_auc_score` and similar may have edge behavior; handle sklearn warnings or edge returns (e.g. empty threshold arrays) and return stable JSON (e.g. empty lists or a clear message).
- **Invalid numeric input**: Coerce to float where applicable; if conversion fails, return an error string rather than raising.
- **pos_label**: If the specified `pos_label` does not appear in `y_true`/`y_pred`, return a clear error or document behavior (e.g. sklearn may raise).

## Technical Approach

### Implementation Strategy

- **New module**: `src/math_mcp/classifier_metrics_tools.py` containing tool implementations and `register_classifier_metrics_tools(mcp)`. Do not extend `stats_tools.py`; classifier evaluation is a separate concern and keeps discovery and maintenance clear.
- **One tool per metric/curve**: Each sklearn metric or curve gets a single MCP tool (e.g. `confusion_matrix`, `classifier_accuracy`, `precision_recall_f1`, `matthews_corrcoef`, `cohen_kappa`, `roc_curve`, `roc_auc_score`, `precision_recall_curve`, `average_precision_score`, `brier_score`, `log_loss`). This matches user mental model and existing granular tool style (see `stats_tools.py`).
- **Input format**: `y_true`, `y_pred` as `list[float]` or `list[int]` (treated as 0/1 or binary). `y_score`/`y_prob` as `list[float]` (scores or probabilities for the positive class). Optional `pos_label` (default 1) where supported by sklearn.
- **Output format**: JSON only. Confusion matrix as 2×2 list or `{tn, fp, fn, tp}`. Curves as `{fpr, tpr, thresholds}` or `{precision, recall, thresholds}`. Scalars as small JSON objects with named keys.
- **Binary-only for v1**: Implement and document binary classification only. Multiclass (e.g. `average='micro'|'macro'|'weighted'` for precision/recall/F1) can be a later enhancement.
- **Code quality**: Use existing ruff settings; no new linter config. Tests via pytest with `PYTHONPATH=src`; follow patterns in `tests/test_stats.py` (import tool functions, call with lists, assert on parsed JSON and error strings).

### Affected Components

- **New**: `src/math_mcp/classifier_metrics_tools.py` — all new tool functions and `register_classifier_metrics_tools(mcp)`.
- **Modify**: `pyproject.toml` — add `scikit-learn>=1.3` to `dependencies`.
- **Modify**: `src/math_mcp/server.py` — import the new module and call `classifier_metrics_tools.register_classifier_metrics_tools(mcp)` after `stats_tools.register_stats_tools(mcp)` (or in another logical position with other tool registrations).
- **New**: `tests/test_classifier_metrics_tools.py` — unit tests for each tool (valid inputs, expected keys/values, empty/mismatch/invalid input error paths).
- **Modify**: `README.md` (and any tool list in `AGENTS.md`) — document the new tools, purpose, and example usage.

### Dependencies & Integration

- **External**: scikit-learn (new). NumPy already used by existing stats/plot tools; sklearn depends on numpy.
- **Internal**: No other math_mcp modules need to import classifier_metrics_tools except `server.py` for registration. No change to batch_tools, plot_output, or plotting_tools unless optional ROC/PR plot tools are added later.

## Acceptance Criteria

- [ ] scikit-learn is added to `pyproject.toml` and `uv sync` installs it.
- [ ] All 11 tools are implemented and registered (confusion_matrix, classifier_accuracy, precision_recall_f1, matthews_corrcoef, cohen_kappa, roc_curve, roc_auc_score, precision_recall_curve, average_precision_score, brier_score, log_loss).
- [ ] Each tool returns valid JSON (or an error string starting with "Error:") and accepts the documented inputs; binary labels and optional pos_label behave as specified.
- [ ] `ruff check --fix src/ tests/` passes.
- [ ] All new tests in `tests/test_classifier_metrics_tools.py` pass with `PYTHONPATH=src pytest tests/ -v`.
- [ ] README (and AGENTS.md if it lists tools) updated with the new classifier metrics tools and at least one example per tool or a consolidated example.

## Implementation Tasks

- [ ] Add `scikit-learn>=1.3` to `dependencies` in `pyproject.toml` and run `uv sync`.
- [ ] Create `src/math_mcp/classifier_metrics_tools.py` with helper to validate binary labels and array lengths.
- [ ] Implement and export: `tool_confusion_matrix`, `tool_classifier_accuracy`, `tool_precision_recall_f1`, `tool_matthews_corrcoef`, `tool_cohen_kappa`, `tool_roc_curve`, `tool_roc_auc_score`, `tool_precision_recall_curve`, `tool_average_precision_score`, `tool_brier_score`, `tool_log_loss`.
- [ ] Implement `register_classifier_metrics_tools(mcp)` and register each tool with a clear `name=` matching the table (e.g. `confusion_matrix`, `classifier_accuracy`, ...).
- [ ] In `server.py`, import `classifier_metrics_tools` and call `register_classifier_metrics_tools(mcp)`.
- [ ] Add `tests/test_classifier_metrics_tools.py` with tests for success cases and for empty/mismatched length/invalid input.
- [ ] Run ruff and fix any issues; run full test suite.
- [ ] Update README.md (and AGENTS.md if applicable) with the new tools and examples.

## Risk Assessment

### Potential Issues

- **Breaking change**: None; purely additive tools and one new dependency.
- **Performance**: Negligible; tools are per-request and sklearn is fast for typical array sizes used in classifier evaluation.
- **Security**: No new network or file I/O; inputs are arrays and optional scalars. Oversized arrays could consume memory; consider documenting reasonable limits if needed later.

### Mitigation Strategies

- Validate array lengths and binary labels at tool entry; return error strings for invalid input.
- Rely on sklearn for numerical correctness; avoid reimplementing metrics.
- If sklearn raises (e.g. constant y_true), catch and return a clear "Error: ..." string.

### Investigation Requirements

- None required for v1. Optional follow-ups: multiclass support, ROC/PR plot tools that produce image content using existing plotting pipeline.

---

## Reference: sklearn.metrics Mapping

| Tool name                | sklearn function                          | Main inputs        |
|--------------------------|-------------------------------------------|--------------------|
| confusion_matrix         | confusion_matrix                          | y_true, y_pred     |
| classifier_accuracy      | accuracy_score                            | y_true, y_pred     |
| precision_recall_f1      | precision_recall_fscore_support / *_score  | y_true, y_pred     |
| matthews_corrcoef        | matthews_corrcoef                         | y_true, y_pred     |
| cohen_kappa              | cohen_kappa_score                         | y_true, y_pred     |
| roc_curve                | roc_curve                                 | y_true, y_score    |
| roc_auc_score            | roc_auc_score                             | y_true, y_score    |
| precision_recall_curve   | precision_recall_curve                    | y_true, y_score    |
| average_precision_score  | average_precision_score                   | y_true, y_score    |
| brier_score              | brier_score_loss                          | y_true, y_prob     |
| log_loss                 | log_loss                                  | y_true, y_prob     |

---

## Deep Dive: Second-Order Effects and Considerations

- **batch_tools**: The batch executor discovers tools by name. New classifier tools will automatically be available in `batch_tools` (e.g. run `confusion_matrix` and `roc_auc_score` in one request). No code change needed; ensure tool names are stable and documented.

- **Docker and image size**: Adding scikit-learn increases the Docker image size (sklearn has numpy, scipy, joblib as deps; scipy and numpy are already present). Build time may increase slightly. No change to docker-compose or Dockerfile is strictly required unless version pinning is desired.

- **Import time and startup**: Importing sklearn.metrics is lazy per tool or at module load. Registering one more module in `server.py` has negligible impact. If the server is used only for symbolic math, the extra dependency is still loaded; acceptable for this codebase.

- **Consistency with stats_tools**: Stats tools return JSON with specific keys (e.g. `mean`, `pvalue`). Classifier tools should follow the same pattern: consistent key names (e.g. `tp`, `fp`, `tn`, `fn` or `precision`, `recall`, `f1`) and same error format (`"Error: ..."`) so clients can parse uniformly.

- **Documentation surface**: README already has a long tools table. Adding 11 rows is significant. Consider a subsection "Classifier evaluation" with a compact table and one or two combined examples to avoid table bloat while keeping discoverability.

- **Future ROC/PR plots**: If later adding `plot_roc_curve` / `plot_precision_recall_curve`, they would live in `plotting_tools.py` and use the same plot-output and URL machinery as other plot tools. The metrics tools would remain the single source of truth for curve data; plot tools would call sklearn internally (no need to pass curve JSON from client). This spec does not mandate those plot tools.

- **Multiclass later**: Extending to multiclass would touch `precision_recall_f1` (average parameter), `confusion_matrix` (larger matrix), and possibly ROC/PR (one-vs-rest). Keeping v1 binary-only avoids ambiguity in `pos_label` and keeps doc and tests simpler.
