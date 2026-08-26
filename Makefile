natcs-evidence:
	node scripts/build_natcs_evidence.mjs

natcs-manuscript:
	node scripts/build_natcs_manuscript.mjs
	node scripts/finalize_natcs_package.mjs
	node scripts/create_natcs_figure_source_package.mjs

natcs-figure-source-package:
	node scripts/create_natcs_figure_source_package.mjs

natcs-reviewer-archive:
	node scripts/build_natcs_reviewer_archive.mjs

natcs-upload-freeze-manifest:
	node scripts/create_natcs_upload_freeze_manifest.mjs

natcs-release-safety-audit:
	node scripts/audit_natcs_release_safety.mjs

natcs-final-gate-check:
	node scripts/check_natcs_final_gates.mjs

natcs-source-only-gate-check:
	node scripts/check_natcs_source_only_gates.mjs
