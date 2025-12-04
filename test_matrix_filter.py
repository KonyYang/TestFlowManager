import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.features.matrix.view.matrix_filter_dialog import MatrixFilterDialog
from PyQt5.QtWidgets import QApplication, QDialog
import sys

def test_filter_dialog():
    """测试筛选对话框"""
    app = QApplication(sys.argv)
    
    # 创建筛选对话框
    dialog = MatrixFilterDialog()
    
    # 显示对话框并获取结果
    if dialog.exec_() == QDialog.Accepted:
        params = dialog.get_filter_params()
        print(f"筛选参数: 页码={params['page']}, 关键字='{params['keyword']}'")
    else:
        print("用户取消了操作")
    
    app.quit()

if __name__ == "__main__":
    test_filter_dialog()