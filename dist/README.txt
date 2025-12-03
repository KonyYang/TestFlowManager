TestFlowManager 使用说明
========================

这是一个独立的Windows应用程序，可以直接运行而无需安装Python。

目录结构说明:
- TestFlowManager.exe: 主程序文件
- config/: 配置文件目录
- Template/: 模板文件目录
- Projects/: 项目文件目录
- Temp/: 临时文件目录
- Backup/: 备份文件目录
- logs/: 日志文件目录

使用方法:
1. 首先，将整个目录结构移动到 D:\TestFlowManager 路径下
2. 根据实际环境修改 D:\TestFlowManager\config\paths.ini 文件中的配置项：
   - 修改实际路径配置（如ltr_file等）
   - 更新密码配置（如ltr_password）
   - 根据使用者不同调整默认值配置（如project_leader）
3. 双击 TestFlowManager.exe 即可运行程序

注意事项:
1. 请勿删除或移动此目录中的任何文件，否则可能导致程序无法正常运行。
2. 程序会在logs目录中生成日志文件，可用于问题排查。
3. 如需重新配置，请修改config目录中的配置文件。
4. 如果遇到路径相关的问题，请检查paths.ini文件中的配置是否正确。
5. 确保程序运行时有足够的权限访问所有需要的目录和文件。

版本信息:
- 当前版本: 1.0.0
- 发布日期: 2025-12-03

技术支持:
如有任何问题，请联系技术支持团队。
