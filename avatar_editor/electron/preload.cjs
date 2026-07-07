const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  saveImage: (dataUrl, fileName) => {
    return ipcRenderer.invoke('save-image', dataUrl, fileName)
  },

  saveToPluginPath: (dataUrl, filePath) => {
    return ipcRenderer.invoke('save-to-plugin-path', dataUrl, filePath)
  },

  getPluginPath: () => {
    return ipcRenderer.invoke('get-plugin-path')
  },

  savePluginPath: (pluginPath) => {
    return ipcRenderer.invoke('save-plugin-path', pluginPath)
  },
})