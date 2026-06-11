"""In-memory capability registry with composition checks."""
from fastapi import HTTPException
from .models import CapabilityRecord, PublishRequest


class CapabilityStore:
    def __init__(self):
        self._capabilities: dict[str, CapabilityRecord] = {}

    def reset(self):
        self._capabilities.clear()

    def publish(self, req: PublishRequest) -> CapabilityRecord:
        manifest = req.manifest
        cap = manifest.get("capability", {})
        cap_id = cap.get("id")
        if not cap_id:
            raise HTTPException(422, "capability.id is required")

        lifecycle = cap.get("lifecycle", "")
        if lifecycle not in ("draft", "beta", "ga", "deprecated"):
            raise HTTPException(422, f"Invalid lifecycle: {lifecycle!r}")

        fulfillment_modes = manifest.get("runtime", {}).get("fulfillment_modes", [])
        if not fulfillment_modes:
            raise HTTPException(422, "At least one fulfillment_mode required")

        self._check_entity_ownership(cap_id, manifest)

        record = CapabilityRecord(
            id=cap_id,
            name=cap.get("name", ""),
            version=cap.get("version", "0.0.1"),
            lifecycle=lifecycle,
            manifest=manifest,
            owner_team=cap.get("owner", ""),
        )
        self._capabilities[cap_id] = record
        return record

    def get(self, cap_id: str) -> CapabilityRecord:
        record = self._capabilities.get(cap_id)
        if not record:
            raise HTTPException(404, f"Capability not found: {cap_id!r}")
        return record

    def list_all(self, lifecycle: str | None = None) -> list[CapabilityRecord]:
        caps = list(self._capabilities.values())
        if lifecycle:
            caps = [c for c in caps if c.lifecycle == lifecycle]
        return caps

    def delete(self, cap_id: str) -> None:
        if cap_id not in self._capabilities:
            raise HTTPException(404, f"Capability not found: {cap_id!r}")
        del self._capabilities[cap_id]

    def get_manifest_scopes(self, cap_id: str) -> list[str]:
        record = self.get(cap_id)
        return record.manifest.get("auth", {}).get("scopes", [])

    def _check_entity_ownership(self, new_cap_id: str, new_manifest: dict) -> None:
        new_owned = {
            e["type"]
            for e in new_manifest.get("entities", [])
            if e.get("owns", False)
        }
        for cap_id, record in self._capabilities.items():
            if cap_id == new_cap_id:
                continue
            existing_owned = {
                e["type"]
                for e in record.manifest.get("entities", [])
                if e.get("owns", False)
            }
            duplicates = new_owned & existing_owned
            if duplicates:
                raise HTTPException(
                    409,
                    f"Entity types already owned by {cap_id!r}: {sorted(duplicates)}",
                )
