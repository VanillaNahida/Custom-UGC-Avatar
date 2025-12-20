import os
import sys
import threading
import subprocess
import logging
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QComboBox,
    QTextEdit, QGroupBox, QGridLayout, QFrame, QSizePolicy,
    QMessageBox, QProgressBar, QSplitter
)
from PyQt5.QtGui import QPixmap, QImage, QIcon, QPalette, QColor, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PIL import Image

# 导入原脚本的功能
from avatar_proxy import (
    is_admin, run_as_admin, check_dependencies,
    install_cert_auto, verify_cert_installation,
    get_running_processes, get_desktop_path, GLOBAL_FONT,
    ProxyEnvironment, get_process_pid,
    AvatarReplacer, ConnectionLogger, TlsLogger, UdpLogFilter
)
from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster
import asyncio

class ProxyThread(QThread):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, source_image, target_process):
        super().__init__()
        self.source_image = source_image
        self.target_process = target_process
        self.running = False
        self.master = None
        self.proxy_env = None
    
    def run(self):
        try:
            self.running = True
            self.status_signal.emit("启动中...")
            
            # 初始化代理环境
            self.proxy_env = ProxyEnvironment.get_instance()
            self.proxy_env.initialize()
            
            process_name = self.target_process.replace('.exe', '')
            
            pid = get_process_pid(self.target_process)
            if pid:
                self.log_signal.emit(f'[进程] 找到 {self.target_process} (PID: {pid})')
            else:
                self.log_signal.emit(f'[进程] 未找到运行中的 {self.target_process}，将监听进程名')
            
            self.log_signal.emit('\n' + '='*60)
            self.log_signal.emit('  原神头像替换代理程序')
            self.log_signal.emit('='*60)
            self.log_signal.emit(f'  源图片: {self.source_image}')
            self.log_signal.emit(f'  目标进程: {self.target_process}')
            if pid:
                self.log_signal.emit(f'  进程PID: {pid}')
            self.log_signal.emit('='*60)
            self.log_signal.emit('')
            self.log_signal.emit('[模式] 使用 mitmproxy 本地捕获模式')
            self.log_signal.emit('[提示] 正在监听请求，请进行头像上传操作')
            self.log_signal.emit('[提示] 点击停止按钮退出程序')
            self.log_signal.emit('')
            
            mode_spec = f'local:{process_name}'
            self.log_signal.emit(f'[配置] 代理模式: {mode_spec}')
            
            # 设置日志过滤
            for handler in logging.root.handlers[:]:
                handler.addFilter(UdpLogFilter())
            
            for name in ['mitmproxy', 'mitmproxy.proxy', 'mitmproxy.proxy.mode_servers', 'mitmproxy.proxy.server']:
                logger = logging.getLogger(name)
                logger.addFilter(UdpLogFilter())
                for handler in logger.handlers:
                    handler.addFilter(UdpLogFilter())
            
            # 创建异步代理函数
            async def proxy_coroutine():
                try:
                    # 创建mitmproxy选项
                    opts = options.Options(
                        mode=[mode_spec],
                        ssl_insecure=True,
                        showhost=True,
                    )
                    
                    # 启动mitmproxy
                    self.master = DumpMaster(opts, with_termlog=False)
                    self.proxy_env.set_master(self.master)
                    
                    avatar_addon = AvatarReplacer(self.source_image)
                    connection_logger = ConnectionLogger()
                    tls_logger = TlsLogger()
                    
                    self.master.addons.add(avatar_addon)
                    self.master.addons.add(connection_logger)
                    self.master.addons.add(tls_logger)
                    
                    self.log_signal.emit('[代理] 代理服务已启动')
                    
                    # 运行mitmproxy
                    await self.master.run()
                except Exception as e:
                    self.log_signal.emit(f'[错误] 代理运行异常: {e}')
                    raise
                finally:
                    if hasattr(self, 'proxy_env') and self.proxy_env:
                        self.proxy_env.cleanup()
            
            # 使用asyncio.run运行代理
            asyncio.run(proxy_coroutine())
            
        except Exception as e:
            self.error_signal.emit(str(e))
            self.status_signal.emit("启动失败")
        finally:
            # 恢复原始print函数
            import builtins
            if hasattr(builtins, 'print') and builtins.print.__name__ != 'print':
                del builtins.print
            
            if self.proxy_env:
                try:
                    self.proxy_env.cleanup()
                except:
                    pass
    
    def stop(self):
        self.running = False
        if self.master:
            try:
                self.master.shutdown()
            except:
                pass
        self.terminate()

class AvatarGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("原神头像替换工具")
        self.setGeometry(100, 100, 900, 700)
        self.setMinimumSize(800, 600)
        
        # 设置主题色
        self.setStyleSheet(""".QMainWindow {
            background-color: #f0f2f5;
        }
        
        QGroupBox {
            border: 1px solid #d0d7de;
            border-radius: 8px;
            margin-top: 6px;
            background-color: white;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            background-color: white;
            color: #24292f;
            font-weight: bold;
        }
        
        QPushButton {
            background-color: #2ea44f;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #2c974b;
        }
        
        QPushButton:pressed {
            background-color: #288a42;
        }
        
        QPushButton:disabled {
            background-color: #94d3a2;
        }
        
        QLineEdit, QComboBox {
            border: 1px solid #d0d7de;
            border-radius: 6px;
            padding: 6px 10px;
            background-color: white;
        }
        
        QLineEdit:focus, QComboBox:focus {
            border-color: #0969da;
            outline: none;
        }
        
        QTextEdit {
            border: 1px solid #d0d7de;
            border-radius: 6px;
            background-color: white;
        }
        
        QLabel {
            color: #24292f;
        }
        """)
        
        self.source_image = ""
        self.target_process = "YuanShen.exe"
        self.proxy_thread = None
        self.is_proxy_running = False
        
        self.init_ui()
        self.update_process_list()
        
    def init_ui(self):
        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部信息栏
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #0969da; color: white;")
        info_frame.setFixedHeight(40)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(10, 5, 10, 5)
        
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: white; font-weight: bold;")
        
        info_layout.addWidget(QLabel("原神头像替换工具"), 0, Qt.AlignLeft)
        info_layout.addWidget(self.status_label, 1, Qt.AlignRight)
        
        main_layout.addWidget(info_frame)
        
        # 主要内容区域
        splitter = QSplitter(Qt.Vertical)
        
        # 上半部分：配置区域
        config_widget = QWidget()
        config_layout = QHBoxLayout(config_widget)
        
        # 左侧：头像设置
        avatar_group = QGroupBox("头像设置")
        avatar_layout = QVBoxLayout(avatar_group)
        
        # 头像预览
        self.avatar_preview = QLabel()
        self.avatar_preview.setFixedSize(200, 200)
        self.avatar_preview.setStyleSheet("border: 2px solid #d0d7de; border-radius: 100px; background-color: #f6f8fa;")
        self.avatar_preview.setAlignment(Qt.AlignCenter)
        self.avatar_preview.setPixmap(self.get_default_avatar())
        
        avatar_layout.addWidget(self.avatar_preview, 0, Qt.AlignCenter)
        
        # 头像选择按钮
        self.avatar_path_edit = QLineEdit()
        self.avatar_path_edit.setPlaceholderText("头像文件路径")
        self.avatar_path_edit.setReadOnly(True)
        
        select_btn = QPushButton("选择头像")
        select_btn.clicked.connect(self.select_avatar)
        
        avatar_path_layout = QHBoxLayout()
        avatar_path_layout.addWidget(self.avatar_path_edit)
        avatar_path_layout.addWidget(select_btn)
        
        avatar_layout.addLayout(avatar_path_layout)
        
        # 右侧：进程设置
        process_group = QGroupBox("进程设置")
        process_layout = QVBoxLayout(process_group)
        
        # 进程选择
        process_label = QLabel("目标进程:")
        self.process_combo = QComboBox()
        self.process_combo.setEditable(True)
        self.process_combo.setInsertPolicy(QComboBox.NoInsert)
        
        refresh_btn = QPushButton("刷新列表")
        refresh_btn.clicked.connect(self.update_process_list)
        
        process_layout.addWidget(process_label)
        
        process_row = QHBoxLayout()
        process_row.addWidget(self.process_combo)
        process_row.addWidget(refresh_btn)
        
        process_layout.addLayout(process_row)
        
        # 中间：操作按钮
        action_group = QGroupBox("操作")
        action_layout = QVBoxLayout(action_group)
        
        self.start_btn = QPushButton("启动代理")
        self.start_btn.setFixedHeight(40)
        self.start_btn.clicked.connect(self.toggle_proxy)
        
        self.install_cert_btn = QPushButton("安装证书")
        self.install_cert_btn.clicked.connect(self.install_cert)
        
        action_layout.addWidget(self.start_btn)
        action_layout.addWidget(self.install_cert_btn)
        
        # 添加到配置布局
        config_layout.addWidget(avatar_group, 1)
        config_layout.addWidget(process_group, 1)
        config_layout.addWidget(action_group, 0)
        
        splitter.addWidget(config_widget)
        
        # 下半部分：日志区域
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("font-family: 'Microsoft YaHei', monospace; font-size: 16px;")
        
        log_layout.addWidget(self.log_text)
        
        splitter.addWidget(log_group)
        splitter.setSizes([300, 400])
        
        main_layout.addWidget(splitter)
        
        # 底部状态栏
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        
        main_layout.addWidget(self.progress_bar)
        
    def get_default_avatar(self):
        # 创建一个默认的头像
        img = QImage(200, 200, QImage.Format_RGB32)
        img.fill(QColor(246, 248, 250))
        return QPixmap.fromImage(img)
    
    def select_avatar(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择头像文件", str(get_desktop_path()), "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.source_image = file_path
            self.avatar_path_edit.setText(file_path)
            self.update_avatar_preview(file_path)
    
    def update_avatar_preview(self, file_path):
        try:
            # 加载图片并调整大小
            img = Image.open(file_path)
            img = img.resize((200, 200), Image.Resampling.LANCZOS)
            
            # 转换为圆形
            from avatar_proxy import make_circle_avatar
            img = make_circle_avatar(img)
            
            # 保存为临时文件或直接转换为 QPixmap
            temp_path = Path(file_path).parent / "temp_preview.png"
            img.save(temp_path)
            
            pixmap = QPixmap(str(temp_path))
            self.avatar_preview.setPixmap(pixmap)
            
            # 删除临时文件
            temp_path.unlink()
            
            self.log(f"已加载头像: {file_path}")
        except Exception as e:
            self.log(f"头像加载失败: {e}")
            QMessageBox.warning(self, "警告", f"无法加载头像文件: {e}")
    
    def update_process_list(self):
        try:
            self.log("刷新进程列表...")
            processes = get_running_processes()
            
            # 清空并添加进程
            self.process_combo.clear()
            for name, _ in processes:
                self.process_combo.addItem(name)
            
            # 设置默认值
            if self.target_process:
                index = self.process_combo.findText(self.target_process)
                if index >= 0:
                    self.process_combo.setCurrentIndex(index)
            
            self.log(f"已加载 {len(processes)} 个进程")
        except Exception as e:
            self.log(f"进程列表刷新失败: {e}")
    
    def install_cert(self):
        try:
            self.log("正在安装证书...")
            self.progress_bar.show()
            self.progress_bar.setValue(25)
            
            # 安装证书
            result = install_cert_auto()
            self.progress_bar.setValue(50)
            
            if result:
                # 验证证书
                verify_result = verify_cert_installation()
                self.progress_bar.setValue(100)
                
                if verify_result:
                    self.log("证书安装和验证成功")
                    QMessageBox.information(self, "成功", "证书安装和验证成功！")
                else:
                    self.log("证书安装成功，但验证失败")
                    QMessageBox.warning(self, "警告", "证书安装成功，但验证失败！")
            else:
                self.progress_bar.setValue(100)
                self.log("证书安装失败")
                QMessageBox.critical(self, "错误", "证书安装失败！")
            
            self.progress_bar.hide()
        except Exception as e:
            self.progress_bar.hide()
            self.log(f"证书安装异常: {e}")
            QMessageBox.critical(self, "错误", f"证书安装异常: {e}")
    
    def toggle_proxy(self):
        if not self.is_proxy_running:
            self.start_proxy()
        else:
            self.stop_proxy()
    
    def start_proxy(self):
        # 检查必要条件
        if not self.source_image:
            QMessageBox.warning(self, "警告", "请先选择头像文件！")
            return
        
        if not Path(self.source_image).exists():
            QMessageBox.warning(self, "警告", "头像文件不存在！")
            return
        
        self.target_process = self.process_combo.currentText()
        if not self.target_process:
            QMessageBox.warning(self, "警告", "请选择目标进程！")
            return
        
        # 检查管理员权限
        if not is_admin():
            self.log("需要管理员权限，正在请求提升...")
            if run_as_admin():
                sys.exit(0)
            else:
                QMessageBox.critical(self, "错误", "无法获取管理员权限！")
                return
        
        # 检查依赖
        if not check_dependencies():
            QMessageBox.critical(self, "错误", "缺少必要依赖，请先安装依赖！")
            return
        
        # 检查证书
        if not verify_cert_installation():
            self.log("证书未安装或验证失败，正在尝试安装...")
            if not install_cert_auto() or not verify_cert_installation():
                QMessageBox.critical(self, "错误", "证书安装或验证失败！")
                return
        
        # 启动代理
        self.log("正在启动代理...")
        self.status_label.setText("启动中...")
        self.start_btn.setText("停止代理")
        
        # 创建并启动代理线程
        self.proxy_thread = ProxyThread(self.source_image, self.target_process)
        self.proxy_thread.log_signal.connect(self.log)
        self.proxy_thread.status_signal.connect(self.update_status)
        self.proxy_thread.error_signal.connect(self.show_error)
        self.proxy_thread.finished.connect(self.proxy_finished)
        
        self.proxy_thread.start()
        self.is_proxy_running = True
    
    def stop_proxy(self):
        if self.proxy_thread and self.is_proxy_running:
            self.log("正在停止代理...")
            self.proxy_thread.stop()
            self.is_proxy_running = False
    
    def proxy_finished(self):
        self.is_proxy_running = False
        self.start_btn.setText("启动代理")
        self.status_label.setText("就绪")
        self.log("代理已停止")
    
    def log(self, message):
        self.log_text.append(message)
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)
    
    def update_status(self, status):
        self.status_label.setText(status)
        self.log(f"状态更新: {status}")
    
    def show_error(self, error):
        QMessageBox.critical(self, "错误", f"代理运行错误: {error}")
        self.log(f"错误: {error}")
        self.stop_proxy()
    
    def closeEvent(self, event):
        # 关闭前停止代理
        if self.is_proxy_running:
            self.stop_proxy()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # 设置全局字体
    font = QFont()
    font.setFamily(GLOBAL_FONT)
    app.setFont(font)
    
    # 设置应用图标
    app.setWindowIcon(QIcon.fromTheme("image"))
    
    # 检查是否以管理员权限运行
    if not is_admin():
        QMessageBox.warning(None, "警告", "建议以管理员权限运行程序，否则可能无法正常工作！点击OK键以管理员身份重启。")
        # 尝试重新以管理员身份运行
        if run_as_admin():
            sys.exit(0)
    
    # 初始化代理环境
    from avatar_proxy import ProxyEnvironment
    proxy_env = ProxyEnvironment.get_instance()
    proxy_env.initialize()
    
    # 注册应用关闭事件
    def cleanup():
        proxy_env.cleanup()
    
    app.aboutToQuit.connect(cleanup)
    
    gui = AvatarGUI()
    gui.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
