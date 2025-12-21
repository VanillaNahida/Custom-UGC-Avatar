import { app, BrowserWindow, dialog, ipcMain, Menu } from 'electron'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import fs from 'node:fs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// 保持窗口对象的全局引用，避免被垃圾回收
let mainWindow

function createWindow () {
  // 创建浏览器窗口
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  // 加载应用的index.html
  if (process.env.VITE_DEV_SERVER_URL) {
    // 开发环境下加载Vite服务器
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL)
    // 开发环境下打开开发者工具
    mainWindow.webContents.openDevTools()
  } else {
    // 生产环境下加载本地文件
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
  }
}

// 处理保存图片请求
ipcMain.handle('save-image', async (event, dataUrl, defaultFileName) => {
  try {
    // 显示保存对话框
    const { filePath, canceled } = await dialog.showSaveDialog(mainWindow, {
      title: '保存图片',
      defaultPath: defaultFileName || 'cropped_image.png',
      filters: [
        { name: 'PNG 图片', extensions: ['png'] },
        { name: '所有文件', extensions: ['*'] }
      ]
    })

    if (canceled || !filePath) {
      return { success: false, message: '保存已取消' }
    }

    // 将base64数据转换为二进制
    const base64Data = dataUrl.replace(/^data:image\/png;base64,/, '')
    const buffer = Buffer.from(base64Data, 'base64')

    // 写入文件
    fs.writeFileSync(filePath, buffer)

    return { success: true, filePath, message: '图片保存成功' }
  } catch (error) {
    console.error('保存图片失败:', error)
    return { success: false, message: `保存失败: ${error.message}` }
  }
})

// 创建中文菜单模板
const createMenu = () => {
  const template = [
    {
      label: '文件',
      submenu: [
        {
          label: '退出',
          accelerator: 'CmdOrCtrl+Q',
          click: () => app.quit()
        }
      ]
    },
    {
      label: '编辑',
      submenu: [
        {
          label: '撤销',
          accelerator: 'CmdOrCtrl+Z',
          role: 'undo'
        },
        {
          label: '重做',
          accelerator: 'Shift+CmdOrCtrl+Z',
          role: 'redo'
        },
        {
          type: 'separator'
        },
        {
          label: '剪切',
          accelerator: 'CmdOrCtrl+X',
          role: 'cut'
        },
        {
          label: '复制',
          accelerator: 'CmdOrCtrl+C',
          role: 'copy'
        },
        {
          label: '粘贴',
          accelerator: 'CmdOrCtrl+V',
          role: 'paste'
        },
        {
          label: '删除',
          role: 'delete'
        },
        {
          type: 'separator'
        },
        {
          label: '全选',
          accelerator: 'CmdOrCtrl+A',
          role: 'selectAll'
        }
      ]
    },
    {
      label: '视图',
      submenu: [
        {
          label: '重新加载',
          accelerator: 'CmdOrCtrl+R',
          click: () => mainWindow?.reload()
        },
        {
          label: '切换开发者工具',
          accelerator: process.platform === 'darwin' ? 'Alt+Command+I' : 'Ctrl+Shift+I',
          click: () => mainWindow?.webContents.toggleDevTools()
        },
        {
          type: 'separator'
        },
        {
          label: '全屏',
          role: 'togglefullscreen'
        }
      ]
    },
    {
      label: '窗口',
      submenu: [
        {
          label: '最小化',
          accelerator: 'CmdOrCtrl+M',
          role: 'minimize'
        },
        {
          label: '关闭',
          accelerator: 'CmdOrCtrl+W',
          role: 'close'
        }
      ]
    },
    {
      label: '帮助',
      submenu: [
        {
          label: '关于',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              title: '关于 Avatar Editor',
              message: 'Avatar Editor v0.0.0',
              detail: '一个简单的头像编辑工具',
              type: 'info'
            })
          }
        }
      ]
    }
  ]

  const menu = Menu.buildFromTemplate(template)
  Menu.setApplicationMenu(menu)
}

// Electron初始化完成后创建窗口
app.whenReady().then(() => {
  createWindow()
  createMenu()

  // macOS下，点击dock图标时重新创建窗口
  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
      createMenu()
    }
  })
})

// 关闭所有窗口时退出应用（Windows和Linux）
app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit()
})
