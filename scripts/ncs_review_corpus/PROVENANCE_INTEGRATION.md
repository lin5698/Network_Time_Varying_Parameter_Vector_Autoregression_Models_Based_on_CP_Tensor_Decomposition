# Future model-call provenance integration

This module is a future-call contract only. It does not reconstruct or backfill any historical Luna call.

## Receipt contents

`provenance.py` records the provider, model, reasoning setting, task and thread identifiers, canonical UTC invocation and completion times, logical input labels with SHA-256 digests, `prompt_sha256`, `schema_sha256`, `output_sha256`, a bounded validator result, and a status code. It never accepts a prompt body, response body, public-material body, secret, environment value, or filesystem path as receipt data. Input labels must be logical identifiers such as `public_source`; the source path is used only while hashing and is not serialized.

## Future call sequence

1. Before the provider call, capture `invoked_at = utc_now()` and derive input hashes with `hash_input_files({"public_source": source_path})`. Keep the prompt in memory and hash its UTF-8 bytes with `sha256_bytes`; hash the exact schema bytes and the exact raw output bytes that will be validated.
2. Call the provider through the existing caller. This change intentionally does not modify `luna.py` or `qwen_batch.py`.
3. After the call, capture `completed_at = utc_now()`. Convert validation to `{ "name": ..., "status": "PASS" | "FAIL", "error_count": ... }`; retain only bounded machine-readable codes if needed, never validator messages or excerpts.
4. Build with `create_receipt(...)` or `create_receipt_from_artifacts(...)`, run `verify_receipt_hashes(...)` with the same artifacts, and publish to a new destination with `write_receipt(...)`.

`write_receipt` validates the object, writes a same-directory temporary file, flushes and `fsync`s it, sets the temporary inode to mode `0400`, and then atomically hard-links it into place. A pre-existing destination, including one won by a concurrent writer, raises `FileExistsError`; receipts are never replaced in place. This is application-level write-once + read-only hardening: the API rejects replacement and the newly published receipt starts read-only. It is not an OS immutable flag, a signature, or a tamper-proof guarantee against users with sufficient privileges to modify or remove files.

## Storage boundary

Keep receipt destinations in a non-private audit directory and use one unique filename per call. The receipt itself contains no path, prompt, public document text, key, or environment value. Consumers that need to re-check provenance must supply the original artifacts separately to `verify_receipt_hashes`; they should not copy those artifacts into the receipt.

The current Luna and Qwen callers remain unchanged. A later integration should add receipt creation at their call boundaries and add a new test for that caller, without manufacturing a receipt for an earlier run.
