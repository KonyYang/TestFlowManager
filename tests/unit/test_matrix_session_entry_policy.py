from src.features.matrix.service.matrix_session_entry_policy import (
    MatrixSessionEntryPolicyTable,
)


def test_matrix_session_entry_policy_table_defaults():
    table = MatrixSessionEntryPolicyTable()

    new_file = table.get(MatrixSessionEntryPolicyTable.NEW_FILE_PILOT)
    preview = table.get(MatrixSessionEntryPolicyTable.PREVIEW)
    debug_preview = table.get(MatrixSessionEntryPolicyTable.DEBUG_PREVIEW)

    assert new_file.mode == "isolated"
    assert new_file.fixed_session_id == "pilot:new-file"
    assert preview.mode == "isolated"
    assert debug_preview.mode == "isolated"
    assert debug_preview.session_id_prefix == "debug:preview:"


def test_matrix_session_entry_policy_table_rejects_unknown_entry():
    table = MatrixSessionEntryPolicyTable()

    try:
        table.get("unknown-entry")
    except KeyError as exc:
        assert "Unknown matrix session entry policy" in str(exc)
    else:
        raise AssertionError("Expected KeyError for unknown policy entry")

