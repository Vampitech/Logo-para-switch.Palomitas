"""Generador mínimo de parches IPS."""

from __future__ import annotations

from dataclasses import dataclass

IPS_MAGIC = b"PATCH"
IPS_EOF = b"EOF"
MAX_RECORD_SIZE = 0xFFFF
MERGE_GAP = 8


@dataclass(frozen=True)
class IpsRecord:
    offset: int
    data: bytes


def _encode_offset(offset: int) -> bytes:
    if not 0 <= offset <= 0xFFFFFF:
        raise ValueError(f"Offset IPS fuera de rango: {offset}")
    return offset.to_bytes(3, "big")


def create_records(base: bytes, target: bytes) -> list[IpsRecord]:
    if len(base) != len(target):
        raise ValueError("Las imágenes deben tener exactamente el mismo tamaño.")

    differences = [index for index, (a, b) in enumerate(zip(base, target)) if a != b]
    if not differences:
        return []

    groups: list[list[int]] = [[differences[0]]]
    for position in differences[1:]:
        if position - groups[-1][-1] <= MERGE_GAP:
            groups[-1].append(position)
        else:
            groups.append([position])

    records: list[IpsRecord] = []
    for group in groups:
        start = group[0]
        end = group[-1] + 1
        for chunk_start in range(start, end, MAX_RECORD_SIZE):
            chunk_end = min(chunk_start + MAX_RECORD_SIZE, end)
            records.append(
                IpsRecord(
                    offset=chunk_start,
                    data=target[chunk_start:chunk_end],
                )
            )
    return records


def build_patch(base: bytes, target: bytes) -> bytes:
    output = bytearray(IPS_MAGIC)
    for record in create_records(base, target):
        output.extend(_encode_offset(record.offset))
        output.extend(len(record.data).to_bytes(2, "big"))
        output.extend(record.data)
    output.extend(IPS_EOF)
    return bytes(output)


def rebase_patch(records: list[IpsRecord], base_offset: int) -> list[IpsRecord]:
    rebased: list[IpsRecord] = []
    for record in records:
        new_offset = record.offset + base_offset
        if new_offset > 0xFFFFFF:
            raise ValueError(
                f"El offset final {new_offset} excede el límite IPS de 16777215."
            )
        rebased.append(IpsRecord(offset=new_offset, data=record.data))
    return rebased


def serialize_records(records: list[IpsRecord]) -> bytes:
    output = bytearray(IPS_MAGIC)
    for record in records:
        output.extend(_encode_offset(record.offset))
        output.extend(len(record.data).to_bytes(2, "big"))
        output.extend(record.data)
    output.extend(IPS_EOF)
    return bytes(output)
