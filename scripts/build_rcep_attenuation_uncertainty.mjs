import path from "path";
import { readCsv, writeCsv, writeJson } from "./natcs_utils.mjs";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const RCEP_DIR = path.join(ROOT, "output", "natcs_empirical_cp", "rcep");
const PANEL_PATH = path.join(RCEP_DIR, "pairwise_cp_panel.csv");
const DRAW_PATH = path.join(RCEP_DIR, "frozen_attenuation_bootstrap.csv");
const SUMMARY_PATH = path.join(RCEP_DIR, "frozen_attenuation_bootstrap_summary.json");
const SUMMARY_CSV_PATH = path.join(RCEP_DIR, "frozen_attenuation_bootstrap_summary.csv");
const N_BOOT = Number(process.env.NATCS_ATTENUATION_BOOT || "2000");

function rng(seed) {
  let state = seed >>> 0;
  return () => {
    state = (1664525 * state + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function mean(values) {
  return values.reduce((sum, value) => sum + value, 0) / Math.max(values.length, 1);
}

function quantile(values, p) {
  const clean = values.filter((value) => Number.isFinite(value)).sort((a, b) => a - b);
  if (!clean.length) return NaN;
  const idx = (clean.length - 1) * p;
  const lo = Math.floor(idx);
  const hi = Math.ceil(idx);
  if (lo === hi) return clean[lo];
  return clean[lo] * (hi - idx) + clean[hi] * (idx - lo);
}

function twoWaySlope(rows) {
  const pairStats = new Map();
  const dateStats = new Map();
  let xTotal = 0;
  let yTotal = 0;

  for (const row of rows) {
    const x = Number(row.TC_relief);
    const y = Number(row.s_net_clip);
    xTotal += x;
    yTotal += y;

    if (!pairStats.has(row.draw_pair)) pairStats.set(row.draw_pair, { x: 0, y: 0, n: 0 });
    const pair = pairStats.get(row.draw_pair);
    pair.x += x;
    pair.y += y;
    pair.n += 1;

    const date = String(row.date);
    if (!dateStats.has(date)) dateStats.set(date, { x: 0, y: 0, n: 0 });
    const dateStat = dateStats.get(date);
    dateStat.x += x;
    dateStat.y += y;
    dateStat.n += 1;
  }

  const xMean = xTotal / Math.max(rows.length, 1);
  const yMean = yTotal / Math.max(rows.length, 1);
  for (const stat of pairStats.values()) {
    stat.x /= Math.max(stat.n, 1);
    stat.y /= Math.max(stat.n, 1);
  }
  for (const stat of dateStats.values()) {
    stat.x /= Math.max(stat.n, 1);
    stat.y /= Math.max(stat.n, 1);
  }

  let numerator = 0;
  let denominator = 0;
  for (const row of rows) {
    const pair = pairStats.get(row.draw_pair);
    const date = dateStats.get(String(row.date));
    const xResidual = Number(row.TC_relief) - pair.x - date.x + xMean;
    const yResidual = Number(row.s_net_clip) - pair.y - date.y + yMean;
    numerator += xResidual * yResidual;
    denominator += xResidual * xResidual;
  }
  return numerator / Math.max(denominator, 1e-12);
}

function rowsForVariant(rows, variantKey, pairLabel = "pair") {
  return rows
    .filter((row) => row.variant_key === variantKey && Number(row.H) === 8)
    .map((row) => ({
      ...row,
      draw_pair: row[pairLabel] ?? row.pair,
    }));
}

function summarizeQuantity(name, point, draws) {
  return {
    quantity: name,
    point,
    mean: mean(draws),
    p025: quantile(draws, 0.025),
    p50: quantile(draws, 0.5),
    p975: quantile(draws, 0.975),
  };
}

function main() {
  const allRows = readCsv(PANEL_PATH);
  const evolvingRows = rowsForVariant(allRows, "baseline_import");
  const frozenRows = rowsForVariant(allRows, "fixed_pre");
  const pairIds = [...new Set(evolvingRows.map((row) => row.pair))].sort();
  const dates = [...new Set(evolvingRows.map((row) => String(row.date)))].sort();
  const evolvingByPair = new Map(pairIds.map((pair) => [pair, evolvingRows.filter((row) => row.pair === pair)]));
  const frozenByPair = new Map(pairIds.map((pair) => [pair, frozenRows.filter((row) => row.pair === pair)]));

  const pointEvolving = twoWaySlope(evolvingRows);
  const pointFrozen = twoWaySlope(frozenRows);
  const pointDifference = pointEvolving - pointFrozen;
  const pointRatio = pointFrozen / Math.max(pointEvolving, 1e-12);
  const next = rng(20260611);
  const draws = [];

  for (let b = 1; b <= N_BOOT; b += 1) {
    const evolvingSample = [];
    const frozenSample = [];
    for (let i = 0; i < pairIds.length; i += 1) {
      const sampledPair = pairIds[Math.floor(next() * pairIds.length)];
      for (const row of evolvingByPair.get(sampledPair)) {
        evolvingSample.push({ ...row, draw_pair: `${i}_${sampledPair}` });
      }
      for (const row of frozenByPair.get(sampledPair)) {
        frozenSample.push({ ...row, draw_pair: `${i}_${sampledPair}` });
      }
    }
    const evolving = twoWaySlope(evolvingSample);
    const frozen = twoWaySlope(frozenSample);
    const difference = evolving - frozen;
    const ratio = frozen / Math.max(evolving, 1e-12);
    draws.push({
      draw: b,
      evolving_coefficient: evolving,
      frozen_coefficient: frozen,
      attenuation_difference: difference,
      frozen_evolving_ratio: ratio,
    });
  }

  const summary = {
    bootstrap_type: "conditional pair-cluster bootstrap on the reconstructed RCEP pair panel",
    bootstrap_replications: N_BOOT,
    cluster_unit: "ordered country pair",
    fixed_effects: "pair and date",
    horizon: 8,
    variants: {
      evolving: "baseline_import",
      frozen: "fixed_pre",
    },
    observations_per_variant: evolvingRows.length,
    pair_count: pairIds.length,
    date_count: dates.length,
    quantities: {
      evolving_coefficient: summarizeQuantity("evolving_coefficient", pointEvolving, draws.map((row) => row.evolving_coefficient)),
      frozen_coefficient: summarizeQuantity("frozen_coefficient", pointFrozen, draws.map((row) => row.frozen_coefficient)),
      attenuation_difference: summarizeQuantity("attenuation_difference", pointDifference, draws.map((row) => row.attenuation_difference)),
      frozen_evolving_ratio: summarizeQuantity("frozen_evolving_ratio", pointRatio, draws.map((row) => row.frozen_evolving_ratio)),
    },
    interpretation_note:
      "This interval conditions on the reconstructed CP coefficient path and quantifies joint second-stage uncertainty for the evolving and frozen pair-level regressions. It is not a full CP re-estimation bootstrap.",
  };

  writeCsv(DRAW_PATH, draws);
  writeJson(SUMMARY_PATH, summary);
  writeCsv(
    SUMMARY_CSV_PATH,
    Object.values(summary.quantities).map((row) => ({
      quantity: row.quantity,
      point: row.point,
      mean: row.mean,
      p025: row.p025,
      p50: row.p50,
      p975: row.p975,
      bootstrap_replications: N_BOOT,
      bootstrap_type: summary.bootstrap_type,
    }))
  );
  console.log(`Wrote ${DRAW_PATH}`);
  console.log(`Wrote ${SUMMARY_PATH}`);
}

main();
