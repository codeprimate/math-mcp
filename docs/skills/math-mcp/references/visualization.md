# Visualization Design Principles

**CRITICAL: Design for perception, not preference. Every visualization choice should optimize for accurate, efficient transfer of quantitative understanding.**

## Graph Type Selection by Relationship

**Match the quantitative relationship to the optimal visualization:**

| Relationship Type | Primary Tool | Rationale |
|------------------|--------------|-----------|
| **Time-series** | `plot_timeseries` | Position + continuity reveals trends over time |
| **Categorical comparison** | `plot_bar_chart` (horizontal preferred) | Length along common scale = highest accuracy |
| **Ranking** | `plot_bar_chart` (sorted by value) | Direct length comparison enables ranking |
| **Part-to-whole** | `plot_stacked_bar` (use sparingly) | Length shows both parts and total |
| **Distribution** | `plot_histogram` | Shape reveals data spread and outliers |
| **Correlation (2 vars)** | `plot_scatter` | Position encodes both variables simultaneously |
| **Deviation from reference** | `plot_bar_chart` with reference line | Shows variance from target/baseline |

**When to use tables instead of graphs:**
- Precise value lookup required
- Small datasets (<20 values)
- Audience needs to reference specific numbers
- Heterogeneous measures that don't share a scale

## Critical Design Rules (MANDATORY)

**ALWAYS apply these principles:**

1. **Position encodes quantity** - Use position along axis as primary encoding (bars, lines, points). It's the most accurate perceptual channel.

2. **Start bar graphs at zero** - Bars encode length; truncation distorts ratio perception. Lines can use non-zero baselines when showing change magnitude.

3. **Order data meaningfully:**
   - Quantitative: By value (largest to smallest or vice versa)
   - Temporal: Chronologically
   - Categorical: Alphabetically or by natural hierarchy
   - **Never leave arbitrary/random ordering**

4. **Minimize non-data ink:**
   - Remove gridlines unless essential for value lookup
   - Use lightest possible weight for necessary structural elements
   - Every visual element must justify its presence
   - Clean, uncluttered data region (white/light background)

5. **Label directly** - Place labels near data rather than using legends when possible. Reduces cognitive load.

6. **Choose appropriate aspect ratio** - Graphs should typically be wider than tall (~1.3-2:1 ratio). Optimize for perceiving the relationship being shown.

7. **Axes labeled with units** - Always include clear axis labels with measurement units.

8. **Scale intervals intuitive** - Use round numbers (1, 2, 5, 10, 25, 50, 100...) for axis ticks.

9. **Match timestamp label format to the data's time range, always in local timezone** - Never use full ISO timestamps or datetime strings as axis labels or category labels. Choose the shortest format that preserves meaning at the displayed granularity. Convert to local timezone before formatting unless the user specifies otherwise.

   | Data range | Appropriate label | ❌ Never use |
   |------------|-------------------|-------------|
   | Multiple years | `2024`, `2025` | `2024-01-01 00:00:00` |
   | Months within a year | `Jan`, `Feb` | `2026-01-01T00:00:00Z` |
   | Months across years | `Jan 2025`, `Feb 2026` | `2025-01-01 00:00:00.000` |
   | Days within a month | `Jan 1`, `Jan 15` | `2026-01-15 00:00:00` |
   | Days across months | `Mar 28`, `Apr 3` | `2026-03-28T00:00:00+00:00` |
   | Hours within a day | `14:00`, `15:00` | `2026-01-15 14:00:00 UTC` |
   | Hours across days | `Jan 15 14:00` | `2026-01-15T14:00:00.000Z` |

   **Format at the source** (in DuckDB before export) — convert timezone then apply STRFTIME. Never pass raw UTC timestamps expecting the chart tool to handle either.

   **Indicate the timezone on any chart that contains timestamps.** The reader cannot be expected to know what zone the data is in. Use the timezone abbreviation in the time axis label:
   - Axis label: `Time (PST)`, `Hour (EST)`, `Date (UTC)`
   - If the chart tool does not support axis subtitles, append to the chart title: `"Response Times — Jan 2026 (PST)"`
   - Use the common abbreviation (PST, EST, UTC) in the label — not the IANA name (`America/Los_Angeles`) which is too long for a label

**NEVER:**
- **No pie charts** - Humans cannot accurately compare angles or areas. Use horizontal bar graphs instead.
- **No 3D effects** - Always distorts values through perspective. Pure decoration that harms accuracy.
- **No dual-scale deception** - If using dual axes, ensure scales are proportionally meaningful; mismatched scales mislead.
- **No chartjunk** - No decorative elements, pictures, or embellishments that don't encode data.
- **No more than 6-8 colors** - Beyond this, color loses effectiveness as a categorical distinguisher.

## Color Usage Rules

**Apply color purposefully based on data type:**

1. **Sequential data** (ordered, one-directional): Single hue with varying intensity (light to dark)
2. **Diverging data** (meaningful midpoint): Two hues diverging from neutral center
3. **Categorical data** (nominal): Distinct hues, limited to 6-8 maximum
4. **Emphasis only** (highlighting): Bright accent color with muted background colors
5. **Always ensure colorblind accessibility** - Use colorblind-safe palettes

**Text legibility:** High contrast required. Avoid colored text on colored backgrounds.

## Visual Encoding Hierarchy (Accuracy)

**When choosing how to encode quantitative values, prefer higher-accuracy methods:**

**High Accuracy:**
- Position along common scale (bars on same axis)
- Position on identical non-aligned scales (small multiples)

**Moderate Accuracy:**
- Length without common scale
- Angle/slope
- Area

**Low Accuracy (avoid for quantitative):**
- Volume
- Color intensity
- Color hue
- Texture/pattern

## Multi-Variable Visualization

**When displaying many variables:**

1. **Small multiples** (preferred) - Repeat same graph structure with different data subsets. Consistent scales enable comparison.
2. **Layering** - Multiple series on one graph. Limit to 3-4 for clarity.
3. **Color encoding** - Add categorical dimension via color (max 6-8 categories)
4. **Faceting** - Break data into panels by categorical variables

**Avoid:** Cramming too much into single graph. Better to use multiple simple graphs than one complex graph.

## Quality Assessment Checklist

**Before finalizing any visualization, verify:**

- [ ] **Does it answer the question efficiently?** - Can the viewer extract the insight in <5 seconds?
- [ ] **Is anything misleading?** - Truncated axes? Manipulated scales? Distorted proportions?
- [ ] **Is every element necessary?** - Can anything be removed without losing meaning?
- [ ] **Does it show the data honestly?** - No visual distortion of relationships?
- [ ] **Is the comparison obvious?** - Are compared values visually proximate?
- [ ] **Would a simpler form work?** - Is complexity justified by data complexity?
- [ ] **Title clearly states what/when/where** - Context is clear
- [ ] **Bars start at zero** (if bar chart)
- [ ] **Data ordered meaningfully** (not random)
- [ ] **Direct labeling used** instead of legend when possible
- [ ] **Color used purposefully**, not decoratively
