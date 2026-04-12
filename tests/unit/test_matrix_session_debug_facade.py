from types import SimpleNamespace

from src.features.matrix.service.matrix_session_debug_facade import MatrixSessionDebugFacade


def test_matrix_session_debug_facade_open_preview_uses_preview_policy():
    calls = []
    facade = MatrixSessionDebugFacade(
        orchestrator=SimpleNamespace(
            open_session=lambda session_id, **kwargs: (
                calls.append((session_id, kwargs.get("mode"), kwargs.get("entry_name")))
                or "session"
            )
        ),
        entry_policies=SimpleNamespace(
            get=lambda name: SimpleNamespace(mode="isolated", session_id_prefix=None)
        ),
    )

    result = facade.open_preview_session("preview:a", entry_name="preview")

    assert result == "session"
    assert calls == [("preview:a", "isolated", "preview")]


def test_matrix_session_debug_facade_open_debug_preview_uses_debug_policy():
    calls = []
    facade = MatrixSessionDebugFacade(
        orchestrator=SimpleNamespace(
            open_debug_preview=lambda **kwargs: (
                calls.append(
                    (
                        kwargs.get("session_id"),
                        kwargs.get("mode"),
                        kwargs.get("session_id_prefix"),
                        kwargs.get("entry_name"),
                    )
                )
                or ("debug:preview:1", "session")
            )
        ),
        entry_policies=SimpleNamespace(
            get=lambda name: SimpleNamespace(mode="isolated", session_id_prefix="debug:preview:")
        ),
    )

    result = facade.open_debug_preview_session()

    assert result == ("debug:preview:1", "session")
    assert calls == [(None, "isolated", "debug:preview:", "debug_preview")]


def test_matrix_session_debug_facade_switch_preview_session_uses_contract_args():
    calls = []
    facade = MatrixSessionDebugFacade(
        orchestrator=SimpleNamespace(
            switch_to_session=lambda session_id, **kwargs: (
                calls.append(
                    (
                        session_id,
                        kwargs.get("expected_entry_names"),
                        kwargs.get("requested_by"),
                    )
                )
                or "switch-result"
            )
        ),
        entry_policies=SimpleNamespace(
            get=lambda name: SimpleNamespace(mode="isolated", session_id_prefix="debug:preview:")
        ),
    )

    result = facade.switch_preview_session("preview:a")

    assert result == "switch-result"
    assert calls == [
        (
            "preview:a",
            ("preview", "debug_preview"),
            "main_window.debug_preview_switch",
        )
    ]
