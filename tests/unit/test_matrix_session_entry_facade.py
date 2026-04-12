from types import SimpleNamespace

from src.features.matrix.service.matrix_session_entry_facade import MatrixSessionEntryFacade


def test_matrix_session_entry_facade_returns_shared_when_pilot_disabled():
    facade = MatrixSessionEntryFacade(
        entry_policies=SimpleNamespace(get=lambda name: None)
    )

    config = facade.resolve_new_file_session_config(pilot_enabled=False)

    assert config.mode == "shared"
    assert config.session_id is None


def test_matrix_session_entry_facade_returns_policy_when_pilot_enabled():
    facade = MatrixSessionEntryFacade(
        entry_policies=SimpleNamespace(
            get=lambda name: SimpleNamespace(mode="isolated", fixed_session_id="pilot:new-file")
        )
    )

    config = facade.resolve_new_file_session_config(pilot_enabled=True)

    assert config.mode == "isolated"
    assert config.session_id == "pilot:new-file"


def test_matrix_session_entry_facade_pilot_gate_defaults_to_disabled():
    assert MatrixSessionEntryFacade.is_new_file_pilot_enabled({}) is False


def test_matrix_session_entry_facade_pilot_gate_accepts_truthy_values():
    env = {MatrixSessionEntryFacade.NEW_FILE_ISOLATED_PILOT_GATE: "On"}
    assert MatrixSessionEntryFacade.is_new_file_pilot_enabled(env) is True


def test_matrix_session_entry_facade_preview_pilot_gate_defaults_to_disabled():
    assert MatrixSessionEntryFacade.is_preview_pilot_enabled({}) is False


def test_matrix_session_entry_facade_preview_pilot_gate_accepts_truthy_values():
    env = {MatrixSessionEntryFacade.PREVIEW_ISOLATED_PILOT_GATE: "yes"}
    assert MatrixSessionEntryFacade.is_preview_pilot_enabled(env) is True


def test_matrix_session_entry_facade_returns_none_preview_session_id_when_pilot_disabled():
    facade = MatrixSessionEntryFacade(entry_policies=SimpleNamespace(get=lambda name: None))
    assert facade.resolve_preview_pilot_session_id(pilot_enabled=False) is None


def test_matrix_session_entry_facade_returns_fixed_preview_session_id_when_pilot_enabled():
    facade = MatrixSessionEntryFacade(entry_policies=SimpleNamespace(get=lambda name: None))
    assert (
        facade.resolve_preview_pilot_session_id(pilot_enabled=True)
        == MatrixSessionEntryFacade.PREVIEW_PILOT_SESSION_ID
    )
