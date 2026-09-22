"""
schema_loader.py

Utility module that automatically reads all SQLAlchemy models
and builds schema strings for Gemini prompt injection.

How it works:
  - Imports all models so they register themselves into Base.metadata
  - get_all_table_names()        → returns list of all table names
  - get_schema_for_tables()      → returns schema string for selected tables only
  - get_full_schema()            → returns schema string for ALL tables (for debugging)

To add a new table in future:
  1. Create the model in app/models/
  2. Add one import line in the _register_all_models() function below
  That's it — schema loader picks it up automatically.
"""

from app.models.base import Base


def _register_all_models():
    """
    Import all models here so SQLAlchemy registers them into Base.metadata.
    Add a new import line every time you create a new model.
    """
    import app.models.sales        # registers 'sales' table
    # import app.models.customers  # ← uncomment when you add customers model
    # import app.models.orders     # ← uncomment when you add orders model
    # import app.models.products   # ← uncomment when you add products model


def get_all_table_names() -> list[str]:
    """
    Returns a list of all registered table names.

    Example output:
        ["sales", "customers", "orders"]
    """
    _register_all_models()
    return list(Base.metadata.tables.keys())


def get_schema_for_tables(table_names: list[str]) -> str:
    """
    Builds a schema string for ONLY the specified tables.
    Used in Step 2 of nl_to_sql — inject only relevant table schemas.

    Args:
        table_names: list of table names returned by Gemini in Step 1
                     e.g. ["sales"]

    Returns:
        A formatted schema string like:
            Table: sales
            Columns:
              - id           : INTEGER  [PRIMARY KEY]
              - product_name : VARCHAR(255)
              - quantity     : INTEGER
              - price        : FLOAT
              - sale_date    : DATE
              - region       : VARCHAR(100)
    """
    _register_all_models()
    schema_parts = []

    for table_name in table_names:
        # Check if the table actually exists in metadata
        if table_name not in Base.metadata.tables:
            continue

        table = Base.metadata.tables[table_name]
        lines = [f"Table: {table_name}", "Columns:"]

        for col in table.columns:
            pk_flag = "  [PRIMARY KEY]" if col.primary_key else ""
            nullable = "" if col.nullable else "  [NOT NULL]"
            lines.append(f"  - {col.name} : {col.type}{pk_flag}{nullable}")

        schema_parts.append("\n".join(lines))

    return "\n\n".join(schema_parts) if schema_parts else "No matching tables found."


def get_full_schema() -> str:
    """
    Builds a schema string for ALL registered tables.
    Useful for debugging or when table count is small.
    """
    _register_all_models()
    all_tables = list(Base.metadata.tables.keys())
    return get_schema_for_tables(all_tables)
