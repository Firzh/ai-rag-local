# Commit Titles

## Commit utama yang disarankan

```text
docs(rag): align boundary, status, and docs maintenance cadence
```

## Alternatif bila sekaligus mengarsipkan dokumentasi lama

```text
docs(rag): add boundary docs and archive stale planning notes
```

## Alternatif bila hanya menambahkan aturan 9+1 commit

```text
docs(rag): add implementation-to-documentation commit cadence
```

## Format commit berikutnya

Gunakan format berikut untuk siklus pengembangan:

```text
feat(rag): implement <scope kecil>
fix(rag): repair <bug spesifik>
test(rag): add <test coverage>
docs(rag): update documentation after implementation batch
```

## Kebijakan 9+1 commit

Setiap 9 commit implementasi, commit ke-10 harus menjadi commit dokumentasi.

Contoh:

```text
commit 01: feat(rag): add chunk identity flag
commit 02: test(rag): cover identity flag for numeric chunks
commit 03: feat(rag): add graph seed gate
commit 04: test(rag): block graph for numeric queries
commit 05: feat(rag): add compressor negation guard
commit 06: test(rag): preserve negation in evidence pack
commit 07: feat(rag): add evidence sufficiency status
commit 08: test(rag): block answer when evidence is weak
commit 09: fix(rag): stabilize metadata propagation
commit 10: docs(rag): update guard status and regression notes
```
