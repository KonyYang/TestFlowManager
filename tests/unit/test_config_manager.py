import json
from pathlib import Path

from src.core.config_manager import ConfigManager


def test_config_manager_reads_main_and_paths_config(tmp_path):
    config_root = tmp_path / "src" / "app" / "config"
    config_root.mkdir(parents=True)

    settings_file = config_root / "settings.json"
    settings_file.write_text(
        json.dumps(
            {
                "logging": {"level": "WARNING", "file": "logs/custom.log"},
                "window": {"width": 1280},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    paths_file = config_root / "paths.ini"
    paths_file.write_text(
        "\n".join(
            [
                "[Paths]",
                "ltr_file = D:\\Data\\ltr.xlsx",
                "template_dir = D:\\Ignored\\Template",
                "",
                "[Defaults]",
                "project_leader = Alice",
                "",
                "[Passwords]",
                "ltr_password = secret",
                "",
                "[STANDARD_FILES]",
                "sample = template.docx",
                "",
                "[EquipmentDataSources]",
                "excel_file_path = D:\\Equipment\\equipment.xlsx",
            ]
        ),
        encoding="utf-8",
    )

    manager = ConfigManager()
    manager._get_resource_path = lambda relative_path: str(config_root / Path(relative_path).name)
    manager.load_main_config()
    manager.load_paths_config()

    assert manager.get_logging("level") == "WARNING"
    assert manager.get_logging("file") == "logs/custom.log"
    assert manager.get_path("ltr_file") == r"D:\Data\ltr.xlsx"
    assert manager.get_default("project_leader") == "Alice"
    assert manager.get_password("ltr_password") == "secret"
    assert manager.get_standard_file("sample") == "template.docx"
    assert manager.get_equipment_data_source("excel_file_path") == r"D:\Equipment\equipment.xlsx"


def test_config_manager_get_resource_path_uses_dev_src_app_config(monkeypatch, tmp_path):
    project_root = tmp_path / "repo"
    app_dir = project_root / "src" / "app"
    app_dir.mkdir(parents=True)

    monkeypatch.chdir(app_dir)
    manager = ConfigManager()

    result = manager._get_resource_path("config/settings.json")

    assert Path(result) == project_root / "src" / "app" / "config" / "settings.json"
