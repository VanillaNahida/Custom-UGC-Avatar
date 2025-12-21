import { ipcMain as g, dialog as p, app as t, BrowserWindow as b, Menu as s, shell as c } from "electron";
import { fileURLToPath as h } from "node:url";
import o from "node:path";
import w from "node:fs";
const i = o.dirname(h(import.meta.url));
let e;
function m() {
  e = new b({
    width: 1108,
    height: 900,
    title: "千星头像编辑器",
    // 设置窗口标题
    webPreferences: {
      preload: o.join(i, "preload.js"),
      contextIsolation: !0,
      nodeIntegration: !1
    }
  }), process.env.VITE_DEV_SERVER_URL ? (e.loadURL(process.env.VITE_DEV_SERVER_URL), e.webContents.openDevTools()) : e.loadFile(o.join(i, "../dist/index.html"));
}
g.handle("save-image", async (n, a, r) => {
  try {
    const { filePath: l, canceled: u } = await p.showSaveDialog(e, {
      title: "保存图片",
      defaultPath: r || "cropped_image.png",
      filters: [
        { name: "PNG 图片", extensions: ["png"] },
        { name: "所有文件", extensions: ["*"] }
      ]
    });
    if (u || !l)
      return { success: !1, message: "保存已取消" };
    const f = a.replace(/^data:image\/png;base64,/, ""), C = Buffer.from(f, "base64");
    return w.writeFileSync(l, C), { success: !0, filePath: l, message: "图片保存成功" };
  } catch (l) {
    return console.error("保存图片失败:", l), { success: !1, message: `保存失败: ${l.message}` };
  }
});
const d = () => {
  const n = [
    {
      label: "文件",
      submenu: [
        {
          label: "退出",
          accelerator: "CmdOrCtrl+Q",
          click: () => t.quit()
        }
      ]
    },
    {
      label: "编辑",
      submenu: [
        {
          label: "撤销",
          accelerator: "CmdOrCtrl+Z",
          role: "undo"
        },
        {
          label: "重做",
          accelerator: "Shift+CmdOrCtrl+Z",
          role: "redo"
        },
        {
          type: "separator"
        },
        {
          label: "剪切",
          accelerator: "CmdOrCtrl+X",
          role: "cut"
        },
        {
          label: "复制",
          accelerator: "CmdOrCtrl+C",
          role: "copy"
        },
        {
          label: "粘贴",
          accelerator: "CmdOrCtrl+V",
          role: "paste"
        },
        {
          label: "删除",
          role: "delete"
        },
        {
          type: "separator"
        },
        {
          label: "全选",
          accelerator: "CmdOrCtrl+A",
          role: "selectAll"
        }
      ]
    },
    {
      label: "视图",
      submenu: [
        {
          label: "重新加载",
          accelerator: "CmdOrCtrl+R",
          click: () => e?.reload()
        },
        {
          label: "打开开发者工具",
          accelerator: "Ctrl+Shift+I",
          click: () => e?.webContents.toggleDevTools()
        },
        {
          type: "separator"
        },
        {
          label: "全屏",
          role: "togglefullscreen"
        }
      ]
    },
    {
      label: "窗口",
      submenu: [
        {
          label: "最小化",
          accelerator: "CmdOrCtrl+M",
          role: "minimize"
        },
        {
          label: "关闭",
          accelerator: "CmdOrCtrl+W",
          role: "close"
        }
      ]
    },
    {
      label: "帮助",
      submenu: [
        {
          label: "关于",
          click: () => {
            p.showMessageBox(e, {
              title: "关于 Avatar Editor",
              message: "Avatar Editor v1.0.0",
              detail: `一个简单的千星头像编辑工具，使用Electron框架开发。
开发者 @香草味的纳西妲喵
主页地址：https://space.bilibili.com/1347891621`,
              type: "info",
              buttons: ["打开作者主页", "确定"],
              defaultId: 1,
              cancelId: 1
            }).then((r) => {
              r.response === 0 && c.openExternal("https://space.bilibili.com/1347891621");
            });
          }
        },
        {
          label: "打开作者主页",
          click: () => {
            c.openExternal("https://space.bilibili.com/1347891621");
          }
        }
      ]
    }
  ], a = s.buildFromTemplate(n);
  s.setApplicationMenu(a);
};
t.whenReady().then(() => {
  m(), d(), t.on("activate", function() {
    b.getAllWindows().length === 0 && (m(), d());
  });
});
t.on("window-all-closed", function() {
  process.platform !== "darwin" && t.quit();
});
