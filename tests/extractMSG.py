import os
import shutil
import win32com.client
from pathlib import Path


def extract_attachments_from_msg(msg_file_path, output_folder):
    """
    从Outlook .msg文件中提取所有附件到指定文件夹

    Args:
        msg_file_path (str): .msg文件的完整路径
        output_folder (str): 附件保存的目标文件夹

    Returns:
        tuple: (success_count, total_count, error_messages)
    """
    # 检查文件是否存在
    if not os.path.exists(msg_file_path):
        return 0, 0, [f"错误：文件 '{msg_file_path}' 不存在"]

    # 创建输出文件夹（如果不存在）
    os.makedirs(output_folder, exist_ok=True)

    success_count = 0
    error_messages = []

    try:
        # 创建Outlook应用程序对象
        outlook = win32com.client.Dispatch("Outlook.Application")

        # 获取MAPI命名空间
        namespace = outlook.GetNamespace("MAPI")

        # 打开.msg文件
        msg = outlook.CreateItemFromTemplate(msg_file_path)

        # 获取附件集合
        attachments = msg.Attachments
        total_count = attachments.Count

        print(f"找到 {total_count} 个附件")

        # 遍历所有附件
        for i in range(1, total_count + 1):
            try:
                attachment = attachments.Item(i)
                attachment_name = attachment.FileName

                # 构建完整的保存路径
                save_path = os.path.join(output_folder, attachment_name)

                # 处理文件名冲突
                counter = 1
                base_name, extension = os.path.splitext(attachment_name)
                while os.path.exists(save_path):
                    new_name = f"{base_name}_{counter}{extension}"
                    save_path = os.path.join(output_folder, new_name)
                    counter += 1

                # 保存附件
                attachment.SaveAsFile(save_path)
                print(f"成功提取: {os.path.basename(save_path)}")
                success_count += 1

            except Exception as e:
                error_msg = f"提取附件 {i} 时出错: {str(e)}"
                error_messages.append(error_msg)
                print(error_msg)

        # 清理COM对象
        msg = None
        namespace = None
        outlook = None

    except Exception as e:
        error_messages.append(f"处理文件时出错: {str(e)}")
        return success_count, 0, error_messages

    return success_count, total_count, error_messages


def batch_extract_msg_attachments(folder_path, output_base_folder):
    """
    批量提取文件夹中所有.msg文件的附件

    Args:
        folder_path (str): 包含.msg文件的文件夹路径
        output_base_folder (str): 附件保存的基础文件夹

    Returns:
        dict: 处理结果的统计信息
    """
    if not os.path.exists(folder_path):
        return {"error": f"文件夹 '{folder_path}' 不存在"}

    msg_files = list(Path(folder_path).glob("*.msg"))

    if not msg_files:
        return {"error": f"在 '{folder_path}' 中未找到.msg文件"}

    results = {
        "total_files": len(msg_files),
        "successful_extractions": 0,
        "total_attachments": 0,
        "successful_attachments": 0,
        "file_results": []
    }

    for msg_file in msg_files:
        # 为每个msg文件创建单独的输出文件夹
        file_stem = msg_file.stem
        output_folder = os.path.join(output_base_folder, file_stem)

        print(f"\n处理文件: {msg_file.name}")
        print(f"输出文件夹: {output_folder}")

        success_count, total_count, errors = extract_attachments_from_msg(
            str(msg_file), output_folder
        )

        file_result = {
            "file_name": msg_file.name,
            "output_folder": output_folder,
            "total_attachments": total_count,
            "successful_attachments": success_count,
            "errors": errors
        }

        results["file_results"].append(file_result)
        results["total_attachments"] += total_count
        results["successful_attachments"] += success_count

        if success_count == total_count and total_count > 0:
            results["successful_extractions"] += 1

    return results


def print_extraction_summary(results):
    """打印提取结果的摘要信息"""
    print("\n" + "=" * 50)
    print("附件提取摘要")
    print("=" * 50)

    if "error" in results:
        print(f"错误: {results['error']}")
        return

    print(f"处理的文件总数: {results['total_files']}")
    print(f"成功提取的文件数: {results['successful_extractions']}")
    print(f"总附件数: {results['total_attachments']}")
    print(f"成功提取的附件数: {results['successful_attachments']}")

    for file_result in results["file_results"]:
        print(f"\n文件: {file_result['file_name']}")
        print(f"  附件数: {file_result['total_attachments']}")
        print(f"  成功提取: {file_result['successful_attachments']}")
        if file_result['errors']:
            print(f"  错误: {len(file_result['errors'])} 个")


# 测试函数
def test_extraction():
    """测试附件提取功能"""
    # 使用用户指定的路径
    msg_file = r"D:\e-mail\Cable Assy Signal Porton Partial Qualification Testing_OPS.msg"
    output_folder = r"D:\extract"

    print("开始测试附件提取...")
    print(f"源文件: {msg_file}")
    print(f"输出文件夹: {output_folder}")

    # 执行提取
    success_count, total_count, errors = extract_attachments_from_msg(msg_file, output_folder)

    # 输出结果
    print(f"\n提取完成: {success_count}/{total_count} 个附件成功提取")
    if errors:
        print("发生的错误:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("所有附件提取成功！")


if __name__ == "__main__":
    # 运行测试
    test_extraction()
