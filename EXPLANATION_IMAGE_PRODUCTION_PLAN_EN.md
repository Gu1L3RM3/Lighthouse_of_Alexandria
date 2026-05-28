# English Explanation Image Production Plan

This plan turns the current audit into a concrete production sequence for the missing `_en` explanatory images.

## Goal

Create the English PNG sets for explanatory phases so that:

- the English UI uses English captions and English slides together
- no explanatory phase falls back to `_ptbr` images when language is `en`
- the validator passes with:

```powershell
python code/utils/validate_explanation_media.py --language en --require-english-assets
```

## Current Status

Missing localized English assets by phase:

- `exp_fase_3`: 9 unique PNGs
- `exp_fase_4`: 9 unique PNGs
- `exp_fase_5`: 8 unique PNGs
- `exp_fase_6`: 8 unique PNGs
- `exp_fase_7`: 9 unique PNGs

Total missing: `43` unique English PNGs.

## Production Order

Recommended order:

1. `exp_fase_3` pilot
2. `exp_fase_4`
3. `exp_fase_5`
4. `exp_fase_6`
5. `exp_fase_7`

Why start with `exp_fase_3`:

- it exercises two content folders: `ohm_law` and `electric_power`
- it establishes the translation/layout pattern for the rest
- it is early enough in the progression to catch style issues quickly

## Asset Rules

For every Portuguese source folder `*_ptbr`, create a matching English folder `*_en`.

Examples:

- `assets/images/explanations/ohm_law_ptbr` -> `assets/images/explanations/ohm_law_en`
- `assets/images/explanations/electric_power_ptbr` -> `assets/images/explanations/electric_power_en`
- `assets/images/explanations/resistor_assoc_ptbr` -> `assets/images/explanations/resistor_assoc_en`

Keep exactly:

- same filenames
- same image dimensions
- same visual ordering
- same diagram geometry
- same emphasis hierarchy

Change only:

- text language
- line breaks when needed to fit English copy

## Visual Acceptance Criteria

Each English image should satisfy:

- text is fully in English
- no Portuguese labels remain in the frame
- no text is cropped
- font size remains readable at in-game scale
- arrows, highlights, formulas, and diagram positions remain aligned
- formulas stay mathematically identical unless the label itself is language-specific

## Pilot Scope: exp_fase_3

Folders to create:

- `assets/images/explanations/ohm_law_en`
- `assets/images/explanations/electric_power_en`

Required files:

- `explanations/ohm_law_en/01_visao_geral.png`
- `explanations/ohm_law_en/02_equacoes_ohm.png`
- `explanations/ohm_law_en/03_circuito_basico.png`
- `explanations/ohm_law_en/06_serie_equivalente.png`
- `explanations/ohm_law_en/08_passos_paineis.png`
- `explanations/ohm_law_en/09_gnd_referencia.png`
- `explanations/electric_power_en/01_potencia_base.png`
- `explanations/electric_power_en/02_potencia_com_resistencia.png`
- `explanations/electric_power_en/03_exemplo_potencia_resistor.png`

Pilot checklist:

1. Copy each PT-BR image into the `_en` folder.
2. Replace all embedded Portuguese text with English.
3. Keep formulas like `V = R x I`, `P = V x I`, `P = I^2 x R`, `P = V^2 / R`.
4. Verify the in-game caption still matches the slide content.
5. Run the validator in required-English mode.
6. Open `exp_fase_3` in-game and verify image/caption sequencing.

## Remaining Phase Batches

### exp_fase_4

Create:

- `assets/images/explanations/resistor_assoc_en`

Files:

- `01_visao_geral.png`
- `02_serie_formula.png`
- `03_serie_exemplo.png`
- `04_paralelo_formula.png`
- `05_paralelo_exemplo.png`
- `06_misto_blocos.png`
- `07_divisor_tensao.png`
- `08_gnd_referencia.png`
- `09_passos_paineis.png`

### exp_fase_5

Create:

- `assets/images/explanations/nodal_kirchhoff_en`

Files:

- `01_visao_geral.png`
- `02_kcl_conceito.png`
- `03_kcl_equacao_no.png`
- `04_kvl_malha.png`
- `05_passos_metodo_nos.png`
- `06_exemplo_numerico.png`
- `07_gnd_referencia.png`
- `08_passos_paineis.png`

### exp_fase_6

Create:

- `assets/images/explanations/thevenin_norton_en`

Files:

- `01_visao_geral.png`
- `02_thevenin_conceito.png`
- `03_norton_conceito.png`
- `04_relacoes.png`
- `05_passos_vth_rth.png`
- `06_passos_inorton.png`
- `08_gnd_referencia.png`
- `09_passos_paineis.png`

### exp_fase_7

Create:

- `assets/images/explanations/max_power_transfer_en`

Files:

- `01_visao_geral.png`
- `02_equivalente_thevenin.png`
- `03_condicao_maxima.png`
- `04_forma_potencia.png`
- `05_passos_vth_rth.png`
- `06_exemplo_numerico.png`
- `07_eficiencia.png`
- `08_gnd_referencia.png`
- `09_passos_paineis.png`

## Validation Workflow

After each batch:

1. Regenerate checklist if needed:

```powershell
python code/utils/generate_explanation_asset_manifest.py
```

2. Validate explanatory media:

```powershell
python code/utils/validate_explanation_media.py --language en --require-english-assets
```

3. Run localization tests:

```powershell
python code/tests/test_scene_copy_localization.py
python code/tests/test_explanation_asset_audit.py
```

## Done Criteria

This work is complete when:

- all `_en` explanatory PNGs exist
- the English validator passes with no fallback
- explanatory scenes display English captions with English slides
- no Portuguese explanatory image appears while language is `en`
