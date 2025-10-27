import os
import sys
import json
import uuid
import random
import shutil
import subprocess
import time
from datetime import datetime

# 仅在 Windows 平台导入 winreg
if sys.platform == "win32":
    import winreg
    import stat

class CursorResetLogic:
    """
    负责处理 Cursor ID 重置的所有底层业务逻辑。
    """
    def __init__(self, status_callback=None):
        self.status_callback = status_callback
        self.cursor_process_name = "cursor.exe" if sys.platform == "win32" else "cursor"
        self.storage_path = self._get_storage_path()
        self.backup_dir = os.path.join(os.path.expanduser("~"), "cursor_backups")

    def _update_status(self, message):
        """通过回调函数向 UI 更新状态信息"""
        if self.status_callback:
            self.status_callback(message)

    def _get_storage_path(self):
        """获取 storage.json 文件的路径"""
        if sys.platform == "win32":
            # Windows: %APPDATA%\Cursor\User\globalStorage\storage.json
            return os.path.join(os.getenv("APPDATA"), "Cursor", "User", "globalStorage", "storage.json")
        elif sys.platform == "darwin":
            # macOS: ~/Library/Application Support/Cursor/User/globalStorage/storage.json
            return os.path.expanduser("~/Library/Application Support/Cursor/User/globalStorage/storage.json")
        else:
            # Linux: ~/.config/Cursor/User/globalStorage/storage.json
            return os.path.expanduser("~/.config/Cursor/User/globalStorage/storage.json")

    def new_mac_machine_id(self):
        """生成符合 V4 UUID 规范的 macMachineId"""
        template = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"
        result = ""
        for char in template:
            if char in ['x', 'y']:
                r = random.randint(0, 15)
                # 'x' is any hex digit, 'y' is 8, 9, A, or B
                v = r if char == 'x' else (r & 0x3 | 0x8)
                result += hex(v)[2:]
            else:
                result += char
        return result

    def new_random_id(self):
        """生成 telemetry.machineId (长度为 64 的十六进制字符串)"""
        # 原始代码是 uuid.uuid4().hex + uuid.uuid4().hex (32 + 32 = 64)
        return uuid.uuid4().hex + uuid.uuid4().hex

    def wait_for_cursor_exit(self):
        """等待 Cursor 进程退出"""
        self._update_status("正在检查 Cursor 进程...")
        while True:
            try:
                if sys.platform == "win32":
                    # 使用 tasklist 检查进程
                    output = subprocess.check_output(["tasklist", "/FI", f"IMAGENAME eq {self.cursor_process_name}"]).decode()
                    cursor_running = self.cursor_process_name in output
                else:
                    # 使用 ps aux 检查进程
                    output = subprocess.check_output(["ps", "aux"]).decode()
                    cursor_running = self.cursor_process_name in output
                
                if not cursor_running:
                    self._update_status("Cursor 已关闭，继续执行...")
                    return True
                
                self._update_status("正在等待 Cursor 进程退出...")
                time.sleep(1)
            except subprocess.CalledProcessError:
                # tasklist/ps aux 失败，通常意味着没有进程列表，可以安全退出
                return True
            except Exception as e:
                self._update_status(f"等待 Cursor 退出时发生错误: {e}")
                return False

    # --- Windows 注册表相关操作 ---
    def backup_machine_guid(self):
        """备份 Windows 注册表中的 MachineGuid"""
        if sys.platform != "win32":
            return None
        
        try:
            # 创建备份目录
            backup_dir = os.path.join(os.path.expanduser("~"), "MachineGuid_Backups")
            os.makedirs(backup_dir, exist_ok=True)

            # 读取当前的 MachineGuid
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ)
            current_guid = winreg.QueryValueEx(key, "MachineGuid")[0]
            winreg.CloseKey(key)

            # 创建备份文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"MachineGuid_{timestamp}.txt")
            
            # 避免文件名冲突
            counter = 0
            temp_file = backup_file
            while os.path.exists(temp_file):
                counter += 1
                temp_file = os.path.join(backup_dir, f"MachineGuid_{timestamp}_{counter}.txt")
            backup_file = temp_file

            with open(backup_file, 'w') as f:
                f.write(current_guid)

            self._update_status(f"MachineGuid 已备份到: {backup_file}")
            return backup_file
        except Exception as e:
            self._update_status(f"备份 MachineGuid 时出错: {str(e)}")
            return None

    def update_machine_guid(self):
        """更新 Windows 注册表中的 MachineGuid"""
        if sys.platform != "win32":
            return None
            
        try:
            new_guid = str(uuid.uuid4()).upper()
            # 需要管理员权限才能写入 HKEY_LOCAL_MACHINE
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "MachineGuid", 0, winreg.REG_SZ, new_guid)
            winreg.CloseKey(key)
            self._update_status(f"新的 MachineGuid: {new_guid}")
            return new_guid
        except PermissionError:
            self._update_status("更新 MachineGuid 失败：需要管理员权限。请以管理员身份运行程序。")
            return None
        except Exception as e:
            self._update_status(f"更新 MachineGuid 时出错: {str(e)}")
            return None

    # --- storage.json 相关操作 ---
    def _backup_storage_json(self):
        """备份 storage.json 文件"""
        if not os.path.exists(self.storage_path):
            return None
            
        os.makedirs(self.backup_dir, exist_ok=True)
        backup_file = os.path.join(self.backup_dir, f"storage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        shutil.copy2(self.storage_path, backup_file)
        self._update_status(f"storage.json 已备份到: {backup_file}")
        return backup_file

    def _read_storage_json(self):
        """读取 storage.json 文件内容"""
        if not os.path.exists(self.storage_path):
            self._update_status("错误：未找到 storage.json 文件")
            return None
            
        try:
            # 尝试处理只读属性
            if sys.platform == "win32":
                original_attributes = os.stat(self.storage_path)
                subprocess.run(['attrib', '-R', self.storage_path], check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 恢复原始属性
            if sys.platform == "win32":
                os.chmod(self.storage_path, original_attributes.st_mode)
            
            return data
        except json.JSONDecodeError:
            self._update_status("错误：storage.json 文件格式错误，无法解析。")
            return None
        except Exception as e:
            self._update_status(f"读取 storage.json 时出错: {str(e)}")
            return None

    def _write_storage_json(self, data):
        """写入 storage.json 文件内容"""
        try:
            # 尝试处理只读属性
            if sys.platform == "win32":
                original_attributes = os.stat(self.storage_path)
                subprocess.run(['attrib', '-R', self.storage_path], check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            
            # 使用 UTF-8 无 BOM 编码保存文件
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            
            # 确保 Windows 上的换行符是 \r\n
            if sys.platform == "win32":
                json_str = json_str.replace('\n', '\r\n')
            
            # 写入文件，使用 'utf-8' 编码，避免写入 BOM
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                f.write(json_str)

            # 恢复原始属性
            if sys.platform == "win32":
                os.chmod(self.storage_path, original_attributes.st_mode)

            return True
        except Exception as e:
            self._update_status(f"写入 storage.json 时出错: {str(e)}")
            return False

    def reset_all_ids(self):
        """执行完整的 ID 重置流程"""
        self._update_status("--- 开始重置 Cursor ID ---")

        # 1. 检查并等待 Cursor 退出
        if not self.wait_for_cursor_exit():
            return False

        # 2. 备份 MachineGuid (仅限 Windows)
        if sys.platform == "win32":
            self.backup_machine_guid()

        # 3. 生成新的 ID
        new_ids = {
            "telemetry.machineId": self.new_random_id(),
            "telemetry.macMachineId": self.new_mac_machine_id(),
            "telemetry.devDeviceId": str(uuid.uuid4()),
            "telemetry.sqmId": "{" + str(uuid.uuid4()).upper() + "}"
        }
        
        self._update_status("已生成新的 ID:")
        for key, value in new_ids.items():
            self._update_status(f"  {key}: {value}")

        # 4. 更新 storage.json
        self._update_status("正在处理 storage.json...")
        backup_file = self._backup_storage_json()
        if not backup_file:
            self._update_status("重置失败：无法备份或找到 storage.json。")
            return False

        data = self._read_storage_json()
        if data is None:
            self._update_status("重置失败：无法读取或解析 storage.json。")
            return False

        # 更新 data
        data.update(new_ids)

        # 写入文件
        if not self._write_storage_json(data):
            self._update_status("重置失败：无法写入 storage.json。")
            return False
            
        self._update_status("已成功更新 storage.json 中的 ID。")

        # 5. 更新 MachineGuid (仅限 Windows)
        if sys.platform == "win32":
            self._update_status("正在更新 Windows MachineGuid...")
            if self.update_machine_guid():
                self._update_status("MachineGuid 更新成功。")
            else:
                self._update_status("MachineGuid 更新失败（可能需要管理员权限）。")
        
        self._update_status("--- Cursor ID 重置完成！ ---")
        return True

if __name__ == '__main__':
    # 示例用法
    def print_status(msg):
        print(msg)

    logic = CursorResetLogic(print_status)
    # result = logic.reset_all_ids()
    # print(f"重置结果: {result}")

