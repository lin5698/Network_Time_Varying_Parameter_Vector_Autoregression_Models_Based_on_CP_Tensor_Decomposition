from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.shared import Inches, Pt

from natcs_evidence import (
    build_rcep_benchmark_table,
    build_simulation_table,
    build_summary_metrics,
    write_evidence_bundle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DOC = ROOT / "Network Time-Varying Parameter Vector Autoregression Models Based on CP Tensor Decomposition-20260327-084902-27.docx"
TARGET_DOC = ROOT / "Network Time-Varying Parameter Vector Autoregression Models Based on CP Tensor Decomposition-20260327-211038-28.docx"
TMP_DIR = ROOT / "tmp" / "docs" / "natcs_rebuild"
TMP_DIR.mkdir(parents=True, exist_ok=True)

FRAMEWORK_FIG = ROOT / "Figure1_network_tvp_var_framework_redesign.png"
VALIDATION_FIG = TMP_DIR / "Fig2_validation_recovery.png"
TARIFF_FIG = ROOT / "tmp" / "rcep_repo" / "repo" / "research_output" / "nature_figures" / "Fig_Tariff_Phase_ins_Final.png"
AMPLIFICATION_FIG = ROOT / "tmp" / "rcep_repo" / "repo" / "research_output" / "nature_figures" / "Fig_Resilience_Measures_Intervals.png"
GIRF_FIG = ROOT / "tmp" / "rcep_repo" / "repo" / "research_output" / "nature_figures" / "Fig_TVP_GIRFs_Intervals.png"
FIXED_VS_TV_FIG = ROOT / "tmp" / "rcep_repo" / "repo" / "research_output" / "nature_figures" / "Fig_Resilience_Trends_Fixed_vs_TV.png"


def style_name(doc: Document, preferred: str, fallback: str = "Normal") -> str:
    try:
        doc.styles[preferred]
        return preferred
    except KeyError:
        return fallback


def clear_document(doc: Document) -> None:
    body = doc._element.body
    sect_pr = body.sectPr
    for child in list(body):
        if child is not sect_pr:
            body.remove(child)


def set_run_font(paragraph, size: int = 10) -> None:
    for run in paragraph.runs:
        run.font.name = "Times New Roman"
        run.font.size = Pt(size)


def add_paragraph(doc: Document, text: str, style: str, align=None, font_size: int | None = None):
    p = doc.add_paragraph(style=style)
    p.add_run(text)
    if align is not None:
        p.alignment = align
    if font_size is not None:
        set_run_font(p, font_size)
    return p


def add_heading(doc: Document, text: str, level: int = 1):
    style = style_name(doc, f"Heading {level}")
    return add_paragraph(doc, text, style)


def add_figure(doc: Document, image_path: Path, caption: str, width: float = 6.2):
    spacer = doc.add_paragraph(style=style_name(doc, "Captioned Figure", "Normal"))
    spacer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = spacer.add_run()
    run.add_picture(str(image_path), width=Inches(width))
    cap = add_paragraph(doc, caption, style_name(doc, "Image Caption", "Normal"))
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(cap, 9)


def format_float(x: float, digits: int = 3) -> str:
    if pd.isna(x):
        return ""
    return f"{x:.{digits}f}"


def format_small(x: float) -> str:
    if pd.isna(x):
        return ""
    if abs(x) >= 0.001:
        return f"{x:.6f}"
    return f"{x:.3e}"


def add_table(doc: Document, df: pd.DataFrame, caption: str, note: str | None = None):
    table = doc.add_table(rows=1, cols=len(df.columns))
    try:
        table.style = "Table Grid"
    except KeyError:
        pass
    hdr = table.rows[0].cells
    for i, col in enumerate(df.columns):
        hdr[i].text = str(col)
    for _, row in df.iterrows():
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = "" if pd.isna(value) else str(value)
    for row in table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(9)
    cap = add_paragraph(doc, caption, style_name(doc, "Image Caption", "Normal"))
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(cap, 9)
    if note:
        n = add_paragraph(doc, note, style_name(doc, "Body Text", "Normal"))
        set_run_font(n, 9)


def extract_references(source_doc: Path) -> list[str]:
    doc = Document(source_doc)
    refs = []
    in_refs = False
    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        if text == "8 References":
            in_refs = True
            continue
        if in_refs and text.startswith("9 Appendix"):
            break
        if in_refs:
            refs.append(text)
    return refs


def build_validation_figure() -> None:
    df = pd.read_csv(ROOT / "monte_carlo_cp_network_tvp_var_results.csv")

    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.2))
    x = df["T"].to_numpy()

    axes[0].plot(x, df["coef_error_raw_mean"], marker="o", lw=2.4, color="#c65f0a", label="Local rolling estimate")
    axes[0].plot(x, df["coef_error_cp_mean"], marker="o", lw=2.4, color="#1f77b4", label="Low-rank CP estimate")
    axes[0].set_title("a. Coefficient recovery error", fontsize=12, loc="left", fontweight="bold")
    axes[0].set_xlabel("Sample size T")
    axes[0].set_ylabel("Relative Frobenius error")
    axes[0].grid(alpha=0.2)
    axes[0].legend(frameon=False, fontsize=9)

    axes[1].plot(x, df["share_error_raw_mean"], marker="o", lw=2.4, color="#c65f0a", label="Local rolling estimate")
    axes[1].plot(x, df["share_error_cp_mean"], marker="o", lw=2.4, color="#1f77b4", label="Low-rank CP estimate")
    axes[1].set_title("b. Network-share recovery error", fontsize=12, loc="left", fontweight="bold")
    axes[1].set_xlabel("Sample size T")
    axes[1].set_ylabel("Absolute error")
    axes[1].grid(alpha=0.2)
    axes[1].legend(frameon=False, fontsize=9)

    fig.suptitle("Simulation benchmark for low-rank compression of time-varying network dynamics", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(VALIDATION_FIG, dpi=300, bbox_inches="tight")
    plt.close(fig)


def build_table_1() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "monte_carlo_cp_network_tvp_var_results.csv")
    out = pd.DataFrame(
        {
            "T": df["T"].astype(int),
            "Replications": df["replications"].astype(int),
            "Local coef. error": df["coef_error_raw_mean"].map(lambda x: format_float(x, 3)),
            "Low-rank coef. error": df["coef_error_cp_mean"].map(lambda x: format_float(x, 3)),
            "Coef. gain (%)": df["coef_error_improvement_pct"].map(lambda x: format_float(x, 1)),
            "Local share error": df["share_error_raw_mean"].map(lambda x: format_float(x, 3)),
            "Low-rank share error": df["share_error_cp_mean"].map(lambda x: format_float(x, 3)),
            "Share gain (%)": df["share_error_improvement_pct"].map(lambda x: format_float(x, 1)),
        }
    )
    return out


def build_table_2() -> tuple[pd.DataFrame, float, float]:
    net = pd.read_csv(ROOT / "tmp" / "rcep_repo" / "repo" / "research_output" / "nature_figures" / "Table_Network_Robustness_Final.csv")
    fixed = pd.read_csv(ROOT / "tmp" / "rcep_repo" / "repo" / "research_output" / "nature_figures" / "Table_Baseline_FixedWeight_Stability.csv")
    full = pd.read_csv(ROOT / "tmp" / "rcep_repo" / "repo" / "research_output" / "nature_figures" / "Table_Tariff_Resilience_Full.csv")

    rows = [
        ["Alternative W", "Import-based W_t", net.loc[0, "Coefficient"], net.loc[0, "Std.Err"], net.loc[0, "p-value"], int(net.loc[0, "N"])],
        ["Alternative W", "Export-based W_t", net.loc[1, "Coefficient"], net.loc[1, "Std.Err"], net.loc[1, "p-value"], int(net.loc[1, "N"])],
        ["Alternative W", "Symmetric W_t", net.loc[2, "Coefficient"], net.loc[2, "Std.Err"], net.loc[2, "p-value"], int(net.loc[2, "N"])],
        ["Alternative W", "Eight-quarter W_t", net.loc[3, "Coefficient"], net.loc[3, "Std.Err"], net.loc[3, "p-value"], int(net.loc[3, "N"])],
        ["Topology benchmark", "Evolving topology W_t", fixed.loc[0, "beta_TC_relief"], fixed.loc[0, "se"], fixed.loc[0, "p_value"], int(fixed.loc[0, "N"])],
        ["Topology benchmark", "Frozen topology W_pre", fixed.loc[1, "beta_TC_relief"], fixed.loc[1, "se"], fixed.loc[1, "p_value"], int(fixed.loc[1, "N"])],
        ["Inference sensitivity", "Horizon H=12", full.loc[1, "Coefficient"], full.loc[1, "Std.Err"], full.loc[1, "p-value"], int(full.loc[1, "N"])],
        ["Inference sensitivity", "Two-way clustered SE", full.loc[2, "Coefficient"], full.loc[2, "Std.Err"], full.loc[2, "p-value"], int(full.loc[2, "N"])],
    ]
    df = pd.DataFrame(rows, columns=["Panel", "Specification", "Coefficient", "Std. Err.", "p-value", "N"])
    for col in ["Coefficient", "Std. Err."]:
        df[col] = df[col].map(format_small)
    df["p-value"] = df["p-value"].map(lambda x: format_float(x, 3))

    reg = pd.read_csv(ROOT / "tmp" / "rcep_repo" / "repo" / "research_output" / "pairwise_regression_data_full.csv")
    reg = reg[(reg["H"] == 8) & (reg["W_type"] == "Time-Varying")].copy()
    beta = float(net.loc[0, "Coefficient"])
    iqr = float(reg["TC_relief"].quantile(0.75) - reg["TC_relief"].quantile(0.25))
    effect = beta * iqr
    baseline_mean = float(reg["A"].mean())
    return df, effect, baseline_mean


def add_bookmark_break(doc: Document) -> None:
    p = doc.add_paragraph()
    run = p.add_run()
    br = OxmlElement("w:br")
    br.set(docx_ns("type"), "page")
    run._r.append(br)


def docx_ns(tag: str) -> str:
    return f"{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}{tag}"


def build_doc() -> None:
    evidence_outputs = write_evidence_bundle(ROOT / "output" / "natcs_evidence")
    refs = extract_references(SOURCE_DOC)
    table1 = build_simulation_table()
    table2 = build_rcep_benchmark_table()
    summary = build_summary_metrics()
    effect_iqr = summary["effect_size_translation"]["effect_for_iqr"]
    baseline_mean = summary["effect_size_translation"]["s_net_clip_mean"]
    pre_a = summary["aggregate_bootstrap_shift"]["pre_2022_g_net_p50_mean"]
    post_a = summary["aggregate_bootstrap_shift"]["post_2022_g_net_p50_mean"]
    girf_pre = summary["girf_network_contribution"]["2018-12-31"]["mean"]
    girf_post = summary["girf_network_contribution"]["2022-12-31"]["mean"]
    break_dates = str(summary["structural_breaks"][0]["break_dates"]).replace("; ", " and ")
    validation_figure = Path(evidence_outputs["validation_figure"])

    doc = Document(str(TARGET_DOC))
    clear_document(doc)

    title_style = style_name(doc, "Title")
    author_style = style_name(doc, "Author", "Normal")
    normal_style = style_name(doc, "Normal")
    abstract_title_style = style_name(doc, "Abstract Title", "Heading 1")
    abstract_style = style_name(doc, "Abstract", "Normal")
    first_style = style_name(doc, "First Paragraph", "Normal")
    body_style = style_name(doc, "Body Text", "Normal")

    add_paragraph(
        doc,
        "Topology-switchable propagation in dynamic networks",
        title_style,
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )
    add_paragraph(doc, "Yilin WU", author_style, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_paragraph(doc, "Overseas Education College, Fujian Business University, Fuzhou 350012, China", normal_style, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=10)
    add_paragraph(doc, "Correspondence should be addressed to Y.W.", normal_style, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=10)

    add_paragraph(doc, "Abstract", abstract_title_style)
    abstract_text = (
        "Dynamic-network smoothing can stabilize time-varying estimates at the cost of removing the topology needed "
        "to compare propagation under alternative network structures. We present a reconstruction criterion that "
        "preserves this topology argument, allowing one fitted path to generate observed-topology, direct-only and "
        "frozen-topology responses. The retained operator is M_{k,t}(W)=A_{k,t}+B_{k,t}W, reconstructed from separated "
        "direct and network coefficient blocks. Synthetic benchmarks test switchable-operator recovery against "
        "unrestricted rolling estimation and reduced-form ablations. RCEP trade networks and a public NYC Taxi panel "
        "then test whether the same readouts remain available in empirical weighted networks."
    )
    add_paragraph(doc, abstract_text, abstract_style)

    add_heading(doc, "Introduction", 1)
    intro_paras = [
        (
            "Many networked dynamical systems evolve on weighted graphs whose edges and transmission coefficients both "
            "change over time. The resulting estimation problem appears in regional trade, supply chains, mobility "
            "networks, epidemic contact systems, ecological interaction matrices, and energy exchange networks. "
            "The problem is to preserve the distinction between direct persistence and network-mediated propagation "
            "after smoothing a time-varying response path."
        ),
        (
            "Existing approaches solve only part of that problem. Unrestricted TVP-VARs allow flexible coefficient "
            "drift but scale poorly once own lags, cross-unit lags, and covariance terms all vary jointly [4-6,11,12,14]. "
            "Spatial and GVAR-style models impose useful structure on interdependence [1,3,10,15,16], but they are not "
            "designed to recover a multihorizon decomposition between direct and lagged network-mediated transmission. "
            "Related low-rank autoregressive models in spatiotemporal learning compress dynamics efficiently [19], yet "
            "they typically target generic pattern discovery rather than an explicit direct-versus-network propagation block."
        ),
        (
            "The framework developed here addresses that gap by keeping the lagged network channel explicit and reducing "
            "coefficient drift through CP tensor decomposition. The paper makes two claims. First, low-rank compression "
            "improves recovery of time-varying network propagation relative to unrestricted local estimates in simulated "
            "systems. Second, when the framework is applied to the RCEP trade network, tariff-relief episodes coincide "
            "with a larger estimated share of trade-shock adjustment transmitted through evolving network linkages. The "
            "methodological emphasis is broader than the RCEP application: the trade system serves as a concrete testbed "
            "for a general computational problem."
        ),
        (
            "The RCEP case study is useful because trade policy changes produce a setting in which the propagation margin "
            "is economically meaningful. The policy question is not simply whether tariff reductions altered bilateral trade, "
            "but whether they coincided with a change in the fraction of adjustment carried by regional network propagation. "
            "That question sits near quantitative trade and value-added trade work [20,21], but the present paper focuses "
            "on propagation measurement rather than on a complete structural evaluation of trade policy."
        ),
    ]
    for idx, text in enumerate(intro_paras):
        add_paragraph(doc, text, first_style if idx == 0 else body_style)

    add_heading(doc, "Results", 1)

    add_heading(doc, "Framework overview and intuition", 2)
    framework_paras = [
        (
            "The model starts from a multivariate system in which each unit responds to its own lags and to lagged "
            "network exposures constructed from a predetermined weighted matrix W_t. This separation is essential. "
            "It makes the network channel observable on the regressor side and leaves open a clean counterfactual in "
            "which network-mediated propagation can be shut down while direct persistence remains active."
        ),
        (
            "To keep the system estimable as the number of units and horizons increases, the drifting coefficient array "
            "is summarized by a small number of CP components. In practical terms, the low-rank representation treats "
            "time variation as movement in a few propagation modes rather than unrestricted drift in every entry of the "
            "full coefficient tensor. That compression is what allows the model to preserve interpretability without "
            "absorbing the network channel into an opaque high-dimensional state."
        ),
    ]
    for idx, text in enumerate(framework_paras):
        add_paragraph(doc, text, first_style if idx == 0 else body_style)
    add_figure(
        doc,
        FRAMEWORK_FIG,
        "Figure 1 | Computational workflow of the network TVP-VAR. The lagged network block remains explicit throughout estimation, propagation analysis, and counterfactual decomposition.",
        width=6.6,
    )

    add_heading(doc, "Validation and benchmarking", 2)
    validation_paras = [
        (
            "The current repository implements the framework through a rolling network estimator, CP compression of the "
            "time-varying coefficient array, and bootstrap-based uncertainty summaries. Validation therefore focuses on the "
            "objects that this implementation actually produces: coefficient recovery, recovery of the network-amplification "
            "share, and period-specific response summaries."
        ),
        (
            "In simulated network systems, low-rank compression improves both coefficient recovery and recovery of the "
            "network-amplification share relative to unrestricted local rolling estimates. Across T = 80, 120, and 160, "
            "the mean coefficient error falls by roughly 24-33%, while network-share error falls by roughly 13-20%. "
            "These gains support preserved-object recovery in the simulated data-generating processes evaluated here."
        ),
        (
            "Bootstrap exercises complement the simulation benchmark by quantifying uncertainty in the empirical first-stage "
            "objects. The aggregate network-amplification share and the representative generalized impulse responses both "
            "exhibit visibly wider intervals at precisely the periods where the propagation environment is changing most "
            "rapidly. That pattern is consistent with a method that is reacting to changing topology rather than smoothing it away."
        ),
    ]
    for idx, text in enumerate(validation_paras):
        add_paragraph(doc, text, first_style if idx == 0 else body_style)
    add_table(
        doc,
        table1,
        "Table 1 | Simulation benchmark for low-rank recovery of time-varying network dynamics.",
        note=(
            "Entries summarize 100 replications of rolling-network simulations. Local estimates refer to unrestricted "
            "rolling coefficient recovery before CP compression; low-rank estimates apply CP factorization to the same "
            "time-varying coefficient tensor."
        ),
    )
    add_figure(
        doc,
        validation_figure,
        "Figure 2 | Object-defined recovery in synthetic network benchmarks. The figure records available readouts by fitted object, then reports operator recovery, network-component GIRF recovery, frozen-topology error and instability.",
        width=6.3,
    )

    add_heading(doc, "RCEP case study", 2)
    rcep_paras = [
        (
            "The empirical demonstration uses quarterly observations for the 15 RCEP economies from 2005Q4 to 2024Q4. "
            "Network exposure is constructed from lagged bilateral trade weights, and the policy regressor tracks tariff "
            "relief along the RCEP implementation path. The key empirical quantity is the network-amplification share A, "
            "which measures the fraction of cumulative response attributable to the lagged network channel rather than to "
            "direct persistence alone."
        ),
        (
            "The policy variation is economically non-trivial. Representative bilateral tariff phase-ins become visible only "
            "after the agreement takes effect, and the cross-pair distribution of relief is heterogeneous rather than uniform. "
            "That heterogeneity makes the RCEP setting suitable as a demonstration of time-varying propagation measurement."
        ),
        (
            "Across import-based, export-based, symmetric, and longer-window network definitions, tariff relief is positively "
            "associated with the estimated network-amplification share. In the baseline import-share specification, the coefficient "
            "is 0.001081 with a standard error of 0.000432. Using the observed interquartile range of the pair-level tariff-relief "
            f"regressor, this corresponds to an increase of approximately {effect_iqr:.4f} in A, or about {100.0 * effect_iqr / baseline_mean:.1f}% "
            "of the sample mean amplification share."
        ),
        (
            "On the fixed reconstructed path, the frozen-topology readout attenuates the pair-level association. "
            "The re-estimated interval crosses zero, so this is topology-sensitive measurement evidence rather than causal policy evidence."
        ),
        (
            "The dynamic first-stage objects move in the same direction. In the bootstrapped aggregate series, the median network-"
            f"amplification share rises from about {pre_a:.2f} before 2022Q1 to about {post_a:.2f} after 2022Q1, and the mean "
            f"network contribution to the cumulative illustrative GIRF increases from about {girf_pre:.2f} in 2018Q4 to about "
            f"{girf_post:.2f} in 2022Q4. Structural-break tests place major shifts in the aggregate propagation series around "
            f"{break_dates}, which is consistent with a changing network environment before and around formal implementation."
        ),
    ]
    for idx, text in enumerate(rcep_paras):
        add_paragraph(doc, text, first_style if idx == 0 else body_style)
    add_figure(
        doc,
        TARIFF_FIG,
        "Figure 3 | Representative RCEP tariff phase-ins. The left panel shows selected bilateral implementation paths; the right panel shows the cross-pair distribution of tariff relief.",
        width=6.3,
    )
    add_table(
        doc,
        table2,
        "Table 2 | RCEP network-propagation association and benchmark comparisons.",
        note=(
            "The table combines alternative network constructions, the frozen-topology benchmark, and two inferential sensitivity checks. "
            "The coefficient always refers to the association between tariff relief and the estimated network-amplification share A."
        ),
    )
    add_figure(
        doc,
        AMPLIFICATION_FIG,
        "Figure 4 | Aggregate network-amplification share and half-life over time with bootstrap intervals. The dashed line marks RCEP implementation.",
        width=6.3,
    )
    add_figure(
        doc,
        GIRF_FIG,
        "Figure 5 | Representative total and direct GIRFs before and during RCEP implementation. The gap between total and direct responses measures the contribution of network propagation.",
        width=6.3,
    )
    add_figure(
        doc,
        FIXED_VS_TV_FIG,
        "Figure 6 | Fixed-topology benchmark versus evolving topology. The fixed-path readout compares observed topology with the pre-RCEP benchmark topology.",
        width=6.3,
    )

    add_heading(doc, "Generality beyond trade networks", 2)
    add_paragraph(
        doc,
        "Although the case study is regional trade, the computational target is broader. The same estimation problem appears when "
        "mobility networks reshape epidemic transmission, when ecological interaction strengths change across seasons, when supply-chain "
        "dependencies shift after disruptions, or when power-trade and fuel-exchange networks rewire under policy shocks. In each case "
        "the practical requirement is the same: preserve a meaningful propagation channel while controlling the dimensionality of "
        "time-varying multivariate dynamics.",
        first_style,
    )

    add_heading(doc, "Discussion", 1)
    discussion_paras = [
        (
            "The main contribution of the paper is computational. It shows how to preserve a lagged network-propagation block inside a "
            "time-varying multivariate system while compressing coefficient drift into a small number of low-rank modes. That combination "
            "produces interpretable propagation objects - total responses, direct responses, network contributions, and amplification shares - "
            "without collapsing the network channel into an undifferentiated latent state."
        ),
        (
            "The RCEP application demonstrates why the distinction matters. The empirical signal is strongest when topology is allowed to evolve, "
            "and it attenuates when the network is fixed at its pre-entry structure. This is consistent with a propagation interpretation: the "
            "post-entry environment is not captured by time variation in direct persistence alone."
        ),
        (
            "Two limitations remain material. First, the current implementation validates low-rank recovery through rolling-network simulations "
            "and bootstrap summaries rather than through a fully integrated Bayesian estimator benchmark. Second, the pair-level policy association "
            "depends on quarterlyized value-added trade series and remains sensitive to some inferential choices, including two-way clustered "
            "standard errors and alternative temporal disaggregation. For those reasons, the paper should be read as a methods paper with a single "
            "empirical demonstration rather than as a definitive causal evaluation of RCEP trade policy."
        ),
    ]
    for idx, text in enumerate(discussion_paras):
        add_paragraph(doc, text, first_style if idx == 0 else body_style)

    add_heading(doc, "Methods", 1)
    method_sections = [
        (
            "Quarterly RCEP panel and source blocks",
            "The empirical panel combines four source blocks: quarterly macro indicators from IMF IFS and national statistical offices, annual "
            "multi-regional input-output information used to construct value-added trade proxies, official RCEP tariff schedules, and bilateral "
            "import data used for network weights. The analysis covers the 15 RCEP economies from 2005Q4 to 2024Q4. The value-added trade outcome "
            "is quarterlyized from annual benchmarks, and the current implementation retains direct gross-trade alternatives and quarterlyization "
            "stress tests as robustness checks.",
        ),
        (
            "Predetermined network construction",
            "At each quarter t, the trade network is constructed from lagged bilateral import shares observed before the innovation at t. The "
            "baseline matrix uses a four-quarter window, imposes a zero diagonal, and applies row normalization. This timing ensures that the "
            "matrix used to form W_t y_{t-k} is measurable with respect to information available before the shock at t. Alternative export-based, "
            "symmetric, and longer-window definitions are used in the robustness block.",
        ),
        (
            "Network TVP-VAR and low-rank compression",
            "The main system is y_t = c_t + sum_k A_{k,t} y_{t-k} + sum_k B_{k,t} W_t y_{t-k} + C_t x_t + eps_t. The array formed by stacking "
            "the time-varying lag coefficients across variables, channels, and time is summarized with a CP tensor representation. The purpose "
            "of the factorization is not generic dimension reduction alone; it is to retain a separate network block while replacing unrestricted "
            "entrywise drift with a small number of propagation modes.",
        ),
        (
            "Propagation objects",
            "For each date, the estimated coefficient blocks generate period-specific moving-average objects and generalized impulse responses. "
            "A direct counterfactual is obtained by setting the lagged network block B to zero while holding the direct lag block fixed. The "
            "network-amplification share A is defined as the fraction of cumulative response attributable to the difference between the total and "
            "direct systems. The paper also reports half-life summaries and representative GIRFs at benchmark dates.",
        ),
        (
            "Estimation and uncertainty",
            "The current repository implementation estimates time variation through rolling network regressions and then summarizes coefficient "
            "drift through CP compression. Uncertainty in the first-stage propagation objects is obtained from bootstrap resampling of the rolling "
            "estimation pipeline, which produces the aggregate interval plots and the GIRF bands reported in the Results section. This implementation "
            "does not yet provide a fully integrated Bayesian benchmark table, which is why the paper frames the validation evidence at the level "
            "of rolling-network recovery and bootstrap stability.",
        ),
        (
            "Empirical association design",
            "The second-stage association relates the pair-level network-amplification share to tariff relief with pair and time effects. The "
            "main reported result uses the import-based evolving network at horizon H = 8. The benchmark comparisons alter the network definition, "
            "replace W_t with its pre-RCEP counterpart W_pre, or vary the inferential design. The purpose of this layer is not to claim a complete "
            "policy-identification design, but to test whether the propagation measure moves systematically with the tariff-relief margin.",
        ),
        (
            "Implementation details",
            "The rolling estimator uses p = 2 lags and a minimum training window of 40 quarters in the released scripts. The simulation benchmark "
            "reported in Table 1 uses 100 replications at T = 80, 120, and 160. Bootstrap summaries use the repository outputs stored in "
            "rolling_resilience_bootstrapped.csv and girf_bootstrap_data.json. Full derivations, selection-matrix identities, and additional "
            "robustness tables are intended for Supplementary Information rather than the main manuscript.",
        ),
    ]
    for head, text in method_sections:
        add_heading(doc, head, 2)
        add_paragraph(doc, text, first_style)

    add_heading(doc, "References", 1)
    for i, ref in enumerate(refs):
        add_paragraph(doc, ref, first_style if i == 0 else body_style)

    add_heading(doc, "Data availability", 1)
    add_paragraph(
        doc,
        "The analysis uses public or licensed source material drawn from IMF International Financial Statistics, national statistical offices, "
        "annual multi-regional input-output tables, official RCEP tariff schedules, and bilateral import data. The assembled peer-review archive "
        "contains the derived evidence objects, metadata, and scripts required to reproduce the manuscript-facing figures and tables. It is "
        "available to editors and reviewers through the journal-approved submission or file-transfer route. On acceptance, the authors will "
        "deposit the redistributable code-and-derived-evidence release in a DOI-minting repository.",
        first_style,
    )

    add_heading(doc, "Code availability", 1)
    add_paragraph(
        doc,
        "The code used for data construction, network formation, rolling estimation, bootstrap summaries, and figure generation is included in the "
        "assembled peer-review archive for editor and reviewer access through the journal-approved submission or file-transfer route. On acceptance, "
        "the authors will deposit the redistributable release in a DOI-minting repository and insert the persistent identifier before publication.",
        first_style,
    )

    add_heading(doc, "Author contributions", 1)
    add_paragraph(
        doc,
        "Y.W. conceived the study, designed the methodology, curated the data, implemented the computational workflow, "
        "produced the empirical results, and wrote and approved the final manuscript.",
        first_style,
    )

    add_heading(doc, "Competing interests", 1)
    add_paragraph(doc, "The authors declare no competing interests.", first_style)

    add_heading(doc, "Acknowledgements", 1)
    add_paragraph(
        doc,
        "This work was supported by the Natural Science Foundation of Fujian Province (Grant No. 2025J011145).",
        first_style,
    )

    doc.save(str(TARGET_DOC))


if __name__ == "__main__":
    build_doc()
