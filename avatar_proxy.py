import os
import sys
import struct
import zlib
import asyncio
import ctypes
import subprocess
import multiprocessing
import logging
import re
import signal
import atexit
from pathlib import Path
from io import BytesIO

GLOBAL_FONT = 'Microsoft YaHei UI'


class ProxyEnvironment:
    _instance = None
    _initialized = False
    _master = None
    _console_handler_set = False
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self._cleanup_done = False
    
    def initialize(self):
        if ProxyEnvironment._initialized:
            return
        self._cleanup_existing_drivers()
        self._register_cleanup_handlers()
        ProxyEnvironment._initialized = True
        sys.stdout.write('[环境] 代理环境初始化完成\n')
    
    def _run_command(self, cmd, use_shell=False):
        try:
            if getattr(sys, 'frozen', False):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                if use_shell or isinstance(cmd, str):
                    subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        startupinfo=startupinfo,
                        timeout=10
                    )
                else:
                    subprocess.run(
                        cmd,
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        startupinfo=startupinfo,
                        timeout=10
                    )
            else:
                subprocess.run(
                    cmd,
                    shell=use_shell if isinstance(cmd, str) else False,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=10
                )
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass
    
    def _kill_redirector_processes(self):
        self._run_command('taskkill /F /IM windows-redirector.exe', use_shell=True)
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    name = proc.info['name']
                    if name and 'redirector' in name.lower():
                        proc.kill()
                except:
                    pass
        except:
            pass
    
    def _delete_windivert_registry(self):
        try:
            import winreg
            keys_to_delete = [
                r'SYSTEM\CurrentControlSet\Services\WinDivert',
                r'SYSTEM\CurrentControlSet\Services\WinDivert14',
            ]
            for key_path in keys_to_delete:
                try:
                    winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                except FileNotFoundError:
                    pass
                except:
                    pass
        except:
            pass
    
    def _cleanup_existing_drivers(self):
        sys.stdout.write('[环境] 正在清理残留的网络驱动...\n')
        self._kill_redirector_processes()
        self._run_command('sc stop WinDivert', use_shell=True)
        self._run_command('sc stop WinDivert14', use_shell=True)
        self._run_command('sc delete WinDivert', use_shell=True)
        self._run_command('sc delete WinDivert14', use_shell=True)
        self._delete_windivert_registry()
        self._run_command('netsh winhttp reset proxy', use_shell=True)
        try:
            import time
            time.sleep(1.0)
        except:
            pass
        sys.stdout.write('[环境] 网络驱动清理完成\n')
    
    def _console_ctrl_handler(self, ctrl_type):
        CTRL_C_EVENT = 0
        CTRL_BREAK_EVENT = 1
        CTRL_CLOSE_EVENT = 2
        CTRL_LOGOFF_EVENT = 5
        CTRL_SHUTDOWN_EVENT = 6
        
        if ctrl_type in (CTRL_C_EVENT, CTRL_BREAK_EVENT, CTRL_CLOSE_EVENT, 
                         CTRL_LOGOFF_EVENT, CTRL_SHUTDOWN_EVENT):
            sys.stdout.write(f'\n[系统] 收到控制台事件 ({ctrl_type})，正在清理...\n')
            self.cleanup()
            return True
        return False
    
    def _register_cleanup_handlers(self):
        atexit.register(self.cleanup)
        
        if sys.platform == 'win32':
            try:
                if not ProxyEnvironment._console_handler_set:
                    HANDLER_ROUTINE = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_uint)
                    self._handler_func = HANDLER_ROUTINE(self._console_ctrl_handler)
                    ctypes.windll.kernel32.SetConsoleCtrlHandler(self._handler_func, True)
                    ProxyEnvironment._console_handler_set = True
                    sys.stdout.write('[环境] 已注册 Windows 控制台事件处理器\n')
            except Exception as e:
                sys.stdout.write(f'[环境] 无法注册控制台事件处理器: {e}\n')
            
            try:
                signal.signal(signal.SIGINT, self._signal_handler)
                signal.signal(signal.SIGTERM, self._signal_handler)
                signal.signal(signal.SIGBREAK, self._signal_handler)
            except:
                pass
        else:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        sys.stdout.write(f'\n[系统] 收到退出信号 ({signum})，正在清理...\n')
        self.cleanup()
        os._exit(0)
    
    def set_master(self, master):
        ProxyEnvironment._master = master
    
    def cleanup(self):
        if self._cleanup_done:
            return
        self._cleanup_done = True
        sys.stdout.write('[环境] 正在恢复系统环境...\n')
        
        if ProxyEnvironment._master:
            try:
                ProxyEnvironment._master.shutdown()
            except:
                pass
            ProxyEnvironment._master = None
        
        self._kill_redirector_processes()
        self._run_command('sc stop WinDivert', use_shell=True)
        self._run_command('sc stop WinDivert14', use_shell=True)
        self._run_command('sc delete WinDivert', use_shell=True)
        self._run_command('sc delete WinDivert14', use_shell=True)
        self._delete_windivert_registry()
        self._run_command('netsh winhttp reset proxy', use_shell=True)
        self._run_command('netsh interface ip set dns name="以太网" source=dhcp', use_shell=True)
        self._run_command('netsh interface ip set dns name="WLAN" source=dhcp', use_shell=True)
        self._run_command('netsh interface ip set dns name="Ethernet" source=dhcp', use_shell=True)
        self._run_command('netsh interface ip set dns name="Wi-Fi" source=dhcp', use_shell=True)
        
        try:
            import time
            time.sleep(0.5)
        except:
            pass
        sys.stdout.write('[环境] 系统环境已恢复\n')


class FilteredStdout:
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
        self.buffer = ""
        self.udp_patterns = [
            re.compile(r'.*->\s*udp\s*->.*', re.IGNORECASE),
            re.compile(r'.*udp.*:.*:.*:.*:.*', re.IGNORECASE),
            re.compile(r'.*\[.*\]:.*->\s*udp', re.IGNORECASE),
        ]
    
    def write(self, text):
        self.buffer += text
        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            if not self._should_filter(line):
                self.original_stdout.write(line + '\n')
    
    def _should_filter(self, line):
        line_lower = line.lower()
        if '-> udp ->' in line_lower:
            return True
        if 'udp' in line_lower and ']:' in line and '->' in line:
            return True
        for pattern in self.udp_patterns:
            if pattern.match(line):
                return True
        return False
    
    def flush(self):
        if self.buffer and not self._should_filter(self.buffer):
            self.original_stdout.write(self.buffer)
        self.buffer = ""
        self.original_stdout.flush()
    
    def isatty(self):
        return self.original_stdout.isatty() if hasattr(self.original_stdout, 'isatty') else False
    
    def fileno(self):
        return self.original_stdout.fileno() if hasattr(self.original_stdout, 'fileno') else -1
    
    def __getattr__(self, name):
        return getattr(self.original_stdout, name)


sys.stdout = FilteredStdout(sys.stdout)
sys.stderr = FilteredStdout(sys.stderr)


def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if sys.platform != 'win32':
        return False
    try:
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
            params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", exe_path, params, None, 1)
        else:
            script = os.path.abspath(sys.argv[0])
            params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        return True
    except:
        return False

def get_desktop_path():
    return Path(os.path.expanduser('~/Desktop'))

def get_mitmproxy_cert_path():
    return Path(os.path.expanduser('~/.mitmproxy/mitmproxy-ca-cert.cer'))

def is_cert_installed():
    try:
        result = subprocess.run(
            ['certutil', '-store', 'Root'],
            capture_output=True,
            text=True,
            encoding='gbk',
            errors='ignore'
        )
        return 'mitmproxy' in result.stdout.lower()
    except:
        return False

def verify_cert_installation():
    cert_path = get_mitmproxy_cert_path()
    if not cert_path.exists():
        sys.stdout.write('[证书验证] 证书文件不存在\n')
        return False
    
    if not is_cert_installed():
        sys.stdout.write('[证书验证] 证书未安装到系统信任存储\n')
        return False
    
    try:
        result = subprocess.run(
            ['certutil', '-verify', str(cert_path)],
            capture_output=True,
            text=True,
            encoding='gbk',
            errors='ignore'
        )
        if result.returncode == 0:
            sys.stdout.write('[证书验证] 证书验证通过\n')
            return True
        else:
            sys.stdout.write(f'[证书验证] 证书验证失败: {result.stderr}\n')
            return False
    except Exception as e:
        sys.stdout.write(f'[证书验证] 验证异常: {e}\n')
        return False

def generate_mitmproxy_cert():
    cert_path = get_mitmproxy_cert_path()
    if cert_path.exists():
        return True
    sys.stdout.write('[证书] 正在生成 mitmproxy 证书...\n')
    try:
        from mitmproxy.certs import CertStore
        certstore_path = Path(os.path.expanduser('~/.mitmproxy'))
        certstore_path.mkdir(parents=True, exist_ok=True)
        CertStore.from_store(str(certstore_path), 'mitmproxy', 2048)
        return cert_path.exists()
    except Exception as e:
        sys.stdout.write(f'[证书] 生成失败: {e}\n')
        return False

def install_cert_auto():
    cert_path = get_mitmproxy_cert_path()
    if not cert_path.exists():
        if not generate_mitmproxy_cert():
            sys.stdout.write('[证书] 无法生成证书\n')
            return False
    if is_cert_installed():
        sys.stdout.write('[证书] 证书已安装\n')
        return True
    sys.stdout.write('[证书] 正在安装证书到受信任的根证书颁发机构...\n')
    try:
        result = subprocess.run(
            ['certutil', '-addstore', '-f', 'Root', str(cert_path)],
            capture_output=True,
            text=True,
            encoding='gbk',
            errors='ignore'
        )
        if result.returncode == 0:
            sys.stdout.write('[证书] 安装成功\n')
            return True
        else:
            sys.stdout.write(f'[证书] 安装失败: {result.stderr}\n')
            return False
    except Exception as e:
        sys.stdout.write(f'[证书] 安装异常: {e}\n')
        return False

def get_running_processes():
    try:
        import psutil
    except ImportError:
        sys.stdout.write('[错误] 需要安装 psutil: pip install psutil\n')
        return []
    
    processes = {}
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name']
            if name and name.endswith('.exe'):
                if name not in processes:
                    processes[name] = proc.info['pid']
        except:
            pass
    
    sorted_procs = sorted(processes.items(), key=lambda x: x[0].lower())
    return sorted_procs

def select_process(default='YuanShen.exe'):
    sys.stdout.write('\n' + '='*60 + '\n')
    sys.stdout.write('  当前运行的进程列表\n')
    sys.stdout.write('='*60 + '\n')
    
    procs = get_running_processes()
    if not procs:
        sys.stdout.write('[警告] 无法获取进程列表，使用默认进程\n')
        return default
    
    page_size = 20
    total_pages = (len(procs) + page_size - 1) // page_size
    current_page = 0
    
    default_index = None
    for i, (name, _) in enumerate(procs):
        if name.lower() == default.lower():
            default_index = i
            break
    
    while True:
        start = current_page * page_size
        end = min(start + page_size, len(procs))
        
        sys.stdout.write(f'\n第 {current_page + 1}/{total_pages} 页 (共 {len(procs)} 个进程)\n\n')
        
        for i in range(start, end):
            name, pid = procs[i]
            marker = ' *' if name.lower() == default.lower() else ''
            sys.stdout.write(f'  [{i + 1:3d}] {name}{marker}\n')
        
        sys.stdout.write('\n')
        sys.stdout.write('  [n] 下一页  [p] 上一页  [回车] 使用默认  [0] 手动输入\n')
        
        choice = input(f'\n请选择进程编号 (默认: {default}): ').strip()
        
        if choice == '':
            return default
        elif choice.lower() == 'n':
            if current_page < total_pages - 1:
                current_page += 1
            continue
        elif choice.lower() == 'p':
            if current_page > 0:
                current_page -= 1
            continue
        elif choice == '0':
            custom = input('请输入进程名 (如 YuanShen.exe): ').strip()
            if custom:
                return custom
            continue
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(procs):
                    return procs[idx][0]
            except:
                pass
            sys.stdout.write('[错误] 无效选择\n')

def get_process_pid(process_name):
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                    return proc.info['pid']
            except:
                pass
    except:
        pass
    return None

def make_circle_avatar(img):
    from PIL import Image, ImageDraw
    size = img.size[0]
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size-1, size-1), fill=255)
    result = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    img_rgba = img.convert('RGBA')
    result.paste(img_rgba, (0, 0), mask)
    return result

def convert_to_palette_with_transparency(img, colors):
    from PIL import Image
    rgba = img.convert('RGBA')
    rgb = Image.new('RGB', rgba.size, (0, 0, 0))
    rgb.paste(rgba, mask=rgba.split()[3])
    p_img = rgb.quantize(colors=colors-1, method=Image.Quantize.MEDIANCUT)
    alpha = rgba.split()[3]
    palette = list(p_img.getpalette())
    new_palette = [0, 0, 0] + palette[:765]
    result = Image.new('P', rgba.size)
    result.putpalette(new_palette)
    pixels = list(p_img.getdata())
    alpha_data = list(alpha.getdata())
    new_pixels = []
    for i, (px, a) in enumerate(zip(pixels, alpha_data)):
        if a == 0:
            new_pixels.append(0)
        else:
            new_pixels.append(px + 1)
    result.putdata(new_pixels)
    return result

def create_png_with_exact_size(source_path, target_size, image_size):
    try:
        from PIL import Image
    except ImportError:
        sys.stdout.write('[错误] 需要安装 Pillow: pip install Pillow\n')
        return None
    
    img = Image.open(source_path)
    target_w, target_h = image_size
    img_w, img_h = img.size
    ratio = max(target_w / img_w, target_h / img_h)
    new_w = int(img_w * ratio)
    new_h = int(img_h * ratio)
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))
    img = make_circle_avatar(img)
    
    best_data = None
    best_diff = float('inf')
    
    modes = [
        ('RGBA', lambda i: i.convert('RGBA'), False),
        ('P255', lambda i: convert_to_palette_with_transparency(i, 255), True),
        ('P128', lambda i: convert_to_palette_with_transparency(i, 128), True),
        ('P64', lambda i: convert_to_palette_with_transparency(i, 64), True),
        ('P32', lambda i: convert_to_palette_with_transparency(i, 32), True),
        ('P16', lambda i: convert_to_palette_with_transparency(i, 16), True),
    ]
    
    for mode_name, converter, needs_transparency in modes:
        try:
            converted = converter(img)
            for level in range(0, 10):
                buf = BytesIO()
                if needs_transparency and converted.mode == 'P':
                    converted.save(buf, format='PNG', compress_level=level, optimize=True, transparency=0)
                else:
                    converted.save(buf, format='PNG', compress_level=level, optimize=True)
                data = buf.getvalue()
                diff = target_size - len(data)
                if 0 <= diff < best_diff:
                    best_data = data
                    best_diff = diff
                    sys.stdout.write(f'[图片] {mode_name} lv{level}: {len(data)}b (差{diff})\n')
        except Exception as e:
            pass
    
    if best_data is None or best_diff < 0:
        sys.stdout.write(f'[错误] 无法压缩到目标大小\n')
        return None
    
    padding = target_size - len(best_data)
    sys.stdout.write(f'[图片] 最佳: {len(best_data)}b, 填充: {padding}b\n')
    
    if padding == 0:
        return best_data
    
    if padding < 12:
        return None
    
    iend_pos = len(best_data) - 12
    if best_data[iend_pos+4:iend_pos+8] != b'IEND':
        iend_pos = best_data.rfind(b'IEND') - 4
        if iend_pos < 0:
            return None
    
    data_len = padding - 12
    text_len = max(0, data_len - 2)
    chunk_data = b'X\x00' + b'P' * text_len
    chunk_type = b'tEXt'
    crc = zlib.crc32(chunk_type + chunk_data) & 0xffffffff
    chunk = struct.pack('>I', len(chunk_data)) + chunk_type + chunk_data + struct.pack('>I', crc)
    final = best_data[:iend_pos] + chunk + best_data[iend_pos:]
    
    if len(final) != target_size:
        return None
    
    return final


class AvatarReplacer:
    def __init__(self, source_image_path):
        self.source_image = source_image_path
        self.request_count = 0
        sys.stdout.write(f'[配置] 源图片: {self.source_image}\n')
        if not os.path.exists(self.source_image):
            raise FileNotFoundError(f'头像文件不存在: {self.source_image}')
    
    def request(self, flow):
        if hasattr(flow, 'metadata') and flow.metadata.get('mode', '') == 'dns':
            return
        
        if hasattr(flow, 'client_conn') and hasattr(flow.client_conn, 'transport_protocol'):
            if flow.client_conn.transport_protocol == 'udp':
                return
        
        request = flow.request
        url = request.pretty_url
        self.request_count += 1
        
        scheme = 'HTTPS' if url.startswith('https://') else 'HTTP'
        sys.stdout.write(f'\n[{scheme}#{self.request_count}] ═══════════════════════════════════════\n')
        sys.stdout.write(f'[{scheme}#{self.request_count}] 方法: {request.method}\n')
        sys.stdout.write(f'[{scheme}#{self.request_count}] URL: {url}\n')
        sys.stdout.write(f'[{scheme}#{self.request_count}] Host: {request.host}:{request.port}\n')
        sys.stdout.write(f'[{scheme}#{self.request_count}] 请求头:\n')
        for key, value in request.headers.items():
            sys.stdout.write(f'[{scheme}#{self.request_count}]   {key}: {value}\n')
        if request.content:
            sys.stdout.write(f'[{scheme}#{self.request_count}] 请求体大小: {len(request.content)} bytes\n')
        sys.stdout.write(f'[{scheme}#{self.request_count}] ═══════════════════════════════════════\n')
        
        if request.method != 'PUT':
            return
        
        content_type = request.headers.get('Content-Type', '')
        if 'image' not in content_type:
            return
        
        sys.stdout.write(f'\n[拦截] ═══════════════════════════════════════\n')
        sys.stdout.write(f'[拦截] PUT {url[:80]}...\n')
        
        content_length = request.headers.get('Content-Length')
        if content_length is None:
            sys.stdout.write('[拦截] 无 Content-Length\n')
            return
        
        try:
            target_size = int(content_length)
        except:
            sys.stdout.write('[拦截] Content-Length 解析失败\n')
            return
        
        sys.stdout.write(f'[拦截] 目标大小: {target_size}b\n')
        
        if '_thn' in url:
            image_size = (256, 256)
            sys.stdout.write('[拦截] 类型: 缩略图 256x256\n')
        else:
            image_size = (512, 512)
            sys.stdout.write('[拦截] 类型: 原图 512x512\n')
        
        new_data = create_png_with_exact_size(self.source_image, target_size, image_size)
        
        if new_data and len(new_data) == target_size:
            request.content = new_data
            sys.stdout.write(f'[拦截] ✓ 替换成功! ({len(new_data)}b)\n')
        else:
            sys.stdout.write('[拦截] ✗ 生成失败\n')
    
    def response(self, flow):
        if hasattr(flow, 'metadata') and flow.metadata.get('mode', '') == 'dns':
            return
        
        if hasattr(flow, 'client_conn') and hasattr(flow.client_conn, 'transport_protocol'):
            if flow.client_conn.transport_protocol == 'udp':
                return
        
        url = flow.request.pretty_url
        scheme = 'HTTPS' if url.startswith('https://') else 'HTTP'
        
        sys.stdout.write(f'\n[{scheme}响应] ═══════════════════════════════════════\n')
        sys.stdout.write(f'[{scheme}响应] URL: {url[:80]}...\n')
        sys.stdout.write(f'[{scheme}响应] 状态码: {flow.response.status_code}\n')
        sys.stdout.write(f'[{scheme}响应] 响应头:\n')
        for key, value in flow.response.headers.items():
            sys.stdout.write(f'[{scheme}响应]   {key}: {value}\n')
        if flow.response.content:
            content_preview = flow.response.content[:200] if len(flow.response.content) > 200 else flow.response.content
            sys.stdout.write(f'[{scheme}响应] 响应体大小: {len(flow.response.content)} bytes\n')
            try:
                sys.stdout.write(f'[{scheme}响应] 响应体预览: {content_preview.decode("utf-8", errors="ignore")}\n')
            except:
                pass
        sys.stdout.write(f'[{scheme}响应] ═══════════════════════════════════════\n')
        
        if 'cngf01-picture-upload' in url:
            if flow.response.status_code == 200:
                sys.stdout.write('[结果] ═══════════════════════════════════════\n')
                sys.stdout.write('[结果] ✓✓✓ 上传成功! ✓✓✓\n')
                sys.stdout.write('[结果] ═══════════════════════════════════════\n\n')
            else:
                sys.stdout.write(f'[结果] ✗ 上传失败: {flow.response.status_code}\n')


class UdpLogFilter(logging.Filter):
    def filter(self, record):
        msg = str(record.getMessage()) if hasattr(record, 'getMessage') else str(record.msg)
        if 'udp' in msg.lower():
            return False
        if '-> udp ->' in msg:
            return False
        return True


class ConnectionLogger:
    def client_connected(self, client):
        addr = str(client.peername) if hasattr(client, 'peername') else str(client)
        if 'udp' in addr.lower():
            return
        sys.stdout.write(f'[连接] 客户端连接: {client.peername}\n')
    
    def client_disconnected(self, client):
        addr = str(client.peername) if hasattr(client, 'peername') else str(client)
        if 'udp' in addr.lower():
            return
        sys.stdout.write(f'[连接] 客户端断开: {client.peername}\n')
    
    def server_connect(self, data):
        if hasattr(data, 'server') and hasattr(data.server, 'transport_protocol'):
            if data.server.transport_protocol == 'udp':
                return
        sys.stdout.write(f'[连接] 连接服务器: {data.server.address}\n')
    
    def server_connected(self, data):
        if hasattr(data, 'server') and hasattr(data.server, 'transport_protocol'):
            if data.server.transport_protocol == 'udp':
                return
        sys.stdout.write(f'[连接] 服务器已连接: {data.server.address}\n')
    
    def server_disconnected(self, data):
        if hasattr(data, 'server') and hasattr(data.server, 'transport_protocol'):
            if data.server.transport_protocol == 'udp':
                return
        sys.stdout.write(f'[连接] 服务器断开: {data.server.address}\n')


class TlsLogger:
    def tls_clienthello(self, data):
        sys.stdout.write(f'[TLS] ClientHello: {data.context.server.address}\n')
    
    def tls_established_client(self, data):
        sys.stdout.write(f'[TLS] 客户端TLS建立: {data.context.server.address}\n')
    
    def tls_established_server(self, data):
        sys.stdout.write(f'[TLS] 服务器TLS建立: {data.context.server.address}\n')
    
    def tls_failed_client(self, data):
        sys.stdout.write(f'[TLS错误] 客户端TLS失败: {data.context.server.address} - {data.context.error}\n')
    
    def tls_failed_server(self, data):
        sys.stdout.write(f'[TLS错误] 服务器TLS失败: {data.context.server.address} - {data.context.error}\n')


def run_proxy(source_image, target_process):
    from mitmproxy import options
    from mitmproxy.tools.dump import DumpMaster
    
    process_name = target_process.replace('.exe', '')
    
    pid = get_process_pid(target_process)
    if pid:
        sys.stdout.write(f'[进程] 找到 {target_process} (PID: {pid})\n')
    else:
        sys.stdout.write(f'[进程] 未找到运行中的 {target_process}，将监听进程名\n')
    
    sys.stdout.write('\n' + '='*60 + '\n')
    sys.stdout.write('  原神头像替换代理程序\n')
    sys.stdout.write('='*60 + '\n')
    sys.stdout.write(f'  源图片: {source_image}\n')
    sys.stdout.write(f'  目标进程: {target_process}\n')
    if pid:
        sys.stdout.write(f'  进程PID: {pid}\n')
    sys.stdout.write('='*60 + '\n')
    sys.stdout.write('\n')
    sys.stdout.write('[模式] 使用 mitmproxy 本地捕获模式\n')
    sys.stdout.write('[提示] 正在监听请求，请进行头像上传操作\n')
    sys.stdout.write('[提示] 按 Ctrl+C 退出程序\n')
    sys.stdout.write('\n')
    
    mode_spec = f'local:{process_name}'
    sys.stdout.write(f'[配置] 代理模式: {mode_spec}\n')
    
    opts = options.Options(
        mode=[mode_spec],
        ssl_insecure=True,
        showhost=True,
    )
    
    for handler in logging.root.handlers[:]:
        handler.addFilter(UdpLogFilter())
    
    for name in ['mitmproxy', 'mitmproxy.proxy', 'mitmproxy.proxy.mode_servers', 'mitmproxy.proxy.server']:
        logger = logging.getLogger(name)
        logger.addFilter(UdpLogFilter())
        for handler in logger.handlers:
            handler.addFilter(UdpLogFilter())
    
    proxy_env = ProxyEnvironment.get_instance()
    
    async def start_proxy():
        master = DumpMaster(opts, with_termlog=False)
        proxy_env.set_master(master)
        avatar_addon = AvatarReplacer(source_image)
        connection_logger = ConnectionLogger()
        tls_logger = TlsLogger()
        master.addons.add(avatar_addon)
        master.addons.add(connection_logger)
        master.addons.add(tls_logger)
        
        for handler in logging.root.handlers[:]:
            handler.addFilter(UdpLogFilter())
        
        sys.stdout.write('[代理] 代理服务已启动\n')
        try:
            await master.run()
        except KeyboardInterrupt:
            pass
        finally:
            proxy_env.cleanup()
    
    try:
        asyncio.run(start_proxy())
    except KeyboardInterrupt:
        proxy_env.cleanup()
    except SystemExit:
        proxy_env.cleanup()
    except Exception as e:
        sys.stdout.write(f'[错误] 代理运行异常: {e}\n')
        proxy_env.cleanup()
    finally:
        proxy_env.cleanup()


def check_dependencies():
    import sys
    missing = []
    try:
        import mitmproxy
        sys.stdout.write(f'[依赖] mitmproxy 版本: {mitmproxy.__version__ if hasattr(mitmproxy, "__version__") else "已安装"}\n')
    except ImportError:
        missing.append('mitmproxy>=10.2.0')
    try:
        from PIL import Image
    except ImportError:
        missing.append('Pillow')
    try:
        import psutil
    except ImportError:
        missing.append('psutil')
    
    try:
        import mitmproxy_rs
        sys.stdout.write('[依赖] mitmproxy_rs 已安装\n')
    except ImportError:
        sys.stdout.write('[警告] mitmproxy_rs 未安装，本地捕获可能不可用\n')
    
    try:
        import mitmproxy_windows
        sys.stdout.write('[依赖] mitmproxy_windows 已安装\n')
    except ImportError:
        sys.stdout.write('[警告] mitmproxy_windows 未安装，Windows本地捕获可能不可用\n')
    
    if missing:
        sys.stdout.write('[错误] 缺少依赖:\n')
        for dep in missing:
            sys.stdout.write(f'  - {dep}\n')
        sys.stdout.write(f'\n请运行: pip install {" ".join(missing)}\n')
        return False
    return True


def main():
    sys.stdout.write('\n' + '='*60 + '\n')
    sys.stdout.write('  原神头像替换代理程序\n')
    sys.stdout.write('='*60 + '\n\n')
    
    if not is_admin():
        sys.stdout.write('[权限] 需要管理员权限，正在请求提升...\n')
        if run_as_admin():
            sys.exit(0)
        else:
            sys.stdout.write('[错误] 无法获取管理员权限\n')
            input('\n按回车键退出...')
            sys.exit(1)
    
    sys.stdout.write('[权限] 已获取管理员权限\n')
    
    proxy_env = ProxyEnvironment.get_instance()
    proxy_env.initialize()
    
    if not check_dependencies():
        input('\n按回车键退出...')
        sys.exit(1)
    
    sys.stdout.write('[依赖] 所有依赖已安装\n')
    
    if not install_cert_auto():
        print('[错误] 证书安装失败，无法继续')
        input('\n按回车键退出...')
        sys.exit(1)
    
    if not verify_cert_installation():
        print('[错误] 证书验证失败，HTTPS 拦截将无法正常工作')
        input('\n按回车键退出...')
        sys.exit(1)
    
    print('[证书] 证书安装和验证通过')
    
    desktop = get_desktop_path()
    print(f'\n[提示] 头像文件应放置在: {desktop}')
    
    avatar_filename = input('请输入头像文件名 (如 tx.png): ').strip()
    if not avatar_filename:
        print('[错误] 未输入文件名')
        input('\n按回车键退出...')
        sys.exit(1)
    
    source_image = desktop / avatar_filename
    if not source_image.exists():
        print(f'[错误] 文件不存在: {source_image}')
        input('\n按回车键退出...')
        sys.exit(1)
    
    target_process = select_process(default='YuanShen.exe')
    print(f'\n[配置] 目标进程: {target_process}')
    
    run_proxy(str(source_image), target_process)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    proxy_env = None
    try:
        proxy_env = ProxyEnvironment.get_instance()
        main()
    except KeyboardInterrupt:
        print('\n[系统] 用户中断程序')
        if proxy_env:
            proxy_env.cleanup()
    except SystemExit:
        if proxy_env:
            proxy_env.cleanup()
    except Exception as e:
        print(f'\n[严重错误] 程序异常: {e}')
        if proxy_env:
            proxy_env.cleanup()
        input('\n按回车键退出...')
    finally:
        if proxy_env:
            proxy_env.cleanup()

