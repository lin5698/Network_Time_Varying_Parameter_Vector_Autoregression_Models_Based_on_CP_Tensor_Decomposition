import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const packageBuilder = fs.readFileSync(
  path.join(root, "scripts/create_natcs_figure_source_package.mjs"),
  "utf8",
);
const finalGates = fs.readFileSync(
  path.join(root, "scripts/check_natcs_final_gates.mjs"),
  "utf8",
);
const figureSourceRoot = path.join(
  root,
  "output/figure_source_package/natcs_main_figure_sources",
);

function collectTextFiles(dir) {
  if (!fs.existsSync(dir)) {
    return [];
  }
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      return collectTextFiles(fullPath);
    }
    if ([".json", ".md", ".svg", ".txt"].includes(path.extname(entry.name))) {
      return [fullPath];
    }
    return [];
  });
}

for (const name of [
  "figure1_callable_operator",
  "figure2_query_certificate",
  "figure3_supported_regime",
]) {
  assert.match(packageBuilder, new RegExp(name), `Figure package must include ${name}.`);
  assert.match(finalGates, new RegExp(name), `Final gate must expect ${name}.`);
}
assert.doesNotMatch(packageBuilder, /natcs_empirical_cp[\\/].*(?:rcep|nyc_taxi)/i);
for (const blockedSource of [
  "output/natcs_empirical_cp",
  "fig_rcep_operator_switch",
  "fig_nyc_portability_summary",
  "fig_validation_recovery",
  "build_natcs_fig2_portal_surrogate",
]) {
  assert.doesNotMatch(
    packageBuilder,
    new RegExp(blockedSource.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&")),
    `Active package must not bind blocked source ${blockedSource}.`,
  );
}
assert.match(packageBuilder, /active main manuscript figures/);

const activeFigureText = [
  packageBuilder,
  finalGates,
  ...collectTextFiles(figureSourceRoot).map((file) => fs.readFileSync(file, "utf8")),
].join("\n");

for (const pattern of [
  /\bE4-R008\b/i,
  /\bCAL-E01:75\b/i,
  /c96e620006d55b1459331c3ead28069920962ccf2df1a682030a37f47e97e635/i,
  /derived-panel-log-error-ratios/i,
  /response_log_error_ratio|operator_log_error_ratio/i,
  /response_cell_ci|operator_cell_ci/i,
  /response_panel_values|operator_panel_values/i,
  /log-error-ratio/i,
]) {
  assert.doesNotMatch(
    activeFigureText,
    pattern,
    `E4 derived log-ratio/CI material must remain outside active figures: ${pattern}`,
  );
}

console.log("Active three-figure package contract test passed.");
