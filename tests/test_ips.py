from switch_logo.core.ips import (
    IpsRecord,
    build_patch,
    create_records,
    rebase_patch,
    serialize_records,
)


def test_build_patch_creates_single_record():
    base = b"AAAA"
    target = b"ABAB"
    patch = build_patch(base, target)

    assert patch.startswith(b"PATCH")
    assert patch.endswith(b"EOF")
    assert b"\x00\x00\x01\x00\x02AB" in patch


def test_create_records_merges_nearby_changes():
    records = create_records(b"AAAAAAA", b"ABBBBAA")
    assert records == [IpsRecord(offset=1, data=b"BBBB")]


def test_rebase_patch_adds_firmware_offset():
    records = [IpsRecord(offset=10, data=b"XYZ")]
    rebased = rebase_patch(records, 1000)

    assert rebased[0].offset == 1010
    assert serialize_records(rebased).startswith(b"PATCH")
