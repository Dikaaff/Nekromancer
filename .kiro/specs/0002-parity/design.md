# Spec 0002 — Design

## Komponen

```
packages/parity/
  grammar/
    csv.yaml         ← aksi: sort_column, filter_value, navigate_page, search
    dbf.yaml         ← aksi: open_record, navigate_record, filter_field
  generator.py       ← generate N urutan acak dari grammar + seed
  runner.py          ← eksekusi urutan pada dua sisi, rekam trace
  normalizer.py      ← terapkan kebijakan normalisasi
  comparator.py      ← bandingkan dua trace yang sudah dinormalisasi
  shrinker.py        ← susutkan urutan ke minimum
  reporter.py        ← hasilkan parity-report.json
evidence/
  {artifact_id}/
    parity-report.json
    counterexamples/
      {n}.json
```

## Properti PBT (Hypothesis)

```python
# P1: jumlah urutan
@given(st.lists(action_strategy, min_size=1000))
def test_sequences_run(sequences):
    assert len(sequences) >= 1000

# P2: sitasi UI
@given(element_strategy)
def test_all_ui_elements_cited(element):
    assert element.cite is not None

# P3: escape injection
@given(st.text())
def test_no_unescaped_artifact_text(text):
    dossier = make_dossier_with(text)
    assert no_unescaped_delimiters(dossier)
```

## Keputusan Desain

| Keputusan | Pilihan | Alasan |
|---|---|---|
| PBT framework | Hypothesis (Python) | Terintegrasi, bisa jalan di CI |
| Penyusutan | Built-in Hypothesis shrinker | Sudah battle-tested |
| Trace format | JSON per aksi | Mudah di-diff dan diaudit |
| Normalisasi | Whitespace + presentasi | Sesuai kebijakan doctrine |
