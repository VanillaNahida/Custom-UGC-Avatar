// preload.js
import { contextBridge, ipcRenderer } from 'electron'

// 暴露API给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 保存图片功能
  saveImage: (dataUrl, fileName) => {
    return ipcRenderer.invoke('save-image', dataUrl, fileName)
  }
})
