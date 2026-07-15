import fs from "fs";
import path from "path";
import crypto from "crypto";
import os from "os";
import { spawnSync } from "child_process";
import { ensureDir, readJson, renderTemplate, writeJson, writeText } from "./natcs_utils.mjs";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const ARCHIVE_ROOT = path.join(ROOT, "output", "reviewer_archive", "natcs_reviewer_archive");
const ARCHIVE_PARENT = path.dirname(ARCHIVE_ROOT);
const ARCHIVE_ZIP = path.join(ARCHIVE_PARENT, "latest_natcs_reviewer_archive.zip");
const CODE_ROOT = path.join(ARCHIVE_ROOT, "code");
const ENV_ROOT = path.join(ARCHIVE_ROOT, "environment");
const REPRO_ROOT = path.join(ARCHIVE_ROOT, "reproduce");
const DATA_ROOT = path.join(ARCHIVE_ROOT, "data_access");
const SRC_ROOT = path.join(ROOT, "manuscript_src", "natcs");

function copyFile(src, dest) {
  assertCopySourceLocal(src);
  ensureDir(path.dirname(dest));
  if (fs.existsSync(dest) && !fs.lstatSync(dest).isDirectory()) {
    fs.rmSync(dest, { force: true });
  }
  fs.copyFileSync(src, dest);
}

function macFileFlags(file) {
  const result = spawnSync("stat", ["-f", "%Sf", file], { cwd: ROOT, encoding: "utf8" });
  return result.status === 0 ? result.stdout.trim() : "";
}

function assertCopySourceLocal(src) {
  if (macFileFlags(src).split(",").includes("dataless")) {
    throw new Error(`Reviewer archive source is dataless; hydrate or regenerate before copying: ${path.relative(ROOT, src)}`);
  }
}

function copyTree(src, dest, predicate) {
  const stat = fs.statSync(src);
  if (stat.isDirectory()) {
    if (!isCleanArchivePath(src)) return;
    ensureDir(dest);
    for (const entry of fs.readdirSync(src)) {
      const childSrc = path.join(src, entry);
      const childDest = path.join(dest, entry);
      copyTree(childSrc, childDest, predicate);
    }
    return;
  }
  if (!isCleanArchivePath(src)) return;
  if (!predicate(src)) return;
  copyFile(src, dest);
}

function isCleanArchivePath(src) {
  const base = path.basename(src);
  if (base === ".DS_Store") return false;
  if (base === "_archives") return false;
  if (hasNumberedDuplicateSuffix(base)) return false;
  if (/^backup_before_/i.test(base)) return false;
  if (base === "submission_checklist.md") return false;
  if (src.includes("__pycache__")) return false;
  return true;
}

function hasNumberedDuplicateSuffix(name) {
  return / \d+(?=(?:\.[^.]+)?$)/.test(name);
}

function isCleanArchiveFile(src) {
  return isCleanArchivePath(src);
}

function commandOutput(command, args) {
  const result = spawnSync(command, args, { cwd: ROOT, encoding: "utf8" });
  if (result.status !== 0) return null;
  return (result.stdout || "").trim();
}

function relArchivePath(file) {
  return path.relative(ARCHIVE_ROOT, file).split(path.sep).join("/");
}

function sha256File(file) {
  const hash = crypto.createHash("sha256");
  hash.update(fs.readFileSync(file));
  return hash.digest("hex");
}

function listArchiveFiles(root = ARCHIVE_ROOT) {
  if (!fs.existsSync(root)) return [];
  const files = [];
  const walk = (dir) => {
    for (const entry of fs.readdirSync(dir).sort()) {
      const current = path.join(dir, entry);
      const stat = fs.lstatSync(current);
      if (stat.isDirectory()) {
        walk(current);
      } else if (stat.isFile()) {
        files.push(current);
      }
    }
  };
  walk(root);
  return files;
}

function archiveChecksums() {
  return Object.fromEntries(
    listArchiveFiles()
      .filter((file) => relArchivePath(file) !== "manifest.json")
      .map((file) => [relArchivePath(file), sha256File(file)])
  );
}

function dependencyManifestStatus() {
  const candidates = [
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "npm-shrinkwrap.json",
  ];
  const present = candidates.filter((name) => fs.existsSync(path.join(ROOT, name)));
  return {
    present,
    note: present.length
      ? "Node dependency manifest files were present at archive build time."
      : "No Node package manifest or lockfile was present at archive build time; the JavaScript build scripts use Node built-ins.",
  };
}

function parseCsvLine(line) {
  const cells = [];
  let current = "";
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (ch === '"') {
      if (quoted && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        quoted = !quoted;
      }
    } else if (ch === "," && !quoted) {
      cells.push(current);
      current = "";
    } else {
      current += ch;
    }
  }
  cells.push(current);
  return cells;
}

function readCsvRows(file) {
  const lines = fs.readFileSync(file, "utf8").trim().split(/\r?\n/);
  const header = parseCsvLine(lines[0] || "");
  return lines.slice(1).filter(Boolean).map((line) => {
    const cells = parseCsvLine(line);
    return Object.fromEntries(header.map((key, i) => [key, cells[i] ?? ""]));
  });
}

function sanitizeMetadata(meta) {
  return {
    ...meta,
    authors: ["Anonymous"],
    affiliations: ["Affiliation withheld for peer review."],
    correspondence: "Correspondence withheld for peer review.",
    funding: "Funding statement withheld for peer review.",
    reference_docx: "",
  };
}

function computeReviewerTemplateContext() {
  const summaryPath = path.join(ROOT, "output", "natcs_evidence", "summary_metrics.json");
  if (!fs.existsSync(summaryPath)) return {};
  const summary = readJson(summaryPath);
  const synth = summary.synthetic_benchmark || {};
  const selection = summary.selection_summary || {};
  const pairCount = 15 * 14;
  const dateCount = Math.round((summary.baseline_association?.n || 0) / pairCount);
  const simulationTablePath = path.join(ROOT, "output", "natcs_evidence", "table1_simulation_benchmark.csv");
  const simulationRows = fs.existsSync(simulationTablePath)
    ? fs.readFileSync(simulationTablePath, "utf8").trim().split(/\r?\n/).slice(1).map((line) => parseCsvLine(line))
    : [];
  const simRow = (scenario, method) => {
    const row = simulationRows.find((cells) => cells[0] === scenario && cells[1] === method);
    if (!row) return {};
    return {
      effective: row[2],
      girf: row[6],
    };
  };
  const gainFor = (scenario, metricLabel) => {
    const row = simulationRows.find((cells) => cells[0] === scenario && cells[1] === "CP-network vs local rolling");
    if (!row) return NaN;
    const metricIdx = 2;
    const resultIdx = 3;
    const rows = simulationRows.filter((cells) => cells[0] === scenario && cells[1] === "CP-network vs local rolling");
    const metricRow = rows.find((cells) => cells[metricIdx] === metricLabel);
    const match = String(metricRow?.[resultIdx] ?? "").match(/([-+]?\d+(?:\.\d+)?)%/);
    return match ? Number(match[1]) : NaN;
  };
  const fmtGainRange = (values) => {
    const finite = values.filter((value) => Number.isFinite(Number(value))).map(Number).sort((a, b) => a - b);
    if (!finite.length) return "";
    return finite.map((value) => value.toFixed(1)).join("-");
  };
  const corr = (metric, target) => (summary.network_mechanisms || []).find((row) => row.metric === metric && row.target === target) || {};
  const nycCorr = (metric, target = "g_net") => (summary.nyc_network_mechanisms || []).find((row) => row.metric === metric && row.target === target) || {};
  const weakSep = (dataset) => (summary.weak_separation || []).find((row) => row.dataset === dataset) || {};
  const fmtCorr = (value) => (value === "" || value == null || Number.isNaN(Number(value)) ? "not estimable" : Number(value).toFixed(2));
  const fmtWeak = (value) => (value === "" || value == null || Number.isNaN(Number(value)) ? "not estimable" : Number(value).toExponential(2));
  const fmtWeakPct = (value) => (value === "" || value == null || Number.isNaN(Number(value)) ? "not estimable" : Number(value).toFixed(1));
  const perturb = (summary.network_propagation_perturbations || [])[0] || {};
  const nyc = summary.nyc_validation || {};
  const rcepDir = path.join(ROOT, "output", "natcs_empirical_cp", "rcep");
  const readSensitivity = (name) => fs.existsSync(path.join(rcepDir, name)) ? readCsvRows(path.join(rcepDir, name)) : [];
  const stabilityRow = (rows, statistic, sample) => rows.find((row) => row.Statistic === statistic && row.Sample === sample) || {};
  const stabilityExclusionRows = readSensitivity("stability_exclusion_sensitivity.csv");
  const stabilityProjectedRows = readSensitivity("stability_projected_sensitivity.csv");
  const stablePair = stabilityRow(stabilityExclusionRows, "Pair-level coefficient", "Stable dates only");
  const stableDiff = stabilityRow(stabilityExclusionRows, "Evolving-minus-frozen aggregate difference", "Stable dates only");
  const projectedPair = stabilityRow(stabilityProjectedRows, "Pair-level coefficient", "Stability-projected path");
  const projectedDiff = stabilityRow(stabilityProjectedRows, "Evolving-minus-frozen aggregate difference", "Stability-projected path");
  const fmtNumber = (value, digits = 6) => (value === "" || value == null || Number.isNaN(Number(value)) ? "not estimable" : Number(value).toFixed(digits));
  const attenuation = summary.fixed_topology_benchmark?.attenuation_uncertainty?.quantities ?? {};
  const attenuationRatio = attenuation.frozen_evolving_ratio ?? {};
  const attenuationDifference = attenuation.attenuation_difference ?? {};
  const rcepAggregate = summary.rcep_aggregate_readout ?? {};
  const fmtInterval = (row, scale = 1, digits = 1) => {
    if (!row || row.p025 == null || row.p975 == null) return "not estimable";
    return `${(scale * Number(row.p025)).toFixed(digits)}-${(scale * Number(row.p975)).toFixed(digits)}`;
  };
  const fmtRange = (values, digits = 3, multiplier = 1) => values
    .filter((x) => x !== null && x !== undefined && Number.isFinite(Number(x)))
    .map((x) => (multiplier * Number(x)).toFixed(digits))
    .join("-");
  const formatPValue = (value) => {
    if (value === "" || value == null || Number.isNaN(Number(value))) return "";
    const num = Number(value);
    if (num < 0.001) return "<0.001";
    return num.toFixed(3);
  };
  const meta = readJson(path.join(ROOT, "manuscript_src", "natcs", "metadata.json"));
  return {
    title: meta.title || "Recovering topology-specific propagation in evolving weighted networks",
    baseline_coef_gain_range: [synth.baseline_small_coef_gain_pct, synth.baseline_large_coef_gain_pct].sort((a, b) => a - b).map((x) => Number(x).toFixed(1)).join("-"),
    baseline_girf_gain_range: [synth.baseline_small_girf_gain_pct, synth.baseline_large_girf_gain_pct].sort((a, b) => a - b).map((x) => Number(x).toFixed(1)).join("-"),
    baseline_coef_gain_replicated_range: [synth.baseline_small_coef_gain_pct, synth.baseline_medium_coef_gain_pct]
      .sort((a, b) => a - b).map((x) => Number(x).toFixed(1)).join("-"),
    baseline_girf_gain_replicated_range: [synth.baseline_small_girf_gain_pct, synth.baseline_medium_girf_gain_pct]
      .sort((a, b) => a - b).map((x) => Number(x).toFixed(1)).join("-"),
    baseline_coef_gain_n50: Number(gainFor("Scale baseline (T=240, N=50)", "Effective-operator error")).toFixed(1),
    baseline_girf_gain_n50: Number(gainFor("Scale baseline (T=240, N=50)", "GIRF error")).toFixed(1),
    synthetic_scenario_count: synth.scenario_count ?? "",
    scale_replications_min: synth.scale_replications_min ?? "",
    scale_replications_n15: synth.scale_replications?.scale_n15 ?? "",
    scale_replications_n30: synth.scale_replications?.scale_n30 ?? "",
    scale_replications_n50: synth.scale_replications?.scale_n50 ?? "",
    baseline_coef: Number(summary.baseline_association?.coefficient ?? 0).toFixed(6),
    baseline_se: Number(summary.baseline_association?.standard_error ?? 0).toFixed(6),
    effect_for_iqr: Number(summary.effect_size_translation?.effect_for_iqr ?? 0).toFixed(4),
    effect_pct_mean: Number(summary.effect_size_translation?.effect_pct_of_mean ?? 0).toFixed(1),
    frozen_coef: Number(summary.fixed_topology_benchmark?.frozen_topology_coefficient ?? 0).toFixed(6),
    frozen_p: Number(summary.fixed_topology_benchmark?.frozen_topology_p_value ?? 0).toFixed(3),
    frozen_ratio_pct: (100 * Number(summary.fixed_topology_benchmark?.coef_ratio_vs_evolving ?? 0)).toFixed(1),
    frozen_ratio_ci_pct: fmtInterval(attenuationRatio, 100, 1),
    frozen_ratio_bootstrap_draws: summary.fixed_topology_benchmark?.attenuation_uncertainty?.bootstrap_replications ?? "",
    attenuation_difference: Number(summary.fixed_topology_benchmark?.attenuation ?? 0).toFixed(6),
    attenuation_difference_ci: fmtInterval(attenuationDifference, 1, 6),
    pre_g_net: Number(summary.aggregate_bootstrap_shift?.pre_2022_g_net_p50_mean ?? 0).toFixed(2),
    post_g_net: Number(summary.aggregate_bootstrap_shift?.post_2022_g_net_p50_mean ?? 0).toFixed(2),
    rcep_pre_point_difference: Number(rcepAggregate.pre_2022?.point_mean_observed_minus_frozen ?? 0).toFixed(5),
    rcep_post_point_difference: Number(rcepAggregate.post_2022?.point_mean_observed_minus_frozen ?? 0).toFixed(5),
    rcep_pre_bootstrap_difference: Number(rcepAggregate.pre_2022?.bootstrap_median_difference_mean ?? 0).toFixed(5),
    rcep_post_bootstrap_difference: Number(rcepAggregate.post_2022?.bootstrap_median_difference_mean ?? 0).toFixed(5),
    rcep_pre_bootstrap_level: Number(rcepAggregate.pre_2022?.bootstrap_observed_level_median_mean ?? 0).toFixed(4),
    rcep_post_bootstrap_level: Number(rcepAggregate.post_2022?.bootstrap_observed_level_median_mean ?? 0).toFixed(4),
    girf_pre: Number(summary.girf_network_contribution?.["2018-12-31"]?.mean ?? 0).toFixed(2),
    girf_post: Number(summary.girf_network_contribution?.["2022-12-31"]?.mean ?? 0).toFixed(2),
    break_dates_main: String((summary.structural_breaks || [])[0]?.break_dates ?? "").replace(/;\s*/g, " and "),
    ridge_lambda: selection.ridge_lambda ?? "",
    cp_rank: selection.cp_rank ?? "",
    rolling_window: selection.window ?? 40,
    lag_order: selection.lag_order ?? 2,
    horizon_main: 8,
    horizon_alt: 12,
    bootstrap_draws: selection.bootstrap_replications ?? 500,
    bootstrap_block_size: selection.bootstrap_block_size ?? 4,
    cp_inits: selection.cp_inits ?? 6,
    cp_max_iter: selection.cp_max_iter ?? 100,
    cp_tol: selection.cp_tol ?? 1e-6,
    stability_rate_pct: (100 * Number(selection.stability_rate_cp ?? 0)).toFixed(1),
    pair_count: pairCount,
    date_count: dateCount,
    effective_sample: summary.baseline_association?.n ?? "",
    collapsed_operator_scale_effective_range: [synth.collapsed_scale_coef_error_min, synth.collapsed_scale_coef_error_max]
      .filter((x) => x !== null && x !== undefined && Number.isFinite(Number(x)))
      .map((x) => Number(x).toFixed(1))
      .join("-"),
    collapsed_operator_scale_girf_range: [synth.collapsed_scale_girf_error_min, synth.collapsed_scale_girf_error_max]
      .filter((x) => x !== null && x !== undefined && Number.isFinite(Number(x)))
      .map((x) => Number(x).toFixed(3))
      .join("-"),
    collapsed_operator_scale_failure_pct: (100 * Number(synth.collapsed_scale_failure_rate ?? 0)).toFixed(1),
    collapsed_operator_baseline_effective: simRow("Scale baseline (T=160, N=15)", "Collapsed-operator CP").effective ?? "",
    collapsed_operator_baseline_girf: simRow("Scale baseline (T=160, N=15)", "Collapsed-operator CP").girf ?? "",
    stable_pair_coef: fmtNumber(stablePair.Value, 6),
    stable_pair_se: fmtNumber(stablePair["Std.Err"], 6),
    stable_pair_p: formatPValue(stablePair["p-value"]),
    stable_topology_diff: fmtNumber(stableDiff.Value, 4),
    projected_pair_coef: fmtNumber(projectedPair.Value, 6),
    projected_pair_se: fmtNumber(projectedPair["Std.Err"], 6),
    projected_pair_p: formatPValue(projectedPair["p-value"]),
    projected_topology_diff: fmtNumber(projectedDiff.Value, 4),
    edge_missing_cp_effective: simRow("Missing observed network edges", "CP-network").effective ?? "",
    edge_missing_cp_girf: simRow("Missing observed network edges", "CP-network").girf ?? "",
    noisy_network_cp_effective: simRow("Noisy observed network weights", "CP-network").effective ?? "",
    noisy_network_cp_girf: simRow("Noisy observed network weights", "CP-network").girf ?? "",
    high_vol_cp_girf: simRow("High topology volatility", "CP-network").girf ?? "",
    high_vol_tucker_girf: simRow("High topology volatility", "Tucker-network").girf ?? "",
    edge_missing_tucker_girf: simRow("Missing observed network edges", "Tucker-network").girf ?? "",
    noisy_network_tucker_girf: simRow("Noisy observed network weights", "Tucker-network").girf ?? "",
    topology_stress_replications_min: synth.topology_stress_replications_min ?? "",
    cp_stress_girf_range: fmtRange([synth.cp_stress_girf_error_min, synth.cp_stress_girf_error_max], 3),
    tucker_stress_girf_range: fmtRange([synth.tucker_stress_girf_error_min, synth.tucker_stress_girf_error_max], 3),
    collapsed_stress_girf_range: fmtRange([synth.collapsed_stress_girf_error_min, synth.collapsed_stress_girf_error_max], 3),
    cp_stress_frozen_range: fmtRange([synth.cp_stress_frozen_error_min, synth.cp_stress_frozen_error_max], 3),
    tucker_stress_frozen_range: fmtRange([synth.tucker_stress_frozen_error_min, synth.tucker_stress_frozen_error_max], 3),
    cp_stress_instability_range: fmtRange([synth.cp_stress_instability_min, synth.cp_stress_instability_max], 1, 100),
    tucker_stress_instability_range: fmtRange([synth.tucker_stress_instability_min, synth.tucker_stress_instability_max], 1, 100),
    collapsed_stress_instability_range: fmtRange([synth.collapsed_stress_instability_min, synth.collapsed_stress_instability_max], 1, 100),
    tucker_stress_structural_defined: synth.tucker_stress_structural_defined ? "defined" : "not consistently defined",
    collapsed_stress_structural_undefined: synth.collapsed_stress_structural_undefined ? "undefined" : "partly defined",
    no_network_stress_structural_undefined: synth.no_network_stress_structural_undefined ? "undefined" : "partly defined",
    spectral_gap_gnet_spearman: fmtCorr(corr("spectral_gap_W", "g_net").spearman),
    spectral_gap_gnet_pearson: fmtCorr(corr("spectral_gap_W", "g_net").pearson),
    strength_gini_gnet_spearman: fmtCorr(corr("node_strength_gini", "g_net").spearman),
    import_exposure_gnet_spearman: fmtCorr(corr("import_exposure_gini", "g_net").spearman),
    directional_asymmetry_gnet_spearman: fmtCorr(corr("directional_asymmetry", "g_net").spearman),
    reciprocity_gnet_spearman: fmtCorr(corr("weighted_reciprocity", "g_net").spearman),
    spectral_effective_rank_gnet_spearman: fmtCorr(corr("spectral_effective_rank_W", "g_net").spearman),
    perturb_target_unit: perturb.dominant_target_unit ?? "",
    perturb_mean_gnet_delta: Number(perturb.mean_g_net_delta ?? 0).toFixed(3),
    perturb_median_gnet_delta: Number(perturb.median_g_net_delta ?? 0).toFixed(3),
    perturb_negative_share_pct: (100 * Number(perturb.share_delta_negative ?? 0)).toFixed(1),
    rcep_weak_median_eta: fmtWeak(weakSep("rcep").median_min_eigenvalue),
    rcep_weak_p01_eta: fmtWeak(weakSep("rcep").p01_min_eigenvalue),
    rcep_weak_flag_pct: fmtWeakPct(weakSep("rcep").weak_separation_flag_pct),
    rcep_weak_median_condition: Number(weakSep("rcep").median_condition_number ?? 0).toFixed(2),
    nyc_weak_median_eta: fmtWeak(weakSep("nyc_taxi").median_min_eigenvalue),
    nyc_weak_p01_eta: fmtWeak(weakSep("nyc_taxi").p01_min_eigenvalue),
    nyc_weak_flag_pct: fmtWeakPct(weakSep("nyc_taxi").weak_separation_flag_pct),
    nyc_weak_median_condition: Number(weakSep("nyc_taxi").median_condition_number ?? 0).toFixed(2),
    nyc_date_count: nyc.date_count ?? "",
    nyc_cp_rank: nyc.cp_rank ?? "",
    nyc_mean_gnet: Number(nyc.mean_g_net ?? 0).toFixed(3),
    nyc_mean_frozen_gnet: Number(nyc.mean_frozen_g_net ?? 0).toFixed(3),
    nyc_mean_topology_difference: Number(nyc.mean_topology_difference ?? 0).toFixed(3),
    nyc_mean_topology_difference_4: Number(nyc.mean_topology_difference ?? 0).toFixed(4),
    nyc_early_girf_label: nyc.early_girf_label ?? "",
    nyc_late_girf_label: nyc.late_girf_label ?? "",
    nyc_early_network_share_median: Number(nyc.early_network_share?.median ?? 0).toFixed(3),
    nyc_late_network_share_median: Number(nyc.late_network_share?.median ?? 0).toFixed(3),
    nyc_early_network_share_mean: Number(nyc.early_network_share?.mean ?? 0).toFixed(3),
    nyc_late_network_share_mean: Number(nyc.late_network_share?.mean ?? 0).toFixed(3),
    nyc_stability_rate_pct: Number(nyc.stability_rate_pct ?? 0).toFixed(1),
    nyc_turnover_gnet_spearman: fmtCorr(nycCorr("weight_turnover").spearman),
    nyc_effective_rank_gnet_spearman: fmtCorr(nycCorr("spectral_effective_rank_W").spearman),
    nyc_top3_incoming_gnet_spearman: fmtCorr(nycCorr("top3_incoming_share").spearman),
    nyc_incoming_gini_gnet_spearman: fmtCorr(nycCorr("incoming_gini").spearman),
    nyc_directional_asymmetry_gnet_spearman: fmtCorr(nycCorr("directional_asymmetry").spearman),
  };
}

function copyRenderedManuscriptSource(destRoot) {
  const context = computeReviewerTemplateContext();
  copyTree(
    SRC_ROOT,
    destRoot,
    (src) => (src.endsWith(".md") || src.endsWith(".txt") || src.endsWith(".bib") || src.endsWith(".csl")) && !src.endsWith("metadata.json")
  );
  if (!Object.keys(context).length) return;
  const renderable = [];
  const walk = (dir) => {
    for (const entry of fs.readdirSync(dir)) {
      const current = path.join(dir, entry);
      const stat = fs.lstatSync(current);
      if (stat.isDirectory()) walk(current);
      else if ([".md", ".txt"].includes(path.extname(current).toLowerCase())) renderable.push(current);
    }
  };
  walk(destRoot);
  for (const file of renderable) {
    const text = fs.readFileSync(file, "utf8");
    fs.writeFileSync(file, renderTemplate(text, context), "utf8");
  }
}

function buildReadme() {
  return [
    "# NatCS Reviewer Archive",
    "",
    "This reviewer archive contains sanitized manuscript source, build code, derived reproducibility objects, environment snapshots and shell scripts for regenerating the manuscript-facing evidence bundle during peer review.",
    "",
    "The computational target is query preservation for topology-substitution responses: the shipped evidence supports endpoint availability and recovery for a topology-switchable operator with observed, zero-network and frozen-topology readouts. CP is the benchmark implementation layer, not the reusable object claimed by the manuscript.",
    "",
    "## Contents",
    "",
    "- `code/`: build scripts, manuscript source, operator-recovery benchmark code, empirical CP implementation scripts and the derived outputs required for review.",
    "- `environment/`: Python package lockfile, Node runtime note and tool-version snapshot from the build machine.",
    "- `reproduce/`: shell scripts for the evidence bundle and sanitized manuscript build.",
    "- `data_access/`: acquisition notes for raw inputs that are not redistributed in this archive.",
    "- `manifest.json`: inventory, exact reproduction commands, stochastic settings and SHA-256 checksums for archive files.",
    "",
    "## Quick start",
    "",
    "1. Inspect the reader-facing evidence first: `code/output/natcs_evidence/reader_facing_evidence_summary.md`, `code/output/natcs_evidence/evidence_support_map.json`, and the manuscript-facing `table*.md` files use paper terminology. `evidence_support_map.json` is the canonical evidence map; `claim_evidence_map.json` is a compatibility alias with identical contents. `summary_metrics.json` and raw CSV files remain machine-readable sources for exact reproduction.",
    "2. Use the supplied evidence-reproduction entry point to regenerate the manuscript-facing evidence bundle from the derived review objects shipped in `code/output/`.",
    "3. Use the supplied manuscript-reproduction entry point to regenerate the sanitized manuscript and Supplementary Information on a manuscript-build host with `pandoc`, `latexmk`, and `pdftoppm` available locally. `environment/tool_versions.json` records the archive-packaging host, not a validated clean manuscript-rebuild host.",
    "4. Compare regenerated outputs under `code/output/` with the files listed in `manifest.json` and `code/output/natcs_evidence/evidence_support_map.json`.",
    "5. The default reviewer path starts from derived evidence objects and does not require access to the restricted raw trade-data acquisition workspace.",
    "",
    "## Reviewer rebuild modes",
    "",
    "Fast reviewer rebuild: use the default entry points, which use reduced bootstrap draws while exercising the same code path.",
    "",
    "Full-output artifact rebuild: use the supplied full-output entry points at the submitted 500-draw bootstrap setting. When matching full CP outputs are shipped, they regenerate manuscript-facing artifacts from the archived full-output bundle; they do not by themselves force a fresh empirical CP rerun.",
    "",
    "Fresh full empirical rerun: use the documented fresh-rerun mode to recompute the CP empirical layer with the submitted bootstrap setting. Differences between fast, full-output and fresh-rerun modes reflect bootstrap resolution or cache scope, not a change in estimator.",
    "",
    "The synthetic benchmark table includes local rolling, CP, Tucker, no-network low-rank, sparse-network, graph-convolution, graph-neural, diffusion graph and recurrent graph-filter comparators. Sparse-network, graph-convolution, graph-neural, diffusion-graph and recurrent graph-filter rows are projection-based stress comparators for the submitted topology-response readouts; they are not native forecasting benchmarks. These outputs are shipped precomputed. The default reproduction path reuses the shipped benchmark summaries unless the rebuild flag is set.",
    "",
    "Fast benchmark smoke rerun: use the documented benchmark-rerun mode.",
    "",
    "Submission-grade benchmark rerun: use the documented 20-replication scale and stress settings with the submitted bootstrap setting. This is substantially slower than the default evidence rebuild because it recomputes the scale, stress and recurrent graph-filter comparisons. N=50 graph-feature rows remain one-rep bounded stress outputs, as reported in Supplementary Table 3.",
    "",
    "Entry points, modes, bootstrap settings, per-draw CP fitting settings and random-seed conventions are listed in `manifest.json`.",
    "",
    "## Data boundary",
    "",
    "This archive is evidence-complete, not raw-data-complete. It includes the derived panels, time-indexed network objects, benchmark summaries, bootstrap outputs, figures and manuscript-facing evidence tables needed to inspect the submitted claims. Raw IMF, tariff, bilateral trade and licensed MRIO inputs are documented in `data_access/restricted_data_instructions.md` because their redistribution is controlled by upstream providers. Raw-to-derived rebuilds are not self-contained in this archive: in addition to upstream data access, they require a non-redistributed RCEP helper location supplied through `NATCS_RCEP_HELPER_REPO` and a public NYC Taxi dataset location supplied through `NATCS_NYC_TAXI_DATASET_DIR`. Those raw inputs are required only to rebuild the raw-to-derived construction layer, not to inspect the submitted tables and figures.",
    "",
  ].join("\n");
}

function buildRestrictedDataNote() {
  return [
    "# Restricted Data Acquisition Notes",
    "",
    "The reviewer archive redistributes derived trade and mobility panels, benchmark summaries, CP empirical outputs, manuscript-facing evidence tables and generated figures that are sufficient to inspect the reported figures and tables.",
    "The default reproduction scripts start from these derived objects. Access to the restricted raw trade-data acquisition workspace is not required to regenerate the manuscript-facing evidence bundle during peer review.",
    "",
    "The raw-source boundary is recorded at the source-block level:",
    "",
    "| Source block | Provider/source recorded in the manuscript materials | Raw access status | Manuscript use | Reviewer archive substitute |",
    "|---|---|---|---|---|",
    "| Quarterly macro indicators | IMF International Financial Statistics and national statistical offices | Raw files are not redistributed because provider access and reuse terms still apply | RCEP quarterly outcome panel | Derived quarterly panel and acquisition notes |",
    "| Bilateral trade weights | UN Comtrade extracts, with documented BACI, WITS, OEC and Atlas fallback/cross-check slots | Raw exports and fallback files are not recursively redistributed | Import-share network matrices and source cross-checks | Derived network matrices and source-coverage summaries |",
    "| Tariff schedules | Official RCEP tariff schedules and bilateral import records | Raw schedule and bilateral source files remain subject to upstream access terms | Tariff-relief regressor and pair-level descriptive association design | Derived tariff-relief panel and association outputs |",
    "| MRIO-derived exposure inputs | Annual multi-regional input-output information used for value-added trade proxies | Licensed or otherwise restricted inputs are not bundled | Quarterlyized value-added exposure proxies and robustness inputs | Derived exposure variables and robustness summaries |",
    "| NYC Taxi mobility operator check | `xinychen/vars` commit `7e63ba9734021171eaf49edb92be8a7e7e8802eb`, path `datasets/NYC-taxi`; NYC Taxi and Limousine Commission portal | Public upstream route is recorded; the derived monthly panel is redistributed for review | Public second-domain aggregate, frozen-topology and impulse-response operator check | Derived monthly mobility panel, acquisition JSON and operator-check table |",
    "",
    "The public NYC Taxi operator check is represented here by a derived monthly panel together with the upstream repository revision and acquisition note shipped in `code/output/natcs_empirical_cp/nyc_taxi/`.",
    "Raw-to-derived rebuilds are not self-contained in this archive. In addition to upstream data access, they require `NATCS_RCEP_HELPER_REPO` for the non-redistributed RCEP helper and `NATCS_NYC_TAXI_DATASET_DIR` for the public NYC Taxi dataset directory.",
    "The code paths that consume restricted trade inputs are documented in the submitted source scripts, but the raw acquisition workspace and helper checkouts are not recursively redistributed in this archive. Those raw inputs are required only for a raw-to-derived reconstruction of the trade panel and network matrices. On acceptance, the authors will deposit the redistributable code-and-derived-evidence release in a DOI-minting repository and update the public-release record with the assigned persistent identifier, licence and access terms.",
    "",
  ].join("\n");
}

function buildEnvironmentSnapshot() {
  ensureDir(ENV_ROOT);
  const pipFreeze = commandOutput("python3", ["-m", "pip", "freeze"]) || "# python3 -m pip freeze failed on the build machine";
  writeText(path.join(ENV_ROOT, "python-requirements-lock.txt"), `${pipFreeze}\n`);

  const npmVersion = commandOutput("npm", ["--version"]) || "unavailable";
  const dependencyStatus = dependencyManifestStatus();
  writeText(path.join(ENV_ROOT, "node-environment.txt"), [
    "# Node Runtime Environment",
    "",
    `node: ${process.version}`,
    `npm: ${npmVersion}`,
    `platform: ${os.platform()} ${os.release()} ${os.arch()}`,
    `dependency_manifest_files: ${dependencyStatus.present.length ? dependencyStatus.present.join(", ") : "none found"}`,
    "",
    dependencyStatus.note,
    "",
  ].join("\n"));

  const toolVersions = {
    node: process.version,
    npm: npmVersion,
    python3: commandOutput("python3", ["--version"]) || "unavailable",
    pandoc: commandOutput("pandoc", ["--version"])?.split("\n")[0] || "unavailable",
    latexmk: commandOutput("latexmk", ["-v"])?.split("\n")[0] || "unavailable",
    pdftoppm: commandOutput("pdftoppm", ["-v"])?.split("\n")[0] || "unavailable",
    platform: {
      os: os.platform(),
      release: os.release(),
      arch: os.arch(),
    },
    node_dependency_manifest: dependencyStatus,
    generated_at: new Date().toISOString(),
  };
  writeJson(path.join(ENV_ROOT, "tool_versions.json"), toolVersions);
}

function writeReproductionScripts() {
  ensureDir(REPRO_ROOT);
  const evidenceScript = [
    "#!/usr/bin/env bash",
    "set -euo pipefail",
    "cd \"$(dirname \"$0\")/../code\"",
    "# By default this rebuild reuses shipped benchmark summaries and derived CP objects.",
    "# Set NATCS_REBUILD_BENCHMARKS=1 for a full synthetic benchmark rerun.",
    "NATCS_SKIP_REVIEWER_ARCHIVE=1 NATCS_CP_NBOOT=\"${NATCS_CP_NBOOT:-20}\" node scripts/build_natcs_evidence.mjs",
    "",
  ].join("\n");
  const manuscriptScript = [
    "#!/usr/bin/env bash",
    "set -euo pipefail",
    "cd \"$(dirname \"$0\")/../code\"",
    "for tool in pandoc latexmk pdftoppm; do",
    "  if ! command -v \"$tool\" >/dev/null 2>&1; then",
    "    echo \"Missing required manuscript-build tool: $tool\" >&2",
    "    echo \"The evidence rebuild does not require the PDF toolchain; use ./reproduce/reproduce_evidence.sh for the derived evidence path.\" >&2",
    "    exit 127",
    "  fi",
    "done",
    "NATCS_SKIP_REVIEWER_ARCHIVE=1 NATCS_CP_NBOOT=\"${NATCS_CP_NBOOT:-20}\" node scripts/build_natcs_manuscript.mjs",
    "",
  ].join("\n");
  const evidencePath = path.join(REPRO_ROOT, "reproduce_evidence.sh");
  const manuscriptPath = path.join(REPRO_ROOT, "reproduce_manuscript.sh");
  writeText(evidencePath, evidenceScript);
  writeText(manuscriptPath, manuscriptScript);
  fs.chmodSync(evidencePath, 0o755);
  fs.chmodSync(manuscriptPath, 0o755);
}

function cleanReviewerEvidenceNames() {
  const evidenceRoot = path.join(CODE_ROOT, "output", "natcs_evidence");
  const oldMap = path.join(evidenceRoot, "claim_evidence_map.json");
  const newMap = path.join(evidenceRoot, "evidence_support_map.json");
  if (fs.existsSync(oldMap) && !fs.existsSync(newMap)) {
    fs.copyFileSync(oldMap, newMap);
  } else if (fs.existsSync(newMap) && !fs.existsSync(oldMap)) {
    fs.copyFileSync(newMap, oldMap);
  }
}

function copyArchiveCode() {
  const meta = readJson(path.join(ROOT, "manuscript_src", "natcs", "metadata.json"));
  const sanitizedMeta = sanitizeMetadata(meta);
  ensureDir(CODE_ROOT);
  fs.rmSync(path.join(CODE_ROOT, "output"), { recursive: true, force: true });
  fs.rmSync(path.join(CODE_ROOT, "output 2"), { recursive: true, force: true });

  copyFile(path.join(ROOT, "Makefile"), path.join(CODE_ROOT, "Makefile"));

  copyTree(
    path.join(ROOT, "scripts"),
    path.join(CODE_ROOT, "scripts"),
    (src) => /\.(mjs|py)$/.test(src)
      && !src.includes("__pycache__")
      && !src.endsWith("rebuild_natcs_docx.py")
      && path.basename(src) !== "natcs_evidence.py"
  );
  copyRenderedManuscriptSource(path.join(CODE_ROOT, "manuscript_src", "natcs"));
  writeJson(path.join(CODE_ROOT, "manuscript_src", "natcs", "metadata.json"), sanitizedMeta);

  copyTree(path.join(ROOT, "output", "natcs_benchmarks"), path.join(CODE_ROOT, "output", "natcs_benchmarks"), isCleanArchiveFile);
  copyTree(path.join(ROOT, "output", "natcs_empirical_cp"), path.join(CODE_ROOT, "output", "natcs_empirical_cp"), isCleanArchiveFile);
  copyTree(path.join(ROOT, "output", "natcs_evidence"), path.join(CODE_ROOT, "output", "natcs_evidence"), isCleanArchiveFile);
  cleanReviewerEvidenceNames();
}

function writeManifest() {
  const toolVersionsPath = path.join(ENV_ROOT, "tool_versions.json");
  const toolVersions = fs.existsSync(toolVersionsPath) ? readJson(toolVersionsPath) : {};
  const selectionSummary = (relativePath) => {
    const file = path.join(CODE_ROOT, relativePath);
    return fs.existsSync(file) ? readJson(file) : null;
  };
  const selectionSubset = (selection) => selection ? {
    bootstrap_replications: selection.bootstrap_replications,
    bootstrap_block_size: selection.bootstrap_block_size,
    cp_rank: selection.cp_rank,
    cp_inits: selection.cp_inits,
    cp_max_iter: selection.cp_max_iter,
    cp_tol: selection.cp_tol,
    window: selection.window,
    lag_order: selection.lag_order,
  } : null;
  const rcepSelection = selectionSummary(path.join("output", "natcs_empirical_cp", "rcep", "selection_summary.json"));
  const nycSelection = selectionSummary(path.join("output", "natcs_empirical_cp", "nyc_taxi", "selection_summary.json"));
  const manifest = {
    archive_root: ".",
    generated_at: new Date().toISOString(),
    package_role: "Separate reviewer reproducibility archive; keep outside the Word-only submission upload package.",
    computational_target: {
      object: "Topology-switchable finite-horizon response operator with observed, zero-network and frozen-topology readouts.",
      primary_claim: "Query preservation for topology-substitution responses in evolving weighted networks.",
      implementation_boundary: "CP is the benchmark and empirical implementation layer; the reusable target is endpoint availability and recovery for the topology-switchable operator.",
      review_scope: "Derived-evidence regeneration for manuscript-facing tables, figures, evidence maps and sanitized manuscript artifacts.",
      excluded_claims: [
        "raw-data-complete archive",
        "causal RCEP tariff-policy identification",
        "native temporal-GNN forecasting benchmark",
        "broad empirical domain generality",
        "latent-network recovery",
      ],
    },
    reproduction: {
      entrypoints: ["Evidence rebuild", "Manuscript rebuild"],
      modes: {
        quick_review: "Reduced-bootstrap code-path inspection.",
        full_output_artifact_rebuild: "Rebuild from shipped derived and full-output objects at the submitted 500-draw bootstrap setting.",
        fresh_empirical_rerun: "Fresh CP empirical rerun under the submitted bootstrap setting.",
        benchmark_rerun: "Synthetic benchmark rerun using the replication settings recorded below.",
      },
      manuscript_build_host_note: "`environment/tool_versions.json` records the archive-packaging host, not a validated clean manuscript-rebuild host. PDF regeneration requires pandoc, latexmk and pdftoppm.",
      evidence_map: {
        canonical: "code/output/natcs_evidence/evidence_support_map.json",
        alias: "code/output/natcs_evidence/claim_evidence_map.json",
        alias_note: "Compatibility alias with identical contents.",
      },
      comparator_scope_note: "Sparse-network, graph-convolution, graph-neural, diffusion-graph and recurrent graph-filter rows are projection-based stress comparators for the submitted topology-response readouts; they are not native forecasting benchmarks.",
      cache_scope_note: "The full-output artifact mode regenerates manuscript-facing artifacts from shipped full outputs when those outputs are present; the fresh empirical mode recomputes the CP layer.",
      raw_to_derived_boundary_note: "Raw-to-derived rebuilds are not self-contained in this archive; they require upstream data access, NATCS_RCEP_HELPER_REPO for the non-redistributed RCEP helper and NATCS_NYC_TAXI_DATASET_DIR for the public NYC Taxi dataset directory.",
      default_review_environment: {
        NATCS_SKIP_REVIEWER_ARCHIVE: "1",
        NATCS_CP_NBOOT: "20",
      },
      key_environment_variables: {
        NATCS_CP_NBOOT: "Number of moving-block bootstrap replications requested by build_natcs_evidence.mjs; reviewer scripts default to 20, final evidence uses 500.",
        NATCS_CP_BLOCK_SIZE: "Moving-block bootstrap block size; default is 4.",
        NATCS_WINDOW: "Rolling estimation window; default is 40.",
        NATCS_P: "VAR lag order; default is 2.",
        NATCS_CP_INITS: "CP-ALS random initializations; default is 6.",
        NATCS_CP_MAX_ITER: "Maximum CP-ALS iterations per initialization; default is 100.",
        NATCS_CP_TOL: "CP-ALS relative tolerance; default is 1e-6.",
        NATCS_REBUILD_CP: "Set to 1 to force CP empirical outputs to rebuild instead of reusing matching shipped outputs.",
        NATCS_RCEP_HELPER_REPO: "Authorized, non-redistributed RCEP helper location required only for raw-to-derived rebuilding.",
        NATCS_NYC_TAXI_DATASET_DIR: "Public NYC Taxi dataset directory required only for raw-to-derived rebuilding.",
        NATCS_REBUILD_BENCHMARKS: "Set to 1 to rerun the synthetic benchmark table instead of reusing shipped benchmark summaries.",
        NATCS_BENCHMARK_SCALE_REPS: "Synthetic scale-scenario replications; reviewer smoke default is 3, while the submission-grade rerun for the N=15/N=30 recovery rows uses 20.",
        NATCS_BENCHMARK_STRESS_REPS: "Synthetic topology-stress replications; reviewer smoke default is 3, while the submission-grade rerun uses 20 for the stress rows.",
        NATCS_ATTENUATION_BOOT: "Conditional pair-cluster attenuation bootstrap replications; default is 2000.",
      },
      bootstrap_settings_from_shipped_selection_summaries: {
        rcep: selectionSubset(rcepSelection),
        nyc_taxi: selectionSubset(nycSelection),
      },
      stochastic_settings: [
        "run_cp_empirical_pipeline.py uses CP initialization seed 20260328.",
        "run_cp_empirical_pipeline.py uses moving-block bootstrap RNG seed 20260328 and CP re-estimation seeds 20260328 + bootstrap_index.",
        "The moving-block bootstrap re-estimation layer uses fixed per-draw CP settings n_init=4, max_iter=80 and tol=1e-5.",
        "natcs_benchmarks.mjs starts non-extend benchmark replications at seed 20260328; extend mode derives seeds from scenario and replication labels.",
        "build_rcep_attenuation_uncertainty.mjs uses conditional pair-cluster bootstrap seed 20260611.",
      ],
      bootstrap_reestimation_cp_settings: {
        n_init: 4,
        max_iter: 80,
        tol: 1e-5,
        note: "Per-draw CP fit budget for the moving-block bootstrap re-estimation layer; main fitted paths use the defaults recorded in the shipped selection summaries.",
      },
    },
    environment: {
      tool_versions: toolVersions,
      python_lockfile: "environment/python-requirements-lock.txt",
      node_runtime_note: "environment/node-environment.txt",
    },
    includes: {
      code: [
        "scripts",
        "manuscript_src/natcs",
        "output/natcs_benchmarks",
        "output/natcs_empirical_cp",
        "output/natcs_evidence",
      ],
      environment: [
        "python-requirements-lock.txt",
        "node-environment.txt",
        "tool_versions.json",
      ],
      reproduce: [
        "reproduce_evidence.sh",
        "reproduce_manuscript.sh",
      ],
      data_access: [
        "restricted_data_instructions.md",
      ],
    },
    checksums: {
      algorithm: "sha256",
      excluded_files: ["manifest.json"],
      files: archiveChecksums(),
    },
  };
  writeJson(path.join(ARCHIVE_ROOT, "manifest.json"), manifest);
}

export function cleanupNatcsReviewerArchive() {
  for (let pass = 0; pass < 5; pass += 1) {
    mergeNumberedSiblings(ARCHIVE_ROOT);
    removeArchiveJunkRecursive(ARCHIVE_ROOT);
    if (!findArchiveJunk(ARCHIVE_ROOT).length) break;
  }
  assertArchiveClean();
}

function mergeNumberedSiblings(root) {
  if (!fs.existsSync(root)) return;
  for (const entry of fs.readdirSync(root)) {
    const current = path.join(root, entry);
    if (!fs.lstatSync(current).isDirectory()) continue;
    if (hasNumberedDuplicateSuffix(entry)) {
      const dest = path.join(root, entry.replace(/ \d+$/, ""));
      mergeArchiveTree(current, dest);
      fs.rmSync(current, { recursive: true, force: true });
      mergeNumberedSiblings(dest);
      continue;
    }
    mergeNumberedSiblings(current);
  }
}

function mergeArchiveTree(src, dest) {
  if (!fs.existsSync(src)) return;
  const stat = fs.statSync(src);
  if (stat.isDirectory()) {
    ensureDir(dest);
    for (const entry of fs.readdirSync(src)) {
      mergeArchiveTree(path.join(src, entry), path.join(dest, entry));
    }
    return;
  }
  if (isCleanArchiveFile(src)) copyFile(src, dest);
}

function removeArchiveJunkRecursive(root) {
  if (!fs.existsSync(root)) return;
  for (const entry of fs.readdirSync(root)) {
    const current = path.join(root, entry);
    if (hasNumberedDuplicateSuffix(entry) || entry === ".DS_Store") {
      fs.rmSync(current, { recursive: true, force: true });
      continue;
    }
    const stat = fs.lstatSync(current);
    if (stat.isDirectory()) removeArchiveJunkRecursive(current);
  }
}

function findArchiveJunk(root, hits = []) {
  if (!fs.existsSync(root)) return hits;
  for (const entry of fs.readdirSync(root)) {
    const current = path.join(root, entry);
    if (hasNumberedDuplicateSuffix(entry) || entry === ".DS_Store") {
      hits.push(path.relative(ROOT, current));
      continue;
    }
    const stat = fs.lstatSync(current);
    if (stat.isDirectory()) findArchiveJunk(current, hits);
  }
  return hits;
}

function assertArchiveClean() {
  const junk = findArchiveJunk(ARCHIVE_ROOT);
  if (junk.length) {
    throw new Error(`Reviewer archive contains duplicate or platform junk paths:\n${junk.join("\n")}`);
  }
  const required = [
    path.join(CODE_ROOT, "scripts", "build_natcs_evidence.mjs"),
    path.join(CODE_ROOT, "scripts", "natcs_weak_separation.py"),
    path.join(CODE_ROOT, "scripts", "natcs_nyc_mechanisms.py"),
    path.join(CODE_ROOT, "output", "natcs_evidence", "reader_facing_evidence_summary.md"),
    path.join(CODE_ROOT, "output", "natcs_evidence", "evidence_support_map.json"),
    path.join(CODE_ROOT, "output", "natcs_evidence", "reader_facing_summary_metrics.json"),
    path.join(CODE_ROOT, "output", "natcs_evidence", "summary_metrics.json"),
    path.join(CODE_ROOT, "output", "natcs_evidence", "table2d_rcep_stability_qualified_readouts.csv"),
    path.join(CODE_ROOT, "output", "natcs_evidence", "table2d_rcep_stability_qualified_readouts.md"),
    path.join(CODE_ROOT, "output", "natcs_empirical_cp", "weak_separation_summary.csv"),
    path.join(CODE_ROOT, "output", "natcs_empirical_cp", "nyc_taxi", "nyc_network_mechanism_correlations.csv"),
    path.join(CODE_ROOT, "output", "natcs_empirical_cp", "nyc_taxi", "figures", "fig_nyc_network_mechanisms.pdf"),
    path.join(CODE_ROOT, "output", "natcs_benchmarks", "benchmark_summary.csv"),
  ];
  const missing = required.filter((file) => !fs.existsSync(file)).map((file) => path.relative(ROOT, file));
  if (missing.length) {
    throw new Error(`Reviewer archive is missing required reproducibility paths:\n${missing.join("\n")}`);
  }
  const legacyEvidenceHelper = path.join(CODE_ROOT, "scripts", "natcs_evidence.py");
  if (fs.existsSync(legacyEvidenceHelper)) {
    throw new Error("Reviewer archive contains legacy scripts/natcs_evidence.py with superseded claim wording");
  }
  const legacyPatterns = [
    ["Network Time-Varying Parameter", "Vector Autoregression Models", "CP Tensor Decomposition"].join(" "),
    ["Figure1", "network_tvp_var", "framework_redesign"].join("_"),
  ];
  const legacyHits = [];
  const scanLegacy = (dir) => {
    if (!fs.existsSync(dir)) return;
    for (const entry of fs.readdirSync(dir)) {
      const current = path.join(dir, entry);
      if (legacyPatterns.some((pattern) => entry.includes(pattern))) {
        legacyHits.push(path.relative(ROOT, current));
      }
      if (fs.lstatSync(current).isFile()) {
        if (entry === "build_natcs_reviewer_archive.mjs") continue;
        const ext = path.extname(current).toLowerCase();
        if ([".md", ".mjs", ".py", ".json", ".txt"].includes(ext)) {
          const body = fs.readFileSync(current, "utf8");
          if (legacyPatterns.some((pattern) => body.includes(pattern))) {
            legacyHits.push(`${path.relative(ROOT, current)} (content)`);
          }
        }
      }
      if (fs.lstatSync(current).isDirectory()) scanLegacy(current);
    }
  };
  scanLegacy(ARCHIVE_ROOT);
  if (legacyHits.length) {
    throw new Error(`Reviewer archive contains legacy manuscript assets:\n${legacyHits.join("\n")}`);
  }
}

function writeReviewerArchiveZip() {
  fs.rmSync(ARCHIVE_ZIP, { force: true });
  const result = spawnSync(
    "/usr/bin/zip",
    ["-q", "-r", "-X", ARCHIVE_ZIP, path.basename(ARCHIVE_ROOT)],
    { cwd: ARCHIVE_PARENT, encoding: "utf8" }
  );
  if (result.status !== 0) {
    throw new Error(`Could not create reviewer archive ZIP: ${(result.stderr || result.stdout || "").trim()}`);
  }
  return ARCHIVE_ZIP;
}

function removeGeneratedReviewerSiblings() {
  if (!fs.existsSync(ARCHIVE_PARENT)) return;
  const base = path.basename(ARCHIVE_ROOT);
  const duplicatePattern = new RegExp(`^${base.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")} \\d+$`);
  for (const entry of fs.readdirSync(ARCHIVE_PARENT)) {
    if (duplicatePattern.test(entry)) {
      fs.rmSync(path.join(ARCHIVE_PARENT, entry), { recursive: true, force: true });
    }
  }
}

export function buildNatcsReviewerArchive() {
  removeGeneratedReviewerSiblings();
  fs.rmSync(ARCHIVE_ROOT, { recursive: true, force: true });
  ensureDir(ARCHIVE_ROOT);
  copyArchiveCode();
  buildEnvironmentSnapshot();
  writeReproductionScripts();
  ensureDir(DATA_ROOT);
  writeText(path.join(ARCHIVE_ROOT, "README.md"), buildReadme());
  writeText(path.join(DATA_ROOT, "restricted_data_instructions.md"), buildRestrictedDataNote());
  writeManifest();
  cleanupNatcsReviewerArchive();
  removeGeneratedReviewerSiblings();
  writeReviewerArchiveZip();
  return ARCHIVE_ROOT;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  console.log(buildNatcsReviewerArchive());
}
