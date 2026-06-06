# The scripts behind the PrevHist dataset

Processing scripts for **PrevHist**, a dataset of Old and Middle Hungarian preverb–verb constructions, covering the period from the late twelfth century to 1772.

- **Dataset:** https://doi.org/10.5281/zenodo.19927110
- **Paper:** Kalivoda, Ágnes (2026). PrevHist: A dataset of Old and Middle Hungarian preverb constructions. *to appear*

---

## ⚠️ Please read first: these scripts cannot be run as-is

These scripts are published for **transparency and documentation**, not as a turnkey pipeline. They operate directly on the two source corpora, and **those corpora are not part of this repository and cannot be redistributed here** — in the case of the Middle Hungarian Corpus in particular, the source files are not mine to release.

As a result, **you will not be able to execute the pipeline end-to-end without independent access to the source corpora.** What you *can* do is read the code to see exactly what each harmonization, search, and filtering step does — which is the point of making it available.

The source corpora are:

- **OHC** — the Old Hungarian Corpus (TSV files). See Simon (2014).
- **MHC** — the Old and Middle Hungarian Corpus of informal language (a MySQL database). See Novák, Gugán, Varga, & Dömötör (2018).

---

## The pipeline

The scripts were run in the following order. Each maps onto one or more of the five processing steps described in the paper.

### 1. `omk_tmk_unify.py` — *harmonization (step 1)*

Reads the two source corpora — the OHC and the MHC — and converts them into a single, unified TSV format with four columns: **original form, normalized form, lemma, and morphological analysis**.

- For the OHC, only the morphologically annotated files are kept; rows flagged as errors, fragments, or foreign-language material are dropped, as are Latin passages in the MHC.
- The text is **re-tokenized** so that punctuation marks and the clitic question particle *-e* become separate tokens, after which token IDs are reassigned.
- A unified **metadata** table is produced alongside the corpus (the register of the OHC texts is filled in manually).

*(The `omk` / `tmk` in the file names stand for* ómagyar korpusz */* középmagyar korpusz*, i.e. the Old / Middle Hungarian corpus.)*

### 2. `vpfx_finder.py` — *identifying preverb candidates (step 2)*

Scans the unified corpus for preverbs and labels each occurrence as `detached`, `prefixed`, or `prefixed_unmarked`.

- Preverbs hidden **inside derivations** are not marked as preverbs in the source annotation, so they are located using the derivational-boundary marker (`|+`) together with a hand-curated list of preverbs and their variants (`vpfx_helpdict.txt`).
- Each candidate is assigned a **construction type** by mapping its morphological analysis (which follows the emMorph annotation scheme; Novák, Siklósi, & Oravecz, 2016) — or, as a fallback, its word ending — onto the construction-type inventory used by [PrevDistro](https://zenodo.org/records/6349410).

### 3. `omk_get_hits.py` — *extracting clauses and metadata (steps 2 & 4)*

Pulls out every clause that contains a flagged preverb and attaches the relevant document-level metadata (document ID, year, register, etc.) to each hit.

### 4. `omk_make_dataset.py` — *building the final dataset (steps 3–5)*

For **detached** preverbs, finds the associated verb by scanning the clause outward from the preverb:

- a verb in the **right context** yields a *discontinuous* order (e.g. *meg nem látta*),
- a verb in the **left context** yields an *inverted* order (e.g. *nem ment el*).

Candidates are validated with a cascade of regular expressions over the intervening material, and complex past tenses and copular constructions (which are absent from Present-day Hungarian) are handled explicitly so that the preverb is linked to the full verbal complex.

The script writes the final **PrevHist** dataset as a TSV file with one row per construction, including the verb lemma, construction type and subtype, preverb position, intervening words, the keyword-in-context concordance in both original and normalized form, and document-level metadata.

---

## Repository contents

| File | Purpose |
|------|---------|
| `omk_tmk_unify.py` | Step 1 — harmonize OHC + MHC into a unified TSV |
| `vpfx_finder.py` | Step 2 — find and classify preverb candidates |
| `omk_get_hits.py` | Steps 2 & 4 — extract clauses + metadata |
| `omk_make_dataset.py` | Steps 3–5 — link verbs, validate, build the dataset |
| `vpfx_helpdict.txt` | Hand-curated preverb list / dictionary of tricky cases, used by `vpfx_finder.py` |
