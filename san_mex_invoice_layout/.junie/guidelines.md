# Project Guidelines: Odoo 15 Module

## 1. Project Structure
This project is an Odoo 15 addon. The standard structure should be followed:

```
san_mex_invoice_layout/
├── __init__.py
├── __manifest__.py        # Module metadata
├── models/                # Python models
│   ├── __init__.py
│   └── model_name.py
├── views/                 # XML views, actions, menus
│   └── model_name_views.xml
├── security/              # Access rights and rules
│   └── ir.model.access.csv
├── data/                  # Data files (demo or system data)
├── static/                # Static assets (JS, CSS, images)
│   ├── src/
│   └── description/
└── tests/                 # Python tests
    ├── __init__.py
    └── test_module.py
```

## 2. Odoo 15 Specifics
-   **Manifest**: Ensure `__manifest__.py` includes `depends`, `data` (in order of dependency), and `license`.
-   **XML IDs**: Use consistent naming `<model_name>_<view_type>_<suffix>`.
-   **Assets**: In Odoo 15, assets are declared in `__manifest__.py` under the `assets` key (e.g., `web.assets_backend`).
-   **Security**: Always include `ir.model.access.csv` for new models.

## 3. Code Style
-   **Python**: Follow PEP8.
    -   Classes: `PascalCase`
    -   Variables/Functions: `snake_case`
    -   Odoo Models: `_name` should use dots (e.g., `sale.order`).
-   **XML**: Indent with 4 spaces.
-   **Commits**: Write clear commit messages referencing the task or module changed.

## 4. Testing
-   Run tests using the Odoo test runner or `start-odoo` with `--test-enable`.
-   Example command: `./odoo-bin -c odoo.conf -d <db_name> -i san_mex_oper_logistic --test-enable`

## 5. Deployment
-   Ensure dependencies are listed in `__manifest__.py`.
-   Update module version in `__manifest__.py` before release.
