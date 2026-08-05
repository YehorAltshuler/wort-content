# wort_ Content Dataset

Validated, machine-readable learning content for the `wort_` application.

The repository publishes coursebooks, Leben in Deutschland vocabulary and
exercises as static JSON endpoints through GitHub Pages. The Flutter app can
check the manifest and update content without an application release.

## Published endpoints

After publishing the repository as `YehorAltshuler/wort-content`:

| Resource | URL |
| --- | --- |
| Manifest | `https://yehoraltshuler.github.io/wort-content/manifest.json` |
| Catalog | `https://yehoraltshuler.github.io/wort-content/catalog.json` |
| Coursebook | `https://yehoraltshuler.github.io/wort-content/coursebooks/<id>/book.json` |
| Exercise | `https://yehoraltshuler.github.io/wort-content/exercises/<id>/exercise.json` |

Clients start with `manifest.json`, verify the catalog SHA-256, and then use the
URLs and hashes in the catalog. Coursebook descriptors contain individually
hashed module URLs; exercise descriptors contain a hashed words URL.

## Guarantees

Publication fails unless all of the following are true:

- source, module and word IDs are present and unique;
- every descriptor references an existing non-empty JSON file;
- every word card has a supported type, term and translations;
- every published descriptor and data file matches its SHA-256;
- the complete published tree can be rebuilt from checked-in source data.

The build is staged and replaces `data/published` atomically. GitHub Pages is
deployed only after tests, source validation, build and published validation
all pass.

## Structure

```text
.
├── .github/workflows/
│   ├── pages.yml
│   └── validate.yml
├── data/
│   ├── source/
│   │   ├── coursebooks/
│   │   └── exercises/
│   └── published/       # generated
├── scripts/assign_ids.py
├── src/wort_content/
├── tests/
└── pyproject.toml
```

`leben-in-deutschland` is represented as a coursebook-shaped vocabulary source,
so it uses the same module, progress and training flow as the other word sets.

## Local development

Requirements: Python 3.11 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
wort-content build
wort-content validate
```

Edit only `data/source`. Do not edit `data/published` by hand. Explicit IDs are
part of the public contract and must not be changed after publication. The
one-time `scripts/assign_ids.py` utility is idempotent and only fills missing IDs.

## Publishing

1. Create the GitHub repository and push the `main` branch.
2. In repository settings, set Pages source to **GitHub Actions**.
3. Run **Build and deploy content to GitHub Pages**, or push a source change.
4. Configure the app to use the manifest endpoint shown above.

