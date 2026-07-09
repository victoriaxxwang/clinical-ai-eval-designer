# Ablation results — pilot-3 golden slate

_Generated 2026-07-09T22:31:21Z. Recall/precision vs the hand-verified goldens; deterministic categories are EXACT identifier matches, literature is overlap + resolvable-ID floor (Lesson 2). Precision on deterministic categories is a lower bound (adjacent-correct records deflate it)._


## HRV

| config | axis | pmids R/P (hits/n) | dois R/P (hits/n) | fda_product_codes R/P (hits/n) | fda_k_numbers R/P (hits/n) | fda_den_numbers R/P (hits/n) |
|---|---|---|---|---|---|---|
| baseline | — (shipped defaults) |    0%/   0% (0/11) |    0%/   0% (0/14) |   29%/  12% (2/16) |    0%/   0% (0/1) |    0%/  —   (0/0) |
| mesh_canonical | MeSH: canonical only (drop synonyms) |    0%/   0% (0/8) |    0%/   0% (0/15) |   29%/  12% (2/16) |    0%/   0% (0/1) |    0%/  —   (0/0) |
| mesh_hierarchy | MeSH: + hierarchy (add child descriptors) |    0%/   0% (0/11) |    0%/   0% (0/14) |   29%/  12% (2/16) |    0%/   0% (0/1) |    0%/  —   (0/0) |
| lit_epmc_only | Providers: Europe PMC only |    0%/   0% (0/14) |    0%/   0% (0/14) |   29%/  12% (2/16) |    0%/   0% (0/1) |    0%/  —   (0/0) |
| lit_epmc_openalex | Providers: Europe PMC + OpenAlex |    0%/   0% (0/11) |    0%/   0% (0/14) |   29%/  12% (2/16) |    0%/   0% (0/1) |    0%/  —   (0/0) |
| verify_off | Crossref verify: OFF |    0%/   0% (0/11) |    0%/   0% (0/14) |   29%/  12% (2/16) |    0%/   0% (0/1) |    0%/  —   (0/0) |

## DR

| config | axis | pmids R/P (hits/n) | dois R/P (hits/n) | fda_product_codes R/P (hits/n) | fda_den_numbers R/P (hits/n) | fda_k_numbers R/P (hits/n) | ncts R/P (hits/n) |
|---|---|---|---|---|---|---|---|
| baseline | — (shipped defaults) |   20%/   8% (1/13) |   20%/   7% (1/15) |  100%/   8% (1/13) |    0%/  —   (0/0) |    0%/   0% (0/4) |    0%/   0% (0/4) |
| mesh_canonical | MeSH: canonical only (drop synonyms) |   20%/   8% (1/13) |   20%/   7% (1/15) |  100%/   8% (1/13) |    0%/  —   (0/0) |    0%/   0% (0/4) |    0%/   0% (0/4) |
| mesh_hierarchy | MeSH: + hierarchy (add child descriptors) |   20%/   8% (1/13) |   20%/   7% (1/15) |  100%/   8% (1/13) |    0%/  —   (0/0) |    0%/   0% (0/4) |    0%/   0% (0/4) |
| lit_epmc_only | Providers: Europe PMC only |    0%/   0% (0/15) |    0%/   0% (0/15) |  100%/   8% (1/13) |    0%/  —   (0/0) |    0%/   0% (0/4) |    0%/   0% (0/4) |
| lit_epmc_openalex | Providers: Europe PMC + OpenAlex |   20%/   8% (1/13) |   20%/   7% (1/15) |  100%/   8% (1/13) |    0%/  —   (0/0) |    0%/   0% (0/4) |    0%/   0% (0/4) |
| verify_off | Crossref verify: OFF |   20%/   8% (1/13) |   20%/   7% (1/15) |  100%/   8% (1/13) |    0%/  —   (0/0) |    0%/   0% (0/4) |    0%/   0% (0/4) |

## warfarin

| config | axis | pmids R/P (hits/n) | dois R/P (hits/n) | ncts R/P (hits/n) | fda_product_codes R/P (hits/n) | fda_k_numbers R/P (hits/n) | fda_nda_numbers R/P (hits/n) |
|---|---|---|---|---|---|---|---|
| baseline | — (shipped defaults) |   14%/   7% (1/15) |   14%/   7% (1/15) |    0%/   0% (0/6) |    0%/   0% (0/1) |   43%/  60% (3/5) |    0%/   0% (0/2) |
| mesh_canonical | MeSH: canonical only (drop synonyms) |   14%/   7% (1/15) |   14%/   7% (1/15) |    0%/   0% (0/6) |    0%/   0% (0/1) |   43%/  60% (3/5) |    0%/   0% (0/2) |
| mesh_hierarchy | MeSH: + hierarchy (add child descriptors) |   14%/   7% (1/15) |   14%/   7% (1/15) |    0%/   0% (0/6) |    0%/   0% (0/1) |   43%/  60% (3/5) |    0%/   0% (0/2) |
| lit_epmc_only | Providers: Europe PMC only |    0%/   0% (0/15) |    0%/   0% (0/15) |    0%/   0% (0/6) |    0%/   0% (0/1) |   43%/  60% (3/5) |    0%/   0% (0/2) |
| lit_epmc_openalex | Providers: Europe PMC + OpenAlex |   14%/   7% (1/15) |   14%/   7% (1/15) |    0%/   0% (0/6) |    0%/   0% (0/1) |   43%/  60% (3/5) |    0%/   0% (0/2) |
| verify_off | Crossref verify: OFF |   14%/   7% (1/15) |   14%/   7% (1/15) |    0%/   0% (0/6) |    0%/   0% (0/1) |   43%/  60% (3/5) |    0%/   0% (0/2) |
