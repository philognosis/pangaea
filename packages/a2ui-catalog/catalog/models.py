"""
A2UI component prop schemas — Pydantic models that define the JSON contract
for each catalog component. These are the Zod schemas of the Python PoC.

INV-2: No code in A2UI surfaces. Component ID + validated props only.
"""
from pydantic import BaseModel, Field
from typing import Any, Optional


class ActionButton(BaseModel):
    label: str
    intent: str
    style: str = "secondary"


class ActionCardProps(BaseModel):
    title: str
    body: str
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    capability_id: str
    actions: list[ActionButton] = Field(default_factory=list)


class ConfirmationCardProps(BaseModel):
    """INV-4: props built from resolved entity data, never model-generated."""
    title: str
    summary: str
    fields: dict[str, Any]
    capability_id: str
    action_id: str
    card_hash: Optional[str] = None
    voice_blocked: bool = True


class EntityCardProps(BaseModel):
    entity_id: str
    entity_type: str
    display_name: str
    fields: dict[str, Any]
    capability_id: str


class EntityPickerProps(BaseModel):
    """Disambiguation card — shown when entity resolution returns multiple results."""
    query: str
    entity_type: str
    candidates: list[dict[str, Any]]
    show_fields: list[str]
    capability_id: str


class ColumnDef(BaseModel):
    key: str
    label: str
    sortable: bool = False


class DataTableProps(BaseModel):
    columns: list[ColumnDef]
    rows: list[dict[str, Any]]
    total: int
    page: int = 1
    page_size: int = 20


class StatusBadgeProps(BaseModel):
    status: str
    label: str
    variant: str = "default"  # default | success | warning | error | info


class SectionHeaderProps(BaseModel):
    title: str
    capability_id: str
    section_label: Optional[str] = None


class CompositeSection(BaseModel):
    section_id: str
    capability_id: str
    label: str
    component_id: str
    props: dict[str, Any]


class CompositeLayoutProps(BaseModel):
    """Multi-section collated view — the mentee view pattern."""
    entity_id: str
    entity_type: str
    sections: list[CompositeSection]


class ReceiptViewProps(BaseModel):
    """INV-5: provenance receipt display."""
    receipt_id: str
    intent_text: str
    capability_id: str
    action_id: str
    committed_at: str
    chain_hash: str
    valid: bool
