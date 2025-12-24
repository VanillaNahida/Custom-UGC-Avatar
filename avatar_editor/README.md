# Avatar Editor - 头像编辑器

一个基于 Vue 3 + Vite + Electron 开发的桌面头像编辑工具，支持图片裁剪、缩放和预览功能。

## 项目特性

- 🖼️ **图片裁剪**: 支持自定义尺寸的方形裁剪
- 🔍 **缩放控制**: 实时缩放图片以精确调整裁剪区域
- 💾 **保存功能**: 支持保存裁剪后的图片
- 🖥️ **桌面应用**: 基于 Electron 的跨平台桌面应用
- 🎨 **现代化UI**: 美观的渐变设计和响应式布局

## 技术栈

- **前端框架**: Vue 3
- **构建工具**: Vite
- **桌面应用**: Electron
- **图片裁剪**: vue-cropper
- **样式**: CSS3 (渐变、动画)

## 项目结构

```
avatar_editor/
├── electron/           # Electron 主进程文件
│   ├── main.js        # 主进程入口
│   └── preload.js     # 预加载脚本
├── src/               # 前端源码
│   ├── App.vue        # 主应用组件
│   ├── main.js        # Vue 应用入口
│   └── style.css      # 全局样式
├── dist-electron/     # Electron 构建输出
├── package.json       # 项目配置和依赖
├── vite.config.js     # Vite 配置
└── favicon.ico          # 应用图标
```

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式

启动开发服务器：

```bash
npm run dev
```

启动 Electron 开发模式：

```bash
npm run dev:electron
```

### 构建应用

构建桌面应用：

```bash
# 构建所有平台
npm run build:electron

# 仅构建 Windows 版本
npm run build:win
```

## 使用说明

1. **选择图片**: 点击"选择图片"按钮上传本地图片
2. **调整裁剪**: 使用缩放滑块调整图片大小，拖动选择裁剪区域
3. **设置尺寸**: 调整裁剪框的尺寸（100px - 500px）
4. **预览效果**: 右侧实时预览裁剪后的效果
5. **保存图片**: 点击"保存图片"按钮保存裁剪结果

## 功能特性

### 图片裁剪
- 支持方形裁剪（1:1 比例）
- 可自定义裁剪尺寸
- 实时预览裁剪效果

### 缩放控制
- 缩放范围：10% - 300%
- 平滑的缩放动画
- 精确的缩放控制

### 界面设计
- 现代化的渐变背景
- 响应式布局设计
- 直观的操作界面

## 开发说明

### 主要组件

- **App.vue**: 主应用组件，包含所有编辑功能
- **vue-cropper**: 图片裁剪组件
- **Electron API**: 提供原生文件保存功能

### 自定义配置

在 `package.json` 中可以修改应用配置：

- `appId`: 应用标识符
- `productName`: 应用名称
- `icon`: 应用图标路径

## 许可证

GPL-3.0 license

## 作者

@香草味的纳西妲喵 <https://space.bilibili.com/1347891621>