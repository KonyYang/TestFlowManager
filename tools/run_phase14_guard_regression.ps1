param(
    [string]$Python = "python"
)

Write-Host "Running Phase-11/12 regression + Phase-14 guard suite..."

$baseTests = @(
    "tests/unit/test_matrix_session_registry.py",
    "tests/unit/test_matrix_session_factory.py",
    "tests/unit/test_matrix_session_manager.py",
    "tests/unit/test_matrix_session_orchestrator.py",
    "tests/unit/test_matrix_session_entry_facade.py",
    "tests/unit/test_matrix_session_debug_facade.py",
    "tests/unit/test_project_creator_flow.py",
    "tests/unit/test_main_window_controller_session_manager_injection.py",
    "tests/unit/test_main_window_ui_session_policy_assembly.py",
    "tests/unit/test_main_window_open_project_flow.py", 
    "tests/unit/test_project_session_flow.py",
    "tests/unit/test_project_creation_application_service.py",
    "tests/unit/test_project_open_side_effects_guard.py",
    "tests/unit/test_project_session_open_project_guard.py",
    "tests/unit/test_project_open_event_dispatch_guard.py",
    "tests/unit/test_project_open_title_guard.py",
    "tests/unit/test_project_session_state_guard.py",
    "tests/unit/test_matrix_service_provider_guard.py"
)

$integration = @(
    "tests/integration/test_matrix_session_transition_flow.py",
    "tests/integration/test_matrix_workspace_session_consistency_flow.py"
)

$command = "$Python -m pytest -q " + ($baseTests + $integration) -join " "
Write-Host "Executing: $command"
& $Python -m pytest -q $baseTests $integration

