"""
A2UI catalog renderer — INV-2: no arbitrary code, catalog components only.

render_from_json(component_id, props_dict) → validated props
  Raises ValueError on unknown component_id.
  Raises pydantic.ValidationError on invalid props.
"""
from .models import (
    ActionCardProps,
    ConfirmationCardProps,
    EntityCardProps,
    EntityPickerProps,
    DataTableProps,
    StatusBadgeProps,
    SectionHeaderProps,
    CompositeLayoutProps,
    ReceiptViewProps,
)

CATALOG: dict[str, type] = {
    "ActionCard": ActionCardProps,
    "ConfirmationCard": ConfirmationCardProps,
    "EntityCard": EntityCardProps,
    "EntityPicker": EntityPickerProps,
    "DataTable": DataTableProps,
    "StatusBadge": StatusBadgeProps,
    "SectionHeader": SectionHeaderProps,
    "CompositeLayout": CompositeLayoutProps,
    "ReceiptView": ReceiptViewProps,
}


def render_from_json(component_id: str, props: dict) -> object:
    """
    Validate and return typed props for the given component.
    INV-2: raises ValueError if component_id is not in catalog.
    """
    if component_id not in CATALOG:
        raise ValueError(
            f"Unknown component ID: {component_id!r}. "
            f"Valid components: {sorted(CATALOG.keys())}"
        )
    schema_cls = CATALOG[component_id]
    return schema_cls.model_validate(props)
