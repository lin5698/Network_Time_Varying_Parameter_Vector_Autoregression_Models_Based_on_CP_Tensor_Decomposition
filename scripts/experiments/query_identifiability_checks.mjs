import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const OUTPUT_DIR = path.join(ROOT, "output", "high_impact_revision");
const JSON_PATH = path.join(OUTPUT_DIR, "query_identifiability_checks.json");
const MD_PATH = path.join(OUTPUT_DIR, "query_identifiability_checks.md");
const TOL = 1e-10;

function zeros(rows, cols) {
  return Array.from({ length: rows }, () => Array(cols).fill(0));
}

function identity(n) {
  const out = zeros(n, n);
  for (let i = 0; i < n; i += 1) out[i][i] = 1;
  return out;
}

function transpose(A) {
  return A[0].map((_, j) => A.map((row) => row[j]));
}

function matmul(A, B) {
  const Bt = transpose(B);
  return A.map((row) => Bt.map((col) => row.reduce((sum, x, i) => sum + x * col[i], 0)));
}

function add(A, B) {
  return A.map((row, i) => row.map((x, j) => x + B[i][j]));
}

function subtract(A, B) {
  return A.map((row, i) => row.map((x, j) => x - B[i][j]));
}

function scale(A, value) {
  return A.map((row) => row.map((x) => value * x));
}

function frobenius(A) {
  return Math.sqrt(A.reduce((total, row) => total + row.reduce((sum, x) => sum + x * x, 0), 0));
}

function kron(A, B) {
  const out = zeros(A.length * B.length, A[0].length * B[0].length);
  for (let i = 0; i < A.length; i += 1) {
    for (let j = 0; j < A[0].length; j += 1) {
      for (let r = 0; r < B.length; r += 1) {
        for (let c = 0; c < B[0].length; c += 1) {
          out[i * B.length + r][j * B[0].length + c] = A[i][j] * B[r][c];
        }
      }
    }
  }
  return out;
}

function matrixRank(A, tolerance = TOL) {
  if (A.length === 0) return 0;
  const M = A.map((row) => row.slice());
  let rank = 0;
  for (let col = 0; col < M[0].length && rank < M.length; col += 1) {
    let pivot = rank;
    for (let row = rank + 1; row < M.length; row += 1) {
      if (Math.abs(M[row][col]) > Math.abs(M[pivot][col])) pivot = row;
    }
    if (Math.abs(M[pivot][col]) <= tolerance) continue;
    [M[rank], M[pivot]] = [M[pivot], M[rank]];
    const divisor = M[rank][col];
    for (let j = col; j < M[0].length; j += 1) M[rank][j] /= divisor;
    for (let row = 0; row < M.length; row += 1) {
      if (row === rank) continue;
      const factor = M[row][col];
      for (let j = col; j < M[0].length; j += 1) M[row][j] -= factor * M[rank][j];
    }
    rank += 1;
  }
  return rank;
}

function stackRows(...matrices) {
  return matrices.flatMap((matrix) => matrix.map((row) => row.slice()));
}

function queryIsIdentifiable(storedMap, queryMap) {
  const storedRank = matrixRank(storedMap);
  const augmentedRank = matrixRank(stackRows(storedMap, queryMap));
  return { identifiable: storedRank === augmentedRank, storedRank, augmentedRank };
}

function firstOrderDifferenceMap(W, W0) {
  return kron(transpose(subtract(W, W0)), identity(W.length));
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function singleTopologyCounterexample() {
  const A = [[0.25, -0.05], [0.02, 0.18]];
  const B = [[0.08, 0.03], [-0.04, 0.06]];
  const H = [[0.30, -0.10], [0.20, 0.40]];
  const W0 = [[0, 1], [1, 0]];
  const W1 = [[0, 0.70], [0.30, 0]];
  const AAlt = subtract(A, matmul(H, W0));
  const BAlt = add(B, H);
  const D0 = add(A, matmul(B, W0));
  const D0Alt = add(AAlt, matmul(BAlt, W0));
  const D1 = add(A, matmul(B, W1));
  const D1Alt = add(AAlt, matmul(BAlt, W1));
  const storedGap = frobenius(subtract(D0, D0Alt));
  const endpointGap = frobenius(subtract(D1, D1Alt));
  assert(storedGap <= TOL, `Equivalent blocks do not match at stored topology: ${storedGap}`);
  assert(endpointGap > 1e-3, `Counterexample endpoint gap is too small: ${endpointGap}`);
  return { stored_gap: storedGap, target_endpoint_gap: endpointGap, pass: true };
}

function partialQueryCases() {
  const W0 = zeros(2, 2);
  const WObserved = [[1, 0], [0, 0]];
  const WGood = scale(WObserved, 2);
  const WBad = [[0, 0], [0, 1]];
  const storedMap = firstOrderDifferenceMap(WObserved, W0);
  const good = queryIsIdentifiable(storedMap, firstOrderDifferenceMap(WGood, W0));
  const bad = queryIsIdentifiable(storedMap, firstOrderDifferenceMap(WBad, W0));
  assert(storedMap.length > 0 && good.storedRank === 2, `Unexpected partial stored rank: ${good.storedRank}`);
  assert(good.identifiable, "A query in the stored row space should be identifiable");
  assert(!bad.identifiable, "A query outside the stored row space should not be identifiable");
  return {
    stored_rank: good.storedRank,
    parameter_dimension: 4,
    full_parameter_identified: good.storedRank === 4,
    in_span_query: good,
    out_of_span_query: bad,
    pass: true,
  };
}

function fullIdentificationCase() {
  const W0 = zeros(2, 2);
  const WObserved = identity(2);
  const WTarget = [[0.2, 0.8], [0.6, 0.4]];
  const storedMap = firstOrderDifferenceMap(WObserved, W0);
  const result = queryIsIdentifiable(storedMap, firstOrderDifferenceMap(WTarget, W0));
  assert(result.storedRank === 4, `Expected full rank 4, found ${result.storedRank}`);
  assert(result.identifiable, "Full block identification should identify every linear topology query");
  return { ...result, parameter_dimension: 4, pass: true };
}

const report = {
  generated_at: new Date().toISOString(),
  theorem_checked: "ker(S) subset ker(T*) iff rank([S; T*]) equals rank(S)",
  tolerance: TOL,
  runs: {
    R001_single_topology_counterexample: singleTopologyCounterexample(),
    R002_partial_query_identification: partialQueryCases(),
    R002_full_block_identification: fullIdentificationCase(),
  },
};

report.status = Object.values(report.runs).every((run) => run.pass) ? "PASS" : "FAIL";
fs.mkdirSync(OUTPUT_DIR, { recursive: true });
fs.writeFileSync(JSON_PATH, `${JSON.stringify(report, null, 2)}\n`);

const partial = report.runs.R002_partial_query_identification;
const markdown = `# Query Identifiability Checks

- Status: **${report.status}**
- Theorem checked: \`${report.theorem_checked}\`
- Numerical rank tolerance: \`${report.tolerance}\`

| Run | Expected result | Observed result | Status |
| --- | --- | --- | --- |
| R001 single stored topology | Same stored map, different target endpoint | stored gap ${report.runs.R001_single_topology_counterexample.stored_gap.toExponential(3)}; endpoint gap ${report.runs.R001_single_topology_counterexample.target_endpoint_gap.toFixed(6)} | PASS |
| R002 partial query | Full block not identified; in-span query identified | stored rank ${partial.stored_rank}/4; query identifiable ${partial.in_span_query.identifiable} | PASS |
| R002 out-of-span query | Query not identified | augmented rank ${partial.out_of_span_query.augmentedRank} > stored rank ${partial.out_of_span_query.storedRank} | PASS |
| R002 full block | Every linear topology query identified | stored rank ${report.runs.R002_full_block_identification.storedRank}/4 | PASS |

These are deterministic linear-algebra checks. They validate the exact kernel condition and do not constitute statistical recovery evidence.
`;

fs.writeFileSync(MD_PATH, markdown);
process.stdout.write(`${JSON.stringify({ status: report.status, json: path.relative(ROOT, JSON_PATH), markdown: path.relative(ROOT, MD_PATH) }, null, 2)}\n`);
