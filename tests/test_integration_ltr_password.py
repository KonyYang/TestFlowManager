"""
LTR密码功能集成测试脚本
用于手动测试LTR文件密码功能
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.features.ltr_manager.service.ltr_viewer_service import LTRViewerService
from src.features.ltr_manager.model.ltr_viewer_data import LTRViewerData
from src.core.config_manager import config_manager
from src.utils.excel_utils import open_excel_file


def test_ltr_password_functionality():
    """测试LTR密码功能"""
    print("LTR文件密码功能测试")
    print("=" * 30)

    # 加载配置（包括路径和密码配置）
    config_manager.load_paths_config()

    # 创建LTR服务实例
    ltr_data = LTRViewerData()
    ltr_service = LTRViewerService(ltr_data)

    # 获取当前配置的文件路径
    file_path = ltr_service.get_ltr_file_path()
    print(f"LTR文件路径: {file_path}")

    # 获取配置的密码
    password = config_manager.get("paths.LTRPassword", "DGLAB")
    print(f"配置的密码: {repr(password)}")

    print("\n尝试使用密码打开LTR文件...")

    try:
        # 直接调用open_excel_file函数进行测试
        print("直接调用open_excel_file函数测试:")
        print(f"  文件路径: {file_path}")
        print(f"  密码: {repr('DGLAB')}")
        print(f"  只读模式: False")

        # 直接使用open_excel_file函数测试
        workbook = open_excel_file(file_path, read_only=False, password="DGLAB")



        if workbook:
            print("✅ 成功使用密码打开LTR文件")
            # 关闭工作簿
            try:
                workbook.Close(SaveChanges=False)
                print("  工作簿已关闭")
            except:
                pass
        else:
            print("❌ 使用密码打开LTR文件失败")

    except Exception as e:
        print(f"❌ 打开文件时发生异常: {e}")

    # 测试LTR服务函数
    print("\n测试LTR服务函数:")
    try:
        # 尝试使用密码打开文件
        success = ltr_service.open_ltr_file_with_password()

        if success:
            print("✅ LTR服务成功使用密码打开LTR文件")
        else:
            print("❌ LTR服务使用密码打开LTR文件失败")

    except Exception as e:
        print(f"❌ LTR服务打开文件时发生异常: {e}")


if __name__ == "__main__":
    test_ltr_password_functionality()
