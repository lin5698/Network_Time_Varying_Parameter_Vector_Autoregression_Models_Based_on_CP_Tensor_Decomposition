# Nature Recent Corpus Access Audit

Date: 2026-07-15

Scope: Nature, Nature Communications and Nature Computational Science candidates recovered from `tmp/pdfs/nature_recent/` and the parent task's explicit reference DOI list. A candidate is `full_text` only when `file` identifies a PDF, `pdfinfo` returns pages, and `pdftotext` produces substantive text. HTML, login/challenge pages and truncated PDFs are not counted as full text.

## Summary

- 25 candidates have validated local PDF plus extracted text, totaling approximately 310,000 extracted words.
- 6 local PDF candidates still fail PDF integrity validation after the completed replacement run.
- No candidate is classified from publisher metadata or an HTML abstract when a validated PDF is absent.
- The parent task states 32 papers. Local evidence contains 28 candidate IDs plus four explicit reference IDs, with `s41467-024-45598-0` overlapping; this yields 31 unique DOI IDs. The 32nd DOI is not present in the current workspace or readable parent-thread evidence and is intentionally not guessed.

## Per-Article Records

| DOI/article ID | Access | Source URL | Pages | Text bytes | Verification/result |
|---|---|---|---:|---:|---|
| `10.1038/s41467-023-37019-5` | full_text | https://www.nature.com/articles/s41467-023-37019-5.pdf | 9 | 73128 | `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; text: `tmp/pdfs/nature_recent_text/s41467-023-37019-5.txt` |
| `10.1038/s41467-023-39999-w` | full_text | https://www.nature.com/articles/s41467-023-39999-w.pdf | 11 | 138761 | `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; text: `tmp/pdfs/nature_recent_text/s41467-023-39999-w.txt` |
| `10.1038/s41467-023-42868-1` | full_text | https://www.nature.com/articles/s41467-023-42868-1.pdf | 10 | 81448 | `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; text: `tmp/pdfs/nature_recent_text/s41467-023-42868-1.txt` |
| `10.1038/s41467-023-43120-6` | full_text | https://www.nature.com/articles/s41467-023-43120-6.pdf | 25 | 248776 | `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; text: `tmp/pdfs/nature_recent_text/s41467-023-43120-6.txt` |
| `10.1038/s41467-023-44257-0` | full_text | https://www.nature.com/articles/s41467-023-44257-0.pdf | 12 | 98111 | `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; text: `tmp/pdfs/nature_recent_text/s41467-023-44257-0.txt` |
| `10.1038/s41467-023-44599-9` | full_text | https://www.nature.com/articles/s41467-023-44599-9.pdf | 14 | 176982 | `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; text: `tmp/pdfs/nature_recent_text/s41467-023-44599-9.txt` |
| `10.1038/s41467-024-45323-x` | full_text | https://www.nature.com/articles/s41467-024-45323-x.pdf | 16 | 113617 | `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; text: `tmp/pdfs/nature_recent_text/s41467-024-45323-x.txt` |
| `10.1038/s41467-024-45598-0` | full_text | https://www.nature.com/articles/s41467-024-45598-0.pdf | 15 | 105003 | `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; also the overlapping explicit reference DOI |
| `10.1038/s41467-024-49207-y` | full_text | https://www.nature.com/articles/s41467-024-49207-y.pdf | 17 | 135423 | `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; text: `tmp/pdfs/nature_recent_text/s41467-024-49207-y.txt` |
| `10.1038/s41467-024-49411-w` | full_text | https://www.nature.com/articles/s41467-024-49411-w.pdf | 11 | 86002 | `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; text: `tmp/pdfs/nature_recent_text/s41467-024-49411-w.txt` |
| `10.1038/s41467-024-50918-5` | full_text | https://www.nature.com/articles/s41467-024-50918-5.pdf | 11 | 99182 | `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; text: `tmp/pdfs/nature_recent_text/s41467-024-50918-5.txt` |
| `10.1038/s41467-024-51477-5` | full_text | https://www.nature.com/articles/s41467-024-51477-5.pdf | 17 | 113258 | `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; text: `tmp/pdfs/nature_recent_text/s41467-024-51477-5.txt` |
| `10.1038/s41467-024-53303-4` | full_text | https://www.nature.com/articles/s41467-024-53303-4.pdf | 16 | 181031 | `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; text: `tmp/pdfs/nature_recent_text/s41467-024-53303-4.txt` |
| `10.1038/s41467-025-64984-w` | full_text | https://www.nature.com/articles/s41467-025-64984-w.pdf | 16 | 119955 | `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; text: `tmp/pdfs/nature_recent_text/s41467-025-64984-w.txt` |
| `10.1038/s41467-025-67802-5` | full_text | https://www.nature.com/articles/s41467-025-67802-5.pdf | 22 | 154859 | `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; text: `tmp/pdfs/nature_recent_text/s41467-025-67802-5.txt` |
| `10.1038/s43588-023-00431-4` | full_text | https://www.nature.com/articles/s43588-023-00431-4.pdf | 26 | 75596 | `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; text: `tmp/pdfs/nature_recent_text/s43588-023-00431-4.txt` |
| `10.1038/s43588-024-00732-2` | full_text | https://www.nature.com/articles/s43588-024-00732-2.pdf | 17 | 125804 | replacement `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; canonical text: `tmp/pdfs/nature_recent_text/s43588-024-00732-2.txt` |
| `10.1038/s41586-022-04959-9` | unavailable | https://www.nature.com/articles/s41586-022-04959-9.pdf | n/a | n/a | local PDF truncated (`xref num 559 not found`, missing endstream); official retry also timed out/partial |
| `10.1038/s41586-022-05688-9` | unavailable | https://www.nature.com/articles/s41586-022-05688-9.pdf | n/a | n/a | local PDF truncated (`xref num 2112 not found`, missing endstream); official retry partial |
| `10.1038/s41586-023-06139-9` | unavailable | https://www.nature.com/articles/s41586-023-06139-9.pdf | n/a | n/a | local PDF truncated (`xref num 871 not found`, missing endstream); retry failed validation |
| `10.1038/s41586-023-06184-4` | unavailable | https://www.nature.com/articles/s41586-023-06184-4.pdf | n/a | n/a | local PDF truncated (`xref num 904 not found`, missing endstream); retry partial |
| `10.1038/s41586-023-06185-3` | full_text | https://www.nature.com/articles/s41586-023-06185-3.pdf | 20 | 128552 | replacement `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; canonical text: `tmp/pdfs/nature_recent_text/s41586-023-06185-3.txt` |
| `10.1038/s41586-023-06970-0` | full_text | https://www.nature.com/articles/s41586-023-06970-0.pdf | 25 | 120932 | replacement `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; canonical text: `tmp/pdfs/nature_recent_text/s41586-023-06970-0.txt` |
| `10.1038/s41586-024-07939-3` | full_text | https://www.nature.com/articles/s41586-024-07939-3.pdf | 26 | 179789 | replacement `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; canonical text: `tmp/pdfs/nature_recent_text/s41586-024-07939-3.txt` |
| `10.1038/s43588-022-00217-0` | unavailable | https://www.nature.com/articles/s43588-022-00217-0.pdf | n/a | n/a | local PDF truncated (missing trailer/xref); Europe PMC reports no OA PDF |
| `10.1038/s43588-023-00429-y` | full_text | https://www.nature.com/articles/s43588-023-00429-y.pdf | 16 | 142962 | replacement `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; canonical text: `tmp/pdfs/nature_recent_text/s43588-023-00429-y.txt` |
| `10.1038/s43588-023-00465-8` | full_text | https://www.nature.com/articles/s43588-023-00465-8.pdf | 20 | 182424 | replacement `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; canonical text: `tmp/pdfs/nature_recent_text/s43588-023-00465-8.txt` |
| `10.1038/s43588-023-00509-z` | unavailable | https://www.nature.com/articles/s43588-023-00509-z.pdf | n/a | n/a | local PDF truncated (missing trailer/xref); Europe PMC reports no OA PDF |
| `10.1038/s41467-017-00148-9` | full_text | https://www.nature.com/articles/s41467-017-00148-9.pdf | 12 | 135984 | replacement `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; canonical text: `tmp/pdfs/nature_recent_text/s41467-017-00148-9.txt` |
| `10.1038/s41467-022-28123-z` | full_text | https://www.nature.com/articles/s41467-022-28123-z.pdf | 8 | 58150 | replacement `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; canonical text: `tmp/pdfs/nature_recent_text/s41467-022-28123-z.txt` |
| `10.1038/s41467-021-24732-2` | full_text | https://www.nature.com/articles/s41467-021-24732-2.pdf | 11 | 113531 | replacement `file=PDF`, `pdfinfo=PASS`, `pdftotext=PASS`; canonical text: `tmp/pdfs/nature_recent_text/s41467-021-24732-2.txt` |

## File Integrity Notes

The six invalid local PDFs remain clearly identified by their xref/trailer failures; no `.part` files remain. The older HTML-derived DIMON text is retained for provenance but is superseded by the validated PDF extraction. Existing manuscript, figures, experiments and findings were not modified by the access update.
