import fs from "fs";
import path from "path";
import { ensureDir, readCsv, writeCsv } from "./natcs_utils.mjs";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const OUTPUT_DIR = process.env.NATCS_BENCHMARK_OUTPUT_DIR
  ? path.resolve(ROOT, process.env.NATCS_BENCHMARK_OUTPUT_DIR)
  : path.join(ROOT, "output", "natcs_benchmarks");
const SUMMARY_PATH = path.join(OUTPUT_DIR, "benchmark_summary.csv");
const DETAIL_PATH = path.join(OUTPUT_DIR, "benchmark_replications.csv");
const LEGACY_PATH = process.env.NATCS_BENCHMARK_OUTPUT_DIR
  ? path.join(OUTPUT_DIR, "monte_carlo_cp_network_tvp_var_results.csv")
  : path.join(ROOT, "monte_carlo_cp_network_tvp_var_results.csv");
const SCALE_REPLICATIONS = Number(process.env.NATCS_BENCHMARK_SCALE_REPS || "3");
const STRESS_REPLICATIONS = Number(process.env.NATCS_BENCHMARK_STRESS_REPS || "3");
const REP_START = process.env.NATCS_BENCHMARK_REP_START ? Number(process.env.NATCS_BENCHMARK_REP_START) : 1;
const REP_END = process.env.NATCS_BENCHMARK_REP_END ? Number(process.env.NATCS_BENCHMARK_REP_END) : null;
const CHECKPOINT = process.env.NATCS_BENCHMARK_CHECKPOINT !== "0";

const SCENARIOS = [
  { name: "scale_n15", label: "Scale baseline (T=160, N=15)", tLen: 160, n: 15, rankTrue: 2, rankEst: 2, window: 40, drift: "slow", topologyVol: 0.04, sparsity: 0.15, shockDist: "gaussian", wNoise: 0.0, replications: SCALE_REPLICATIONS, sigma: 0.03, horizon: 4 },
  { name: "scale_n30", label: "Scale baseline (T=200, N=30)", tLen: 200, n: 30, rankTrue: 2, rankEst: 2, window: 48, drift: "slow", topologyVol: 0.05, sparsity: 0.15, shockDist: "gaussian", wNoise: 0.0, replications: SCALE_REPLICATIONS, sigma: 0.03, horizon: 4 },
  { name: "scale_n50", label: "Scale baseline (T=240, N=50)", tLen: 240, n: 50, rankTrue: 2, rankEst: 2, window: 56, drift: "slow", topologyVol: 0.05, sparsity: 0.15, shockDist: "gaussian", wNoise: 0.0, replications: SCALE_REPLICATIONS, sigma: 0.03, horizon: 4 },
  { name: "rank_under", label: "Rank under-specification", tLen: 160, n: 15, rankTrue: 2, rankEst: 1, window: 40, drift: "slow", topologyVol: 0.04, sparsity: 0.15, shockDist: "gaussian", wNoise: 0.0, replications: STRESS_REPLICATIONS, sigma: 0.03, horizon: 4 },
  { name: "rank_over", label: "Rank over-specification", tLen: 160, n: 15, rankTrue: 2, rankEst: 3, window: 40, drift: "slow", topologyVol: 0.04, sparsity: 0.15, shockDist: "gaussian", wNoise: 0.0, replications: STRESS_REPLICATIONS, sigma: 0.03, horizon: 4 },
  { name: "abrupt_drift", label: "Abrupt coefficient drift", tLen: 160, n: 15, rankTrue: 2, rankEst: 2, window: 40, drift: "abrupt", topologyVol: 0.04, sparsity: 0.15, shockDist: "gaussian", wNoise: 0.0, replications: STRESS_REPLICATIONS, sigma: 0.03, horizon: 4 },
  { name: "high_topology_vol", label: "High topology volatility", tLen: 160, n: 15, rankTrue: 2, rankEst: 2, window: 40, drift: "slow", topologyVol: 0.18, sparsity: 0.15, shockDist: "gaussian", wNoise: 0.0, replications: STRESS_REPLICATIONS, sigma: 0.03, horizon: 4 },
  { name: "sparse_misspecified", label: "Sparse and misspecified network", tLen: 160, n: 15, rankTrue: 2, rankEst: 2, window: 40, drift: "slow", topologyVol: 0.08, sparsity: 0.55, shockDist: "gaussian", wNoise: 0.18, replications: STRESS_REPLICATIONS, sigma: 0.03, horizon: 4 },
  { name: "edge_missing", label: "Missing observed network edges", tLen: 160, n: 15, rankTrue: 2, rankEst: 2, window: 40, drift: "slow", topologyVol: 0.06, sparsity: 0.15, shockDist: "gaussian", wNoise: 0.0, wDrop: 0.30, replications: STRESS_REPLICATIONS, sigma: 0.03, horizon: 4 },
  { name: "noisy_network", label: "Noisy observed network weights", tLen: 160, n: 15, rankTrue: 2, rankEst: 2, window: 40, drift: "slow", topologyVol: 0.06, sparsity: 0.15, shockDist: "gaussian", wNoise: 0.35, wDrop: 0.0, replications: STRESS_REPLICATIONS, sigma: 0.03, horizon: 4 },
  { name: "heavy_tailed", label: "Heavy-tailed shocks", tLen: 160, n: 15, rankTrue: 2, rankEst: 2, window: 40, drift: "slow", topologyVol: 0.04, sparsity: 0.15, shockDist: "t5", wNoise: 0.0, replications: STRESS_REPLICATIONS, sigma: 0.03, horizon: 4 },
];

const METHOD_LABELS = {
  local_network: "Local rolling",
  cp_network: "CP-network",
  collapsed_operator_cp: "Collapsed-operator CP",
  tucker_network: "Tucker-network",
  cp_nonnetwork: "Low-rank no-network",
  sparse_network: "Sparse network TVP-VAR",
  graph_filter: "Graph-convolution VAR",
  graph_neural_var: "Graph neural VAR",
  diffusion_graph_var: "Diffusion graph VAR",
  recurrent_graph_filter: "Recurrent graph-filter VAR",
};
const METHOD_SEQUENCE = Object.keys(METHOD_LABELS);

function existingBenchmarkRecords() {
  if (process.env.NATCS_BENCHMARK_EXTEND !== "1" || !fs.existsSync(DETAIL_PATH)) return [];
  return readCsv(DETAIL_PATH);
}

function writeBenchmarkOutputs(records) {
  const summary = summarize(records);
  writeCsv(DETAIL_PATH, records);
  writeCsv(SUMMARY_PATH, summary);
  const legacy = [];
  for (const scenario of ["scale_n15", "scale_n30"]) {
    const local = summary.find((row) => row.scenario === scenario && row.method === "local_network");
    const cp = summary.find((row) => row.scenario === scenario && row.method === "cp_network");
    if (!local || !cp) continue;
    legacy.push({
      T: local.T,
      replications: local.replications,
      coef_error_raw_mean: local.coef_error_median,
      coef_error_cp_mean: cp.coef_error_median,
      coef_error_improvement_pct: 100 * (local.coef_error_median - cp.coef_error_median) / Math.max(local.coef_error_median, 1e-12),
      share_error_raw_mean: local.share_error_median,
      share_error_cp_mean: cp.share_error_median,
      share_error_improvement_pct: 100 * (local.share_error_median - cp.share_error_median) / Math.max(local.share_error_median, 1e-12),
      coef_error_raw_sd: 0,
      coef_error_cp_sd: 0,
      share_error_raw_sd: 0,
      share_error_cp_sd: 0,
    });
  }
  writeCsv(LEGACY_PATH, legacy);
  return { detail: DETAIL_PATH, summary: SUMMARY_PATH, legacy: LEGACY_PATH };
}

function activeMethods() {
  if (!process.env.NATCS_BENCHMARK_METHODS) return new Set(METHOD_SEQUENCE);
  return new Set(process.env.NATCS_BENCHMARK_METHODS.split(",").map((x) => x.trim()).filter(Boolean));
}

function shouldRun(methods, method) {
  return methods.has(method);
}

function activeScenarios() {
  const requested = process.env.NATCS_BENCHMARK_SCENARIOS
    ? new Set(process.env.NATCS_BENCHMARK_SCENARIOS.split(",").map((x) => x.trim()).filter(Boolean))
    : null;
  if (requested) return SCENARIOS.filter((cfg) => requested.has(cfg.name));
  if (process.env.NATCS_BENCHMARK_FAST === "1") {
    const keep = new Set(["scale_n15", "scale_n30", "scale_n50"]);
    return SCENARIOS.filter((cfg) => keep.has(cfg.name)).map((cfg) => ({ ...cfg, replications: Math.min(cfg.replications, 1) }));
  }
  return SCENARIOS;
}

function activeReplicationIndexes(cfg) {
  const start = Math.max(1, Number.isFinite(REP_START) ? REP_START : 1);
  const end = Math.min(cfg.replications, Number.isFinite(REP_END) ? REP_END : cfg.replications);
  if (end < start) return [];
  return Array.from({ length: end - start + 1 }, (_, idx) => start + idx);
}

function seedForScenarioReplication(cfg, rep) {
  let offset = 0;
  for (const scenario of SCENARIOS) {
    if (scenario.name === cfg.name) break;
    offset += scenario.replications;
  }
  return 20260328 + offset + rep;
}

function methodSeed(baseSeed, method) {
  let hash = 2166136261;
  for (const ch of method) {
    hash ^= ch.charCodeAt(0);
    hash = Math.imul(hash, 16777619) >>> 0;
  }
  return (baseSeed + hash) >>> 0;
}

function rng(seed) {
  let state = seed >>> 0;
  return () => {
    state = (1664525 * state + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function randn(next) {
  const u1 = Math.max(next(), 1e-12);
  const u2 = next();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

function randt5(next) {
  const z = randn(next);
  let chi = 0;
  for (let i = 0; i < 5; i += 1) chi += randn(next) ** 2;
  return z / Math.sqrt(chi / 5);
}

function zeros(r, c) {
  return Array.from({ length: r }, () => Array(c).fill(0));
}

function eye(n) {
  const out = zeros(n, n);
  for (let i = 0; i < n; i += 1) out[i][i] = 1;
  return out;
}

function clone(A) {
  return A.map((row) => row.slice());
}

function transpose(A) {
  return A[0].map((_, j) => A.map((row) => row[j]));
}

function matmul(A, B) {
  const Bt = transpose(B);
  return A.map((row) => Bt.map((col) => row.reduce((acc, v, i) => acc + v * col[i], 0)));
}

function matvec(A, v) {
  return A.map((row) => row.reduce((acc, x, i) => acc + x * v[i], 0));
}

function add(A, B) {
  return A.map((row, i) => row.map((x, j) => x + B[i][j]));
}

function scale(A, s) {
  return A.map((row) => row.map((x) => x * s));
}

function froNorm(A) {
  let total = 0;
  for (const row of A) for (const x of row) total += x * x;
  return Math.sqrt(total);
}

function dot(a, b) {
  let total = 0;
  for (let i = 0; i < a.length; i += 1) total += a[i] * b[i];
  return total;
}

function norm(a) {
  return Math.sqrt(dot(a, a));
}

function normalize(v) {
  const n = Math.max(norm(v), 1e-12);
  return v.map((x) => x / n);
}

function solve(A, B) {
  const n = A.length;
  const m = Array.isArray(B[0]) ? B[0].length : 1;
  const aug = A.map((row, i) => row.concat(Array.isArray(B[0]) ? B[i].slice() : [B[i]]));
  for (let col = 0; col < n; col += 1) {
    let pivot = col;
    for (let r = col + 1; r < n; r += 1) {
      if (Math.abs(aug[r][col]) > Math.abs(aug[pivot][col])) pivot = r;
    }
    if (Math.abs(aug[pivot][col]) < 1e-12) throw new Error("Singular system");
    [aug[col], aug[pivot]] = [aug[pivot], aug[col]];
    const div = aug[col][col];
    for (let j = col; j < n + m; j += 1) aug[col][j] /= div;
    for (let r = 0; r < n; r += 1) {
      if (r === col) continue;
      const factor = aug[r][col];
      for (let j = col; j < n + m; j += 1) aug[r][j] -= factor * aug[col][j];
    }
  }
  const out = aug.map((row) => row.slice(n));
  return m === 1 ? out.map((row) => row[0]) : out;
}

function gram(A) {
  return matmul(transpose(A), A);
}

function matrixFromColumns(cols) {
  const rows = cols[0].length;
  return Array.from({ length: rows }, (_, i) => cols.map((col) => col[i]));
}

function topEigenvectorsSym(A, k) {
  let work = clone(A);
  const vectors = [];
  const values = [];
  for (let r = 0; r < k; r += 1) {
    let v = Array.from({ length: A.length }, (_, i) => (i === r % A.length ? 1 : 0.1));
    v = normalize(v);
    for (let iter = 0; iter < 60; iter += 1) v = normalize(matvec(work, v));
    const lambda = dot(v, matvec(work, v));
    vectors.push(v);
    values.push(lambda);
    const outer = v.map((vi) => v.map((vj) => lambda * vi * vj));
    work = work.map((row, i) => row.map((x, j) => x - outer[i][j]));
  }
  return { vectors, values };
}

function spectralRadiusApprox(A) {
  const AtA = gram(A);
  const { values } = topEigenvectorsSym(AtA, 1);
  return Math.sqrt(Math.max(values[0], 0));
}

function randomMatrix(rows, cols, next, scaleValue = 1) {
  return Array.from({ length: rows }, () => Array.from({ length: cols }, () => scaleValue * randn(next)));
}

function unfoldTensor(X, mode) {
  const I = X.length;
  const J = X[0].length;
  const K = X[0][0].length;
  const rows = mode === 0 ? I : mode === 1 ? J : K;
  const cols = mode === 0 ? J * K : mode === 1 ? I * K : I * J;
  const out = zeros(rows, cols);
  if (mode === 0) {
    for (let i = 0; i < I; i += 1) for (let j = 0; j < J; j += 1) for (let k = 0; k < K; k += 1) out[i][j * K + k] = X[i][j][k];
  } else if (mode === 1) {
    for (let i = 0; i < I; i += 1) for (let j = 0; j < J; j += 1) for (let k = 0; k < K; k += 1) out[j][i * K + k] = X[i][j][k];
  } else {
    for (let i = 0; i < I; i += 1) for (let j = 0; j < J; j += 1) for (let k = 0; k < K; k += 1) out[k][i * J + j] = X[i][j][k];
  }
  return out;
}

function khatriRao(A, B) {
  const rows = A.length * B.length;
  const rank = A[0].length;
  const out = zeros(rows, rank);
  for (let r = 0; r < rank; r += 1) {
    for (let i = 0; i < A.length; i += 1) {
      for (let j = 0; j < B.length; j += 1) out[i * B.length + j][r] = A[i][r] * B[j][r];
    }
  }
  return out;
}

function cpAls(tensor, rank, next, iterations = 60) {
  const I = tensor.length;
  const J = tensor[0].length;
  const K = tensor[0][0].length;
  let A = randomMatrix(I, rank, next, 0.3);
  let B = randomMatrix(J, rank, next, 0.3);
  let C = randomMatrix(K, rank, next, 0.3);
  for (let it = 0; it < iterations; it += 1) {
    const gramCB = add(hadamard(gram(C), gram(B)), scale(eye(rank), 1e-6));
    A = matmul(unfoldTensor(tensor, 0), matmul(khatriRao(C, B), inverse(gramCB)));

    const gramCA = add(hadamard(gram(C), gram(A)), scale(eye(rank), 1e-6));
    B = matmul(unfoldTensor(tensor, 1), matmul(khatriRao(C, A), inverse(gramCA)));

    const gramBA = add(hadamard(gram(B), gram(A)), scale(eye(rank), 1e-6));
    C = matmul(unfoldTensor(tensor, 2), matmul(khatriRao(B, A), inverse(gramBA)));

    for (let r = 0; r < rank; r += 1) {
      const normA = Math.sqrt(A.reduce((acc, row) => acc + row[r] * row[r], 0)) || 1;
      const normB = Math.sqrt(B.reduce((acc, row) => acc + row[r] * row[r], 0)) || 1;
      for (let i = 0; i < I; i += 1) A[i][r] /= normA;
      for (let j = 0; j < J; j += 1) B[j][r] /= normB;
      for (let k = 0; k < K; k += 1) C[k][r] *= normA * normB;
    }
  }
  return { A, B, C };
}

function hadamard(A, B) {
  return A.map((row, i) => row.map((x, j) => x * B[i][j]));
}

function inverse(A) {
  return solve(A, eye(A.length));
}

function reconstructCp(A, B, C) {
  const I = A.length;
  const J = B.length;
  const K = C.length;
  const R = A[0].length;
  const out = Array.from({ length: I }, () => Array.from({ length: J }, () => Array(K).fill(0)));
  for (let r = 0; r < R; r += 1) {
    for (let i = 0; i < I; i += 1) {
      for (let j = 0; j < J; j += 1) {
        for (let k = 0; k < K; k += 1) out[i][j][k] += A[i][r] * B[j][r] * C[k][r];
      }
    }
  }
  return out;
}

function modeProduct(tensor, M, mode) {
  const I = tensor.length;
  const J = tensor[0].length;
  const K = tensor[0][0].length;
  if (mode === 0) {
    const out = Array.from({ length: M.length }, () => Array.from({ length: J }, () => Array(K).fill(0)));
    for (let r = 0; r < M.length; r += 1) for (let i = 0; i < I; i += 1) for (let j = 0; j < J; j += 1) for (let k = 0; k < K; k += 1) out[r][j][k] += M[r][i] * tensor[i][j][k];
    return out;
  }
  if (mode === 1) {
    const out = Array.from({ length: I }, () => Array.from({ length: M.length }, () => Array(K).fill(0)));
    for (let i = 0; i < I; i += 1) for (let r = 0; r < M.length; r += 1) for (let j = 0; j < J; j += 1) for (let k = 0; k < K; k += 1) out[i][r][k] += M[r][j] * tensor[i][j][k];
    return out;
  }
  const out = Array.from({ length: I }, () => Array.from({ length: J }, () => Array(M.length).fill(0)));
  for (let i = 0; i < I; i += 1) for (let j = 0; j < J; j += 1) for (let r = 0; r < M.length; r += 1) for (let k = 0; k < K; k += 1) out[i][j][r] += M[r][k] * tensor[i][j][k];
  return out;
}

function tuckerHosvd(tensor, ranks) {
  const U1 = matrixFromColumns(topEigenvectorsSym(matmul(unfoldTensor(tensor, 0), transpose(unfoldTensor(tensor, 0))), ranks[0]).vectors);
  const U2 = matrixFromColumns(topEigenvectorsSym(matmul(unfoldTensor(tensor, 1), transpose(unfoldTensor(tensor, 1))), ranks[1]).vectors);
  const U3 = matrixFromColumns(topEigenvectorsSym(matmul(unfoldTensor(tensor, 2), transpose(unfoldTensor(tensor, 2))), ranks[2]).vectors);
  let core = modeProduct(tensor, transpose(U1), 0);
  core = modeProduct(core, transpose(U2), 1);
  core = modeProduct(core, transpose(U3), 2);
  let out = modeProduct(core, U1, 0);
  out = modeProduct(out, U2, 1);
  out = modeProduct(out, U3, 2);
  return out;
}

function safeRowNormalize(W) {
  const out = clone(W);
  for (let i = 0; i < out.length; i += 1) {
    out[i][i] = 0;
    let sum = out[i].reduce((acc, x) => acc + Math.max(x, 0), 0);
    if (sum <= 1e-12) {
      const j = (i + 1) % out.length;
      out[i][j] = 1;
      sum = 1;
    }
    for (let j = 0; j < out.length; j += 1) out[i][j] = Math.max(out[i][j], 0) / sum;
  }
  return out;
}

function randomW(n, next, sparsity) {
  const W = zeros(n, n);
  for (let i = 0; i < n; i += 1) {
    for (let j = 0; j < n; j += 1) {
      if (i === j || next() < sparsity) {
        W[i][j] = 0;
      } else {
        W[i][j] = Math.max(randn(next) + 1.2, 0.05);
      }
    }
  }
  return safeRowNormalize(W);
}

function evolveW(prev, next, sparsity, vol) {
  const draw = randomW(prev.length, next, sparsity);
  const mixed = prev.map((row, i) => row.map((x, j) => (1 - vol) * x + vol * draw[i][j]));
  return safeRowNormalize(mixed);
}

function perturbW(W, next, sparsity, noise) {
  if (noise <= 0) return W;
  const alt = randomW(W.length, next, sparsity);
  return safeRowNormalize(W.map((row, i) => row.map((x, j) => (1 - noise) * x + noise * alt[i][j])));
}

function dropObservedEdges(W, next, dropRate = 0) {
  if (dropRate <= 0) return W;
  const out = W.map((row, i) => row.map((x, j) => (i !== j && x > 0 && next() < dropRate ? 0 : x)));
  return safeRowNormalize(out);
}

function latentPath(cfg, next) {
  const g = Array.from({ length: cfg.tLen }, () => Array(cfg.rankTrue).fill(0));
  g[0] = Array.from({ length: cfg.rankTrue }, (_, i) => (i === 0 ? 0.85 : -0.3) + 0.08 * randn(next));
  for (let t = 1; t < cfg.tLen; t += 1) {
    const jump = cfg.drift === "abrupt" && (t === Math.floor(cfg.tLen / 3) || t === Math.floor((2 * cfg.tLen) / 3));
    g[t] = g[t - 1].map((x) => (jump ? x + 0.35 * randn(next) : (cfg.drift === "abrupt" ? 0.9 * x : 0.97 * x) + (cfg.drift === "abrupt" ? 0.05 : 0.04) * randn(next)));
  }
  return g;
}

function stabilizeBlocks(A, B, W) {
  const radius = spectralRadiusApprox(add(A, matmul(B, W)));
  if (radius > 0.78) {
    const scaleFactor = 0.78 / Math.max(radius, 1e-12);
    return [scale(A, scaleFactor), scale(B, scaleFactor)];
  }
  return [A, B];
}

function generateTruth(cfg, next) {
  const U = randomMatrix(cfg.n, cfg.rankTrue, next, 0.7);
  const Vd = randomMatrix(cfg.n, cfg.rankTrue, next, 0.7);
  const Vn = randomMatrix(cfg.n, cfg.rankTrue, next, 0.55);
  const g = latentPath(cfg, next);
  const W = [];
  W[0] = randomW(cfg.n, next, cfg.sparsity);
  for (let t = 1; t < cfg.tLen; t += 1) W[t] = evolveW(W[t - 1], next, cfg.sparsity, cfg.topologyVol);
  const A = [];
  const B = [];
  for (let t = 0; t < cfg.tLen; t += 1) {
    const diag = zeros(cfg.rankTrue, cfg.rankTrue);
    for (let r = 0; r < cfg.rankTrue; r += 1) diag[r][r] = g[t][r];
    let At = scale(matmul(matmul(U, diag), transpose(Vd)), 0.12 / cfg.n);
    let Bt = scale(matmul(matmul(U, diag), transpose(Vn)), 0.28 / cfg.n);
    [At, Bt] = stabilizeBlocks(At, Bt, W[t]);
    A.push(At);
    B.push(Bt);
  }
  return { A, B, W };
}

function sampleShock(next, dist) {
  return dist === "t5" ? randt5(next) / Math.sqrt(5 / 3) : randn(next);
}

function simulatePanel(cfg, seed) {
  const next = rng(seed);
  const truth = generateTruth(cfg, next);
  const y = Array.from({ length: cfg.tLen }, () => Array(cfg.n).fill(0));
  for (let t = 1; t < cfg.tLen; t += 1) {
    const lag = y[t - 1];
    const networkLag = matvec(truth.W[t - 1], lag);
    const direct = matvec(truth.A[t - 1], lag);
    const network = matvec(truth.B[t - 1], networkLag);
    y[t] = direct.map((x, i) => x + network[i] + cfg.sigma * sampleShock(next, cfg.shockDist));
  }
  return {
    y,
    ...truth,
    WEst: truth.W.map((Wt) => dropObservedEdges(perturbW(Wt, next, cfg.sparsity, cfg.wNoise), next, cfg.wDrop ?? 0)),
  };
}

function ridgeOls(X, Y) {
  const Xt = transpose(X);
  const XtX = matmul(Xt, X).map((row, i) => row.map((x, j) => x + (i === j ? 1e-6 : 0)));
  const XtY = matmul(Xt, Y);
  return transpose(solve(XtX, XtY));
}

function estimateLocalNetwork(y, W, window) {
  const tensor = [];
  const idxs = [];
  for (let t = window; t < y.length; t += 1) {
    const X = [];
    const Y = [];
    for (let s = t - window + 1; s < t; s += 1) {
      X.push([...y[s - 1], ...matvec(W[s - 1], y[s - 1])]);
      Y.push(y[s]);
    }
    const beta = ridgeOls(X, Y);
    tensor.push(beta);
    idxs.push(t - 1);
  }
  return { tensor: toTensor(tensor), idxs };
}

function estimateLocalNoNetwork(y, window) {
  const tensor = [];
  const idxs = [];
  for (let t = window; t < y.length; t += 1) {
    const X = [];
    const Y = [];
    for (let s = t - window + 1; s < t; s += 1) {
      X.push([...y[s - 1]]);
      Y.push(y[s]);
    }
    const beta = ridgeOls(X, Y);
    tensor.push(beta);
    idxs.push(t - 1);
  }
  return { tensor: toTensor(tensor), idxs };
}

function collapseNetworkTensor(local, WUse, n) {
  const blocks = local.idxs.map((idx, k) => {
    const beta = tensorSlice(local.tensor, k);
    const A = beta.map((row) => row.slice(0, n));
    const B = beta.map((row) => row.slice(n));
    return add(A, matmul(B, WUse[idx]));
  });
  return { tensor: toTensor(blocks), idxs: local.idxs };
}

function softThreshold(x, lambda) {
  if (x > lambda) return x - lambda;
  if (x < -lambda) return x + lambda;
  return 0;
}

function estimateSparseNetwork(y, W, window, threshold = 0.025) {
  const local = estimateLocalNetwork(y, W, window);
  const tensor = local.tensor.map((row) => row.map((col) => col.map((x) => softThreshold(x, threshold))));
  return { tensor, idxs: local.idxs };
}

function estimateGraphFilter(y, W, window) {
  const tensor = [];
  const idxs = [];
  const n = y[0].length;
  for (let t = window; t < y.length; t += 1) {
    const X = [];
    const Y = [];
    for (let s = t - window + 1; s < t; s += 1) {
      X.push([1, ...y[s - 1], ...matvec(W[s - 1], y[s - 1])]);
      Y.push(y[s]);
    }
    const beta = ridgeOls(X, Y);
    const block = zeros(n, 2 * n);
    for (let i = 0; i < n; i += 1) {
      block[i][i] = beta[i][i + 1];
      block[i][n + i] = beta[i][n + i + 1];
    }
    tensor.push(block);
    idxs.push(t - 1);
  }
  return { tensor: toTensor(tensor), idxs };
}

function estimateGraphNeuralVar(y, W, window) {
  const tensor = [];
  const idxs = [];
  const n = y[0].length;
  for (let t = window; t < y.length; t += 1) {
    const X = [];
    const Y = [];
    for (let s = t - window + 1; s < t; s += 1) {
      const lag = y[s - 1];
      const networkLag = matvec(W[s - 1], lag);
      X.push([
        ...lag,
        ...networkLag,
        ...lag.map((x) => Math.tanh(x)),
        ...networkLag.map((x) => Math.tanh(x)),
      ]);
      Y.push(y[s]);
    }
    const beta = ridgeOls(X, Y);
    const block = zeros(n, 2 * n);
    for (let i = 0; i < n; i += 1) {
      for (let j = 0; j < n; j += 1) {
        block[i][j] = beta[i][j] + beta[i][2 * n + j];
        block[i][n + j] = beta[i][n + j] + beta[i][3 * n + j];
      }
    }
    tensor.push(block);
    idxs.push(t - 1);
  }
  return { tensor: toTensor(tensor), idxs };
}

function estimateDiffusionGraphVar(y, W, window) {
  const tensor = [];
  const idxs = [];
  const n = y[0].length;
  for (let t = window; t < y.length; t += 1) {
    const X = [];
    const Y = [];
    for (let s = t - window + 1; s < t; s += 1) {
      const lag = y[s - 1];
      const Wlag = matvec(W[s - 1], lag);
      const W2lag = matvec(W[s - 1], Wlag);
      X.push([...lag, ...Wlag, ...W2lag]);
      Y.push(y[s]);
    }
    const beta = ridgeOls(X, Y);
    const WRef = W[t - 1];
    const block = zeros(n, 2 * n);
    for (let i = 0; i < n; i += 1) {
      for (let j = 0; j < n; j += 1) {
        block[i][j] = beta[i][j];
        let projectedTwoHop = 0;
        for (let l = 0; l < n; l += 1) projectedTwoHop += beta[i][2 * n + l] * WRef[l][j];
        block[i][n + j] = beta[i][n + j] + projectedTwoHop;
      }
    }
    tensor.push(block);
    idxs.push(t - 1);
  }
  return { tensor: toTensor(tensor), idxs };
}

function estimateRecurrentGraphFilterVar(y, W, window) {
  const tensor = [];
  const idxs = [];
  const n = y[0].length;
  for (let t = window; t < y.length; t += 1) {
    const X = [];
    const Y = [];
    let previousPrediction = Array(n).fill(0);
    for (let s = t - window + 1; s < t; s += 1) {
      const lag = y[s - 1];
      const Wlag = matvec(W[s - 1], lag);
      const W2lag = matvec(W[s - 1], Wlag);
      const row = [
        ...lag,
        ...Wlag,
        ...W2lag,
        ...previousPrediction,
      ];
      X.push(row);
      Y.push(y[s]);
      previousPrediction = row.slice(0, n).map((x, i) => 0.45 * x + 0.35 * row[n + i] + 0.20 * previousPrediction[i]);
    }
    const beta = ridgeOls(X, Y);
    const WRef = W[t - 1];
    const block = zeros(n, 2 * n);
    for (let i = 0; i < n; i += 1) {
      for (let j = 0; j < n; j += 1) {
        let recurrentDirect = beta[i][3 * n + j] * 0.45;
        let recurrentNetwork = beta[i][3 * n + j] * 0.35;
        block[i][j] = beta[i][j] + recurrentDirect;
        let projectedTwoHop = 0;
        for (let l = 0; l < n; l += 1) projectedTwoHop += beta[i][2 * n + l] * WRef[l][j];
        block[i][n + j] = beta[i][n + j] + projectedTwoHop + recurrentNetwork;
      }
    }
    tensor.push(block);
    idxs.push(t - 1);
  }
  return { tensor: toTensor(tensor), idxs };
}

function toTensor(blocks) {
  const K = blocks.length;
  const I = blocks[0].length;
  const J = blocks[0][0].length;
  const tensor = Array.from({ length: I }, () => Array.from({ length: J }, () => Array(K).fill(0)));
  for (let k = 0; k < K; k += 1) for (let i = 0; i < I; i += 1) for (let j = 0; j < J; j += 1) tensor[i][j][k] = blocks[k][i][j];
  return tensor;
}

function tensorSlice(tensor, k) {
  return tensor.map((row) => row.map((col) => col[k]));
}

function cumulativeResponse(M, horizon, shock) {
  let current = eye(M.length);
  const e = Array(M.length).fill(0);
  e[shock] = 1;
  const out = [];
  for (let h = 0; h <= horizon; h += 1) {
    out.push(matvec(current, e));
    current = matmul(M, current);
  }
  return out;
}

function stabilizeEffective(M) {
  const radius = spectralRadiusApprox(M);
  return radius >= 0.95 ? scale(M, 0.95 / Math.max(radius, 1e-12)) : M;
}

function networkShareRaw(A, B, W, horizon, receiver = A.length - 1, shock = 0) {
  const total = stabilizeEffective(add(A, matmul(B, W)));
  const direct = stabilizeEffective(A);
  let sTotal = 0;
  let sDirect = 0;
  for (const vec of cumulativeResponse(total, horizon, shock)) sTotal += Math.abs(vec[receiver]);
  for (const vec of cumulativeResponse(direct, horizon, shock)) sDirect += Math.abs(vec[receiver]);
  return (sTotal - sDirect) / Math.max(sTotal, 1e-12);
}

function girfError(MTrue, MHat, horizon) {
  const t = stabilizeEffective(MTrue);
  const h = stabilizeEffective(MHat);
  let total = 0;
  let count = 0;
  for (let shock = 0; shock < t.length; shock += 1) {
    const rt = cumulativeResponse(t, horizon, shock);
    const rh = cumulativeResponse(h, horizon, shock);
    for (let i = 0; i < rt.length; i += 1) {
      total += rt[i].reduce((acc, x, idx) => acc + Math.abs(x - rh[i][idx]), 0);
      count += 1;
    }
  }
  return total / Math.max(count, 1);
}

function networkComponentError(A, B, W, AHat, BHat, WHat, horizon) {
  const totalTrue = stabilizeEffective(add(A, matmul(B, W)));
  const totalHat = stabilizeEffective(add(AHat, matmul(BHat, WHat)));
  const directTrue = stabilizeEffective(A);
  const directHat = stabilizeEffective(AHat);
  let total = 0;
  let count = 0;
  for (let shock = 0; shock < A.length; shock += 1) {
    const rtTotal = cumulativeResponse(totalTrue, horizon, shock);
    const rhTotal = cumulativeResponse(totalHat, horizon, shock);
    const rtDirect = cumulativeResponse(directTrue, horizon, shock);
    const rhDirect = cumulativeResponse(directHat, horizon, shock);
    for (let h = 0; h < rtTotal.length; h += 1) {
      for (let i = 0; i < A.length; i += 1) {
        total += Math.abs((rtTotal[h][i] - rtDirect[h][i]) - (rhTotal[h][i] - rhDirect[h][i]));
        count += 1;
      }
    }
  }
  return total / Math.max(count, 1);
}

function averageW(mats, limit = 16) {
  const take = Math.max(1, Math.min(limit, mats.length));
  const acc = zeros(mats[0].length, mats[0][0].length);
  for (let t = 0; t < take; t += 1) {
    for (let i = 0; i < acc.length; i += 1) {
      for (let j = 0; j < acc.length; j += 1) acc[i][j] += mats[t][i][j] / take;
    }
  }
  return safeRowNormalize(acc);
}

function evaluateNetworkTensor(tensor, idxs, truth, horizon, WUse, WPre) {
  const metrics = { coef: [], share: [], girf: [], networkComponent: [], frozenCounterfactual: [], prediction: [], unstable: 0 };
  for (let k = 0; k < idxs.length; k += 1) {
    const idx = idxs[k];
    const beta = tensorSlice(tensor, k);
    const AHat = beta.map((row) => row.slice(0, truth.A[0].length));
    const BHat = beta.map((row) => row.slice(truth.A[0].length));
    const MHat = add(AHat, matmul(BHat, WUse[idx]));
    const MTrue = add(truth.A[idx], matmul(truth.B[idx], truth.W[idx]));
    metrics.coef.push(froNorm(add(MHat, scale(MTrue, -1))) / Math.max(froNorm(MTrue), 1e-12));
    metrics.share.push(Math.abs(networkShareRaw(AHat, BHat, WUse[idx], horizon) - networkShareRaw(truth.A[idx], truth.B[idx], truth.W[idx], horizon)));
    metrics.girf.push(girfError(MTrue, MHat, horizon));
    metrics.networkComponent.push(networkComponentError(truth.A[idx], truth.B[idx], truth.W[idx], AHat, BHat, WUse[idx], horizon));
    metrics.frozenCounterfactual.push(girfError(add(truth.A[idx], matmul(truth.B[idx], WPre)), add(AHat, matmul(BHat, WPre)), horizon));
    if (truth.y && truth.y[idx] && truth.y[idx + 1]) {
      const pred = matvec(MHat, truth.y[idx]);
      const actual = truth.y[idx + 1];
      metrics.prediction.push(Math.sqrt(pred.reduce((acc, x, i) => acc + (x - actual[i]) ** 2, 0) / Math.max(pred.length, 1)));
    }
    metrics.unstable += spectralRadiusApprox(MHat) >= 0.98 ? 1 : 0;
  }
  const mean = (arr) => arr.reduce((a, b) => a + b, 0) / Math.max(arr.length, 1);
  return {
    coefError: mean(metrics.coef),
    shareError: mean(metrics.share),
    girfError: mean(metrics.girf),
    networkComponentError: mean(metrics.networkComponent),
    frozenCounterfactualError: mean(metrics.frozenCounterfactual),
    predictionError: mean(metrics.prediction),
    instabilityRate: metrics.unstable / Math.max(idxs.length, 1),
  };
}

function evaluateNoNetworkTensor(tensor, idxs, truth, horizon) {
  const metrics = { coef: [], share: [], girf: [], networkComponent: [], frozenCounterfactual: [], prediction: [], unstable: 0 };
  for (let k = 0; k < idxs.length; k += 1) {
    const idx = idxs[k];
    const AHat = tensorSlice(tensor, k);
    const MTrue = add(truth.A[idx], matmul(truth.B[idx], truth.W[idx]));
    metrics.coef.push(froNorm(add(AHat, scale(MTrue, -1))) / Math.max(froNorm(MTrue), 1e-12));
    metrics.share.push(NaN);
    metrics.girf.push(girfError(MTrue, AHat, horizon));
    metrics.networkComponent.push(NaN);
    metrics.frozenCounterfactual.push(NaN);
    if (truth.y && truth.y[idx] && truth.y[idx + 1]) {
      const pred = matvec(AHat, truth.y[idx]);
      const actual = truth.y[idx + 1];
      metrics.prediction.push(Math.sqrt(pred.reduce((acc, x, i) => acc + (x - actual[i]) ** 2, 0) / Math.max(pred.length, 1)));
    }
    metrics.unstable += spectralRadiusApprox(AHat) >= 0.98 ? 1 : 0;
  }
  const mean = (arr) => arr.reduce((a, b) => a + b, 0) / Math.max(arr.length, 1);
  return {
    coefError: mean(metrics.coef),
    shareError: mean(metrics.share),
    girfError: mean(metrics.girf),
    networkComponentError: mean(metrics.networkComponent),
    frozenCounterfactualError: mean(metrics.frozenCounterfactual),
    predictionError: mean(metrics.prediction),
    instabilityRate: metrics.unstable / Math.max(idxs.length, 1),
  };
}

function evaluateCollapsedTensor(tensor, idxs, truth, horizon) {
  const metrics = { coef: [], share: [], girf: [], networkComponent: [], frozenCounterfactual: [], prediction: [], unstable: 0 };
  for (let k = 0; k < idxs.length; k += 1) {
    const idx = idxs[k];
    const MHat = tensorSlice(tensor, k);
    const MTrue = add(truth.A[idx], matmul(truth.B[idx], truth.W[idx]));
    metrics.coef.push(froNorm(add(MHat, scale(MTrue, -1))) / Math.max(froNorm(MTrue), 1e-12));
    metrics.share.push(NaN);
    metrics.girf.push(girfError(MTrue, MHat, horizon));
    metrics.networkComponent.push(NaN);
    metrics.frozenCounterfactual.push(NaN);
    if (truth.y && truth.y[idx] && truth.y[idx + 1]) {
      const pred = matvec(MHat, truth.y[idx]);
      const actual = truth.y[idx + 1];
      metrics.prediction.push(Math.sqrt(pred.reduce((acc, x, i) => acc + (x - actual[i]) ** 2, 0) / Math.max(pred.length, 1)));
    }
    metrics.unstable += spectralRadiusApprox(MHat) >= 0.98 ? 1 : 0;
  }
  const mean = (arr) => arr.reduce((a, b) => a + b, 0) / Math.max(arr.length, 1);
  return {
    coefError: mean(metrics.coef),
    shareError: mean(metrics.share),
    girfError: mean(metrics.girf),
    networkComponentError: mean(metrics.networkComponent),
    frozenCounterfactualError: mean(metrics.frozenCounterfactual),
    predictionError: mean(metrics.prediction),
    instabilityRate: metrics.unstable / Math.max(idxs.length, 1),
  };
}

function summarize(records) {
  const groups = new Map();
  for (const row of records) {
    const key = `${row.scenario}::${row.method}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(row);
  }
  const quantile = (arr, q) => {
    const sorted = [...arr].sort((a, b) => a - b);
    const pos = (sorted.length - 1) * q;
    const low = Math.floor(pos);
    const high = Math.ceil(pos);
    if (low === high) return sorted[low];
    const w = pos - low;
    return sorted[low] * (1 - w) + sorted[high] * w;
  };
  const summary = [];
  const q = (arr, p) => {
    const valid = arr.filter((x) => Number.isFinite(x));
    if (!valid.length) return NaN;
    return quantile(valid, p);
  };
  for (const rows of groups.values()) {
    summary.push({
      scenario: rows[0].scenario,
      scenario_label: rows[0].scenario_label,
      method: rows[0].method,
      method_label: METHOD_LABELS[rows[0].method],
      T: rows[0].T,
      N: rows[0].N,
      replications: rows.length,
      coef_error_median: q(rows.map((r) => r.coef_error), 0.5),
      coef_error_q25: q(rows.map((r) => r.coef_error), 0.25),
      coef_error_q75: q(rows.map((r) => r.coef_error), 0.75),
      share_error_median: q(rows.map((r) => r.share_error), 0.5),
      share_error_q25: q(rows.map((r) => r.share_error), 0.25),
      share_error_q75: q(rows.map((r) => r.share_error), 0.75),
      girf_error_median: q(rows.map((r) => r.girf_error), 0.5),
      girf_error_q25: q(rows.map((r) => r.girf_error), 0.25),
      girf_error_q75: q(rows.map((r) => r.girf_error), 0.75),
      network_component_error_median: q(rows.map((r) => r.network_component_error), 0.5),
      network_component_error_q25: q(rows.map((r) => r.network_component_error), 0.25),
      network_component_error_q75: q(rows.map((r) => r.network_component_error), 0.75),
      frozen_counterfactual_error_median: q(rows.map((r) => r.frozen_counterfactual_error), 0.5),
      frozen_counterfactual_error_q25: q(rows.map((r) => r.frozen_counterfactual_error), 0.25),
      frozen_counterfactual_error_q75: q(rows.map((r) => r.frozen_counterfactual_error), 0.75),
      prediction_error_median: q(rows.map((r) => r.prediction_error), 0.5),
      prediction_error_q25: q(rows.map((r) => r.prediction_error), 0.25),
      prediction_error_q75: q(rows.map((r) => r.prediction_error), 0.75),
      runtime_mean_seconds: rows.reduce((a, b) => a + b.runtime_seconds, 0) / rows.length,
      memory_mb_median: q(rows.map((r) => r.memory_mb), 0.5),
      memory_mb_q25: q(rows.map((r) => r.memory_mb), 0.25),
      memory_mb_q75: q(rows.map((r) => r.memory_mb), 0.75),
      instability_rate_mean: rows.reduce((a, b) => a + b.instability_rate, 0) / rows.length,
      failure_rate: rows.reduce((a, b) => a + b.failure, 0) / rows.length,
    });
  }
  return summary;
}

export function generateSyntheticBenchmarks() {
  ensureDir(OUTPUT_DIR);
  const records = existingBenchmarkRecords();
  const methods = activeMethods();
  let seed = 20260328;
  for (const cfg of activeScenarios()) {
    const hasExisting = (method, replication) => process.env.NATCS_BENCHMARK_EXTEND === "1"
      && records.some((row) => row.scenario === cfg.name && row.method === method && Number(row.replication) === replication);
    for (const replication of activeReplicationIndexes(cfg)) {
      const rep = replication - 1;
      const pendingMethods = [...methods].filter((method) => !hasExisting(method, replication));
      if (process.env.NATCS_BENCHMARK_EXTEND === "1" && pendingMethods.length === 0) continue;
      const started = Date.now();
      const simSeed = process.env.NATCS_BENCHMARK_EXTEND === "1"
        ? seedForScenarioReplication(cfg, rep)
        : seed++;
      const sim = simulatePanel(cfg, simSeed);
      const WPre = averageW(sim.W);
      const local = estimateLocalNetwork(sim.y, sim.WEst, cfg.window);
      const localMetrics = evaluateNetworkTensor(local.tensor, local.idxs, sim, cfg.horizon, sim.WEst, WPre);
      if (shouldRun(methods, "local_network") && !hasExisting("local_network", replication)) records.push({
        scenario: cfg.name,
        scenario_label: cfg.label,
        method: "local_network",
        replication,
        T: cfg.tLen,
        N: cfg.n,
        coef_error: localMetrics.coefError,
        share_error: localMetrics.shareError,
        girf_error: localMetrics.girfError,
        network_component_error: localMetrics.networkComponentError,
        frozen_counterfactual_error: localMetrics.frozenCounterfactualError,
        prediction_error: localMetrics.predictionError,
        runtime_seconds: (Date.now() - started) / 1000,
        memory_mb: process.memoryUsage().rss / (1024 * 1024),
        instability_rate: localMetrics.instabilityRate,
        failure: 0,
      });

      const legacyNext = rng(simSeed + 1001 + rep);
      if (shouldRun(methods, "cp_network") && !hasExisting("cp_network", replication)) {
      const cpStarted = Date.now();
      let cpFailure = 0;
      let cpMetrics = { coefError: NaN, shareError: NaN, girfError: NaN, networkComponentError: NaN, frozenCounterfactualError: NaN, predictionError: NaN, instabilityRate: NaN };
      try {
        const cp = cpAls(local.tensor, cfg.rankEst, legacyNext);
        cpMetrics = evaluateNetworkTensor(reconstructCp(cp.A, cp.B, cp.C), local.idxs, sim, cfg.horizon, sim.WEst, WPre);
      } catch {
        cpFailure = 1;
      }
      records.push({
        scenario: cfg.name,
        scenario_label: cfg.label,
        method: "cp_network",
        replication,
        T: cfg.tLen,
        N: cfg.n,
        coef_error: cpMetrics.coefError,
        share_error: cpMetrics.shareError,
        girf_error: cpMetrics.girfError,
        network_component_error: cpMetrics.networkComponentError,
        frozen_counterfactual_error: cpMetrics.frozenCounterfactualError,
        prediction_error: cpMetrics.predictionError,
        runtime_seconds: (Date.now() - cpStarted) / 1000,
        memory_mb: process.memoryUsage().rss / (1024 * 1024),
        instability_rate: cpMetrics.instabilityRate,
        failure: cpFailure,
      });
      }

      if (shouldRun(methods, "collapsed_operator_cp") && !hasExisting("collapsed_operator_cp", replication)) {
      const next = rng(methodSeed(simSeed, "collapsed_operator_cp"));
      const collapsedStarted = Date.now();
      let collapsedFailure = 0;
      let collapsedMetrics = { coefError: NaN, shareError: NaN, girfError: NaN, networkComponentError: NaN, frozenCounterfactualError: NaN, predictionError: NaN, instabilityRate: NaN };
      try {
        const collapsed = collapseNetworkTensor(local, sim.WEst, cfg.n);
        const cp = cpAls(collapsed.tensor, cfg.rankEst, next);
        collapsedMetrics = evaluateCollapsedTensor(reconstructCp(cp.A, cp.B, cp.C), collapsed.idxs, sim, cfg.horizon);
      } catch {
        collapsedFailure = 1;
      }
      records.push({
        scenario: cfg.name,
        scenario_label: cfg.label,
        method: "collapsed_operator_cp",
        replication,
        T: cfg.tLen,
        N: cfg.n,
        coef_error: collapsedMetrics.coefError,
        share_error: collapsedMetrics.shareError,
        girf_error: collapsedMetrics.girfError,
        network_component_error: collapsedMetrics.networkComponentError,
        frozen_counterfactual_error: collapsedMetrics.frozenCounterfactualError,
        prediction_error: collapsedMetrics.predictionError,
        runtime_seconds: (Date.now() - collapsedStarted) / 1000,
        memory_mb: process.memoryUsage().rss / (1024 * 1024),
        instability_rate: collapsedMetrics.instabilityRate,
        failure: collapsedFailure,
      });
      }

      if (shouldRun(methods, "tucker_network") && !hasExisting("tucker_network", replication)) {
      const tuckerStarted = Date.now();
      let tuckerFailure = 0;
      let tuckerMetrics = { coefError: NaN, shareError: NaN, girfError: NaN, networkComponentError: NaN, frozenCounterfactualError: NaN, predictionError: NaN, instabilityRate: NaN };
      try {
        const tuckerTensor = tuckerHosvd(local.tensor, [cfg.rankEst, cfg.rankEst, cfg.rankEst]);
        tuckerMetrics = evaluateNetworkTensor(tuckerTensor, local.idxs, sim, cfg.horizon, sim.WEst, WPre);
      } catch {
        tuckerFailure = 1;
      }
      records.push({
        scenario: cfg.name,
        scenario_label: cfg.label,
        method: "tucker_network",
        replication,
        T: cfg.tLen,
        N: cfg.n,
        coef_error: tuckerMetrics.coefError,
        share_error: tuckerMetrics.shareError,
        girf_error: tuckerMetrics.girfError,
        network_component_error: tuckerMetrics.networkComponentError,
        frozen_counterfactual_error: tuckerMetrics.frozenCounterfactualError,
        prediction_error: tuckerMetrics.predictionError,
        runtime_seconds: (Date.now() - tuckerStarted) / 1000,
        memory_mb: process.memoryUsage().rss / (1024 * 1024),
        instability_rate: tuckerMetrics.instabilityRate,
        failure: tuckerFailure,
      });
      }

      if (shouldRun(methods, "sparse_network") && !hasExisting("sparse_network", replication)) {
      const sparseStarted = Date.now();
      let sparseFailure = 0;
      let sparseMetrics = { coefError: NaN, shareError: NaN, girfError: NaN, networkComponentError: NaN, frozenCounterfactualError: NaN, predictionError: NaN, instabilityRate: NaN };
      try {
        const sparse = estimateSparseNetwork(sim.y, sim.WEst, cfg.window);
        sparseMetrics = evaluateNetworkTensor(sparse.tensor, sparse.idxs, sim, cfg.horizon, sim.WEst, WPre);
      } catch {
        sparseFailure = 1;
      }
      records.push({
        scenario: cfg.name,
        scenario_label: cfg.label,
        method: "sparse_network",
        replication,
        T: cfg.tLen,
        N: cfg.n,
        coef_error: sparseMetrics.coefError,
        share_error: sparseMetrics.shareError,
        girf_error: sparseMetrics.girfError,
        network_component_error: sparseMetrics.networkComponentError,
        frozen_counterfactual_error: sparseMetrics.frozenCounterfactualError,
        prediction_error: sparseMetrics.predictionError,
        runtime_seconds: (Date.now() - sparseStarted) / 1000,
        memory_mb: process.memoryUsage().rss / (1024 * 1024),
        instability_rate: sparseMetrics.instabilityRate,
        failure: sparseFailure,
      });
      }

      if (shouldRun(methods, "graph_filter") && !hasExisting("graph_filter", replication)) {
      const graphStarted = Date.now();
      let graphFailure = 0;
      let graphMetrics = { coefError: NaN, shareError: NaN, girfError: NaN, networkComponentError: NaN, frozenCounterfactualError: NaN, predictionError: NaN, instabilityRate: NaN };
      try {
        const graph = estimateGraphFilter(sim.y, sim.WEst, cfg.window);
        graphMetrics = evaluateNetworkTensor(graph.tensor, graph.idxs, sim, cfg.horizon, sim.WEst, WPre);
      } catch {
        graphFailure = 1;
      }
      records.push({
        scenario: cfg.name,
        scenario_label: cfg.label,
        method: "graph_filter",
        replication,
        T: cfg.tLen,
        N: cfg.n,
        coef_error: graphMetrics.coefError,
        share_error: graphMetrics.shareError,
        girf_error: graphMetrics.girfError,
        network_component_error: graphMetrics.networkComponentError,
        frozen_counterfactual_error: graphMetrics.frozenCounterfactualError,
        prediction_error: graphMetrics.predictionError,
        runtime_seconds: (Date.now() - graphStarted) / 1000,
        memory_mb: process.memoryUsage().rss / (1024 * 1024),
        instability_rate: graphMetrics.instabilityRate,
        failure: graphFailure,
      });
      }

      if (shouldRun(methods, "graph_neural_var") && !hasExisting("graph_neural_var", replication)) {
      const graphNeuralStarted = Date.now();
      let graphNeuralFailure = 0;
      let graphNeuralMetrics = { coefError: NaN, shareError: NaN, girfError: NaN, networkComponentError: NaN, frozenCounterfactualError: NaN, predictionError: NaN, instabilityRate: NaN };
      try {
        const graphNeural = estimateGraphNeuralVar(sim.y, sim.WEst, cfg.window);
        graphNeuralMetrics = evaluateNetworkTensor(graphNeural.tensor, graphNeural.idxs, sim, cfg.horizon, sim.WEst, WPre);
      } catch {
        graphNeuralFailure = 1;
      }
      records.push({
        scenario: cfg.name,
        scenario_label: cfg.label,
        method: "graph_neural_var",
        replication,
        T: cfg.tLen,
        N: cfg.n,
        coef_error: graphNeuralMetrics.coefError,
        share_error: graphNeuralMetrics.shareError,
        girf_error: graphNeuralMetrics.girfError,
        network_component_error: graphNeuralMetrics.networkComponentError,
        frozen_counterfactual_error: graphNeuralMetrics.frozenCounterfactualError,
        prediction_error: graphNeuralMetrics.predictionError,
        runtime_seconds: (Date.now() - graphNeuralStarted) / 1000,
        memory_mb: process.memoryUsage().rss / (1024 * 1024),
        instability_rate: graphNeuralMetrics.instabilityRate,
        failure: graphNeuralFailure,
      });
      }

      if (shouldRun(methods, "diffusion_graph_var") && !hasExisting("diffusion_graph_var", replication)) {
      const diffusionStarted = Date.now();
      let diffusionFailure = 0;
      let diffusionMetrics = { coefError: NaN, shareError: NaN, girfError: NaN, networkComponentError: NaN, frozenCounterfactualError: NaN, predictionError: NaN, instabilityRate: NaN };
      try {
        const diffusion = estimateDiffusionGraphVar(sim.y, sim.WEst, cfg.window);
        diffusionMetrics = evaluateNetworkTensor(diffusion.tensor, diffusion.idxs, sim, cfg.horizon, sim.WEst, WPre);
      } catch {
        diffusionFailure = 1;
      }
      records.push({
        scenario: cfg.name,
        scenario_label: cfg.label,
        method: "diffusion_graph_var",
        replication,
        T: cfg.tLen,
        N: cfg.n,
        coef_error: diffusionMetrics.coefError,
        share_error: diffusionMetrics.shareError,
        girf_error: diffusionMetrics.girfError,
        network_component_error: diffusionMetrics.networkComponentError,
        frozen_counterfactual_error: diffusionMetrics.frozenCounterfactualError,
        prediction_error: diffusionMetrics.predictionError,
        runtime_seconds: (Date.now() - diffusionStarted) / 1000,
        memory_mb: process.memoryUsage().rss / (1024 * 1024),
        instability_rate: diffusionMetrics.instabilityRate,
        failure: diffusionFailure,
      });
      }

      if (shouldRun(methods, "recurrent_graph_filter") && !hasExisting("recurrent_graph_filter", replication)) {
      const recurrentGraphStarted = Date.now();
      let recurrentGraphFailure = 0;
      let recurrentGraphMetrics = { coefError: NaN, shareError: NaN, girfError: NaN, networkComponentError: NaN, frozenCounterfactualError: NaN, predictionError: NaN, instabilityRate: NaN };
      try {
        const recurrentGraph = estimateRecurrentGraphFilterVar(sim.y, sim.WEst, cfg.window);
        recurrentGraphMetrics = evaluateNetworkTensor(recurrentGraph.tensor, recurrentGraph.idxs, sim, cfg.horizon, sim.WEst, WPre);
      } catch {
        recurrentGraphFailure = 1;
      }
      records.push({
        scenario: cfg.name,
        scenario_label: cfg.label,
        method: "recurrent_graph_filter",
        replication,
        T: cfg.tLen,
        N: cfg.n,
        coef_error: recurrentGraphMetrics.coefError,
        share_error: recurrentGraphMetrics.shareError,
        girf_error: recurrentGraphMetrics.girfError,
        network_component_error: recurrentGraphMetrics.networkComponentError,
        frozen_counterfactual_error: recurrentGraphMetrics.frozenCounterfactualError,
        prediction_error: recurrentGraphMetrics.predictionError,
        runtime_seconds: (Date.now() - recurrentGraphStarted) / 1000,
        memory_mb: process.memoryUsage().rss / (1024 * 1024),
        instability_rate: recurrentGraphMetrics.instabilityRate,
        failure: recurrentGraphFailure,
      });
      }

      if (shouldRun(methods, "cp_nonnetwork") && !hasExisting("cp_nonnetwork", replication)) {
      const noNetStarted = Date.now();
      let noNetFailure = 0;
      let noNetMetrics = { coefError: NaN, shareError: NaN, girfError: NaN, networkComponentError: NaN, frozenCounterfactualError: NaN, predictionError: NaN, instabilityRate: NaN };
      try {
        const noNet = estimateLocalNoNetwork(sim.y, cfg.window);
        const cp = cpAls(noNet.tensor, cfg.rankEst, legacyNext);
        noNetMetrics = evaluateNoNetworkTensor(reconstructCp(cp.A, cp.B, cp.C), noNet.idxs, sim, cfg.horizon);
      } catch {
        noNetFailure = 1;
      }
      records.push({
        scenario: cfg.name,
        scenario_label: cfg.label,
        method: "cp_nonnetwork",
        replication,
        T: cfg.tLen,
        N: cfg.n,
        coef_error: noNetMetrics.coefError,
        share_error: noNetMetrics.shareError,
        girf_error: noNetMetrics.girfError,
        network_component_error: noNetMetrics.networkComponentError,
        frozen_counterfactual_error: noNetMetrics.frozenCounterfactualError,
        prediction_error: noNetMetrics.predictionError,
        runtime_seconds: (Date.now() - noNetStarted) / 1000,
        memory_mb: process.memoryUsage().rss / (1024 * 1024),
        instability_rate: noNetMetrics.instabilityRate,
        failure: noNetFailure,
      });
      }
      if (CHECKPOINT) writeBenchmarkOutputs(records);
    }
  }

  return writeBenchmarkOutputs(records);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const out = generateSyntheticBenchmarks();
  console.log(out);
}
