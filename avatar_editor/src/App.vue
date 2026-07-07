<script setup>
import { ref, onMounted } from 'vue'
import ToastContainer from './components/ToastContainer.vue'
import { useToast } from './composables/useToast.js'

const { success, error, info, warning } = useToast()

const imageUrl = ref('')
const cropSize = ref(300)
const scale = ref(1)
const previewUrl = ref('')
const cropper = ref(null)
const isImageLoaded = ref(false)
const fileInput = ref(null)

const showHelp = ref(false)
const pluginPath = ref('')

const generateImageHash = async (dataUrl) => {
  try {
    const binaryString = atob(dataUrl.replace(/^data:image\/\w+;base64,/, ''))
    const bytes = new Uint8Array(binaryString.length)
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i)
    }
    const hashBuffer = await crypto.subtle.digest('SHA-256', bytes)
    const hashArray = Array.from(new Uint8Array(hashBuffer))
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
    return hashHex.substring(0, 16)
  } catch (error) {
    console.error('计算哈希失败:', error)
    return Date.now().toString(16)
  }
}

// 触发文件选择
const triggerFileInput = () => {
  if (fileInput.value) {
    fileInput.value.click()
  }
}

// 选择图片
const handleFileChange = (e) => {
  const file = e.target.files[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    warning('请选择图片文件')
    return
  }
  const reader = new FileReader()
  reader.onload = (e) => {
    imageUrl.value = e.target.result
    isImageLoaded.value = true
    info('图片已加载，可以开始编辑')
    setTimeout(() => {
      updatePreview()
    }, 100)
  }
  reader.readAsDataURL(file)
}

// 更新预览
const updatePreview = () => {
  if (cropper.value) {
    try {
      // 尝试使用不同的方法获取裁剪数据
      if (typeof cropper.value.getCropData === 'function') {
        cropper.value.getCropData((data) => {
          previewUrl.value = data
        })
      } else if (typeof cropper.value.getCroppedCanvas === 'function') {
        // 兼容其他图片裁剪库的API
        const canvas = cropper.value.getCroppedCanvas()
        previewUrl.value = canvas.toDataURL('image/png')
      }
    } catch (error) {
      console.error('获取裁剪数据失败:', error)
    }
  }
}

// 保存图片
const saveImage = async () => {
  if (!previewUrl.value) {
    warning('请先加载图片')
    return
  }
  try {
    const hash = await generateImageHash(previewUrl.value)
    const fileName = `${hash}.png`

    if (window.electronAPI && typeof window.electronAPI.saveImage === 'function') {
      const result = await window.electronAPI.saveImage(previewUrl.value, fileName)
      if (result.success) {
        success('图片保存成功')
      } else {
        if (result.message !== '保存已取消') {
          error('保存失败: ' + result.message)
        }
      }
    } else {
      const link = document.createElement('a')
      link.href = previewUrl.value
      link.download = fileName
      link.click()
      success('图片保存成功')
    }
  } catch (err) {
    error('保存图片失败: ' + err.message)
  }
}

// 监听裁剪尺寸变化
const handleCropSizeChange = (value) => {
  cropSize.value = value
}

const handleDragOver = (e) => {
  e.preventDefault()
}

const handleDrop = (e) => {
  e.preventDefault()
  const files = e.dataTransfer.files
  if (!files || files.length === 0) return
  const file = files[0]
  if (!file.type.startsWith('image/')) {
    warning('请拖入图片文件')
    return
  }
  const reader = new FileReader()
  reader.onload = (e) => {
    imageUrl.value = e.target.result
    isImageLoaded.value = true
    info('图片已加载，可以开始编辑')
    setTimeout(() => {
      updatePreview()
    }, 100)
  }
  reader.readAsDataURL(file)
}

const clearCanvas = () => {
  imageUrl.value = ''
  previewUrl.value = ''
  isImageLoaded.value = false
  scale.value = 1
}

const handlePaste = async (e) => {
  const items = e.clipboardData?.items
  if (!items) return
  let pasted = false
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      const file = item.getAsFile()
      if (file) {
        const reader = new FileReader()
        reader.onload = (e) => {
          imageUrl.value = e.target.result
          isImageLoaded.value = true
          info('图片已加载，可以开始编辑')
          setTimeout(() => {
            updatePreview()
          }, 100)
        }
        reader.readAsDataURL(file)
        pasted = true
        break
      }
    }
  }
  if (!pasted) {
    warning('剪贴板中没有图片')
  }
}

// 保存插件路径设置
const savePluginPathSetting = async () => {
  if (!pluginPath.value.trim()) {
    warning('请输入插件目录路径')
    return
  }
  if (!window.electronAPI || typeof window.electronAPI.savePluginPath !== 'function') {
    error('当前环境不支持此功能，请在 Electron 中运行')
    return
  }
  const result = await window.electronAPI.savePluginPath(pluginPath.value)
  if (result.success) {
    success('路径配置已保存')
  } else {
    error('保存配置失败: ' + result.message)
  }
}

// 输出到插件目录
const exportToPlugin = async () => {
  if (!previewUrl.value) {
    warning('请先加载并裁剪图片')
    return
  }
  if (!pluginPath.value.trim()) {
    warning('请先配置插件目录路径')
    return
  }
  if (!window.electronAPI || typeof window.electronAPI.saveToPluginPath !== 'function') {
    error('当前环境不支持此功能，请在 Electron 中运行')
    return
  }
  const result = await window.electronAPI.saveToPluginPath(previewUrl.value, pluginPath.value)
  if (result.success) {
    success('已输出到插件目录')
  } else {
    error('输出失败: ' + result.message)
  }
}

onMounted(async () => {
  imageUrl.value = ''
  window.addEventListener('paste', handlePaste)

  if (window.electronAPI && typeof window.electronAPI.getPluginPath === 'function') {
    const savedPath = await window.electronAPI.getPluginPath()
    if (savedPath) {
      pluginPath.value = savedPath
    }
  }
})
</script>

<template>
  <div class="avatar-editor">
    <h1 class="title">头像编辑器</h1>

    <div class="toolbar">
      <div class="file-input-wrapper">
        <button class="btn btn-primary" @click="triggerFileInput">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16"><path d="M2 4.5A1.5 1.5 0 013.5 3h2.8l1.2 1.5h4A1.5 1.5 0 0113 6v5.5A1.5 1.5 0 0111.5 13h-8A1.5 1.5 0 012 11.5V4.5z" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/><path d="M8 7.5v4M6 9.5h4" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
          选择图片
        </button>
        <input 
          ref="fileInput" 
          type="file" 
          accept="image/*" 
          class="file-input" 
          @change="handleFileChange"
        />
      </div>
      <button class="btn btn-success" @click="saveImage">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16"><path d="M3 13.5V3a1 1 0 011-1h5l4 4v7.5a1 1 0 01-1 1H4a1 1 0 01-1-1z" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/><path d="M6 13.5V9h4v4.5" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/><path d="M9 2v3.5h3" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/></svg>
        保存图片
      </button>
      <button class="btn btn-danger" @click="clearCanvas">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16"><path d="M2.5 4.5h11M5.5 4.5V3a1 1 0 011-1h3a1 1 0 011 1v1.5M6.5 7.5v5M9.5 7.5v5" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/><path d="M3.5 4.5l1 9a1 1 0 001 1h5a1 1 0 001-1l1-9" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/></svg>
        清空画布
      </button>
      <button class="btn btn-help" @click="showHelp = true">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16"><circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M6.5 6.5A1.5 1.5 0 018 5a1.5 1.5 0 011.5 1.5c0 1-1.5 1.5-1.5 2.5M8 12v.5" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
        帮助
      </button>
    </div>

    <div class="plugin-config">
      <div class="plugin-path-row">
        <label class="plugin-label">插件目录路径:</label>
        <input 
          v-model="pluginPath" 
          type="text" 
          class="plugin-path-input" 
          placeholder="例如: D:\Example\Plugins\image.png"
        />
        <button class="btn btn-small btn-save" @click="savePluginPathSetting">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="14" height="14"><path d="M3 9l3 3 7-7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              保存路径
            </button>
      </div>
      <div class="plugin-actions">
        <button class="btn btn-export" :disabled="!previewUrl" @click="exportToPlugin">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="14" height="14"><path d="M8 1.5v9M4.5 6.5L8 10l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M2.5 12.5v1a1 1 0 001 1h9a1 1 0 001-1v-1" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
            输出到插件目录
          </button>
      </div>
    </div>
    
    <div class="editor-container">
      <div class="crop-area" @dragover="handleDragOver" @drop="handleDrop">
        <vue-cropper
          ref="cropper"
          v-if="imageUrl"
          :img="imageUrl"
          :outputSize="1"
          :outputType="'png'"
          :info="true"
          :full="true"
          :autoCrop="true"
          :autoCropWidth="cropSize"
          :autoCropHeight="cropSize"
          :fixed="true"
          :fixedNumber="[1, 1]"
          :centerBox="true"
          :high="true"
          :infoTrue="true"
          :maxImgSize="2000"
          :enlarge="10"
          :scale="scale"
          @realTime="updatePreview"
        />
        <div v-else class="placeholder">
          <p>点击上方按钮选择图片</p>
          <p class="drop-hint">或直接拖拽图片到此处（支持Ctrl+V粘贴图片上传）</p>
        </div>
      </div>
      
      <div class="control-panel">
        <div class="control-section">
          <h3>裁剪尺寸</h3>
          <div class="size-info">
            <span>裁剪大小: {{ cropSize }}px</span>
          </div>
          <input 
            type="range" 
            min="100" 
            max="500" 
            step="10" 
            v-model.number="cropSize"
            @input="handleCropSizeChange(cropSize)"
            class="slider"
          />
        </div>
        
        <div class="control-section">
          <h3>操作</h3>
          <button class="btn btn-secondary" @click="updatePreview">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="14" height="14"><path d="M1.5 8A6.5 6.5 0 018 1.5 6.5 6.5 0 0114.5 8 6.5 6.5 0 018 14.5" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><path d="M1.5 8h3.2l2-4 2.6 8 2-4H14.5" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
            更新预览
          </button>
        </div>
        
        <div class="control-section">
          <h3>裁剪预览</h3>
          <div class="preview-area">
            <img v-if="previewUrl" :src="previewUrl" alt="预览" class="preview-img" />
            <div v-else class="preview-placeholder">
              <p>暂无预览</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 帮助弹窗 -->
    <div v-if="showHelp" class="modal-overlay" @click="showHelp = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>如何使用</h2>
          <button class="modal-close" @click="showHelp = false">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" width="20" height="20">
                <path d="M5.5 5.5l9 9m0-9l-9 9" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
        </div>
        <div class="modal-body">
          <ul class="help-list">
            <li>拖动裁剪框裁剪你想要的图片</li>
            <li>裁剪框蓝色小点鼠标按住拖放可缩放裁剪框</li>
            <li>鼠标滚轮对图片画布进行缩放</li>
            <li>阴影部分左键按住可移动图片画布</li>
          </ul>
        </div>
      </div>
    </div>

    <ToastContainer />
  </div>
</template>

<style scoped>
.avatar-editor {
  max-width: 1280px;
  margin: 0 auto;
  padding: 32px;
  min-height: 100vh;
}

.title {
  text-align: center;
  color: var(--text-primary);
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 32px;
  font-family: 'Blueaka_Bold', 'Blueaka', sans-serif;
  letter-spacing: 0.02em;
}

/* ---- Toolbar ---- */
.toolbar {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.file-input-wrapper {
  position: relative;
  display: inline-block;
}

.file-input {
  position: absolute;
  opacity: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
  pointer-events: none;
}

/* ---- Button System ---- */
.btn {
  padding: 10px 20px;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 150ms var(--ease-out),
              box-shadow 150ms var(--ease-out),
              background 200ms var(--ease-out);
  box-shadow: var(--shadow-sm);
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn:active {
  transform: translateY(0);
}

.btn:focus-visible {
  outline: 2px solid var(--border-focus);
  outline-offset: 2px;
}

.btn-primary {
  background: var(--accent);
  color: var(--bg-primary);
}

.btn-primary:hover {
  background: var(--accent-hover);
}

.btn-success {
  background: var(--accent);
  color: var(--bg-primary);
}

.btn-success:hover {
  background: var(--accent-hover);
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  width: 100%;
  margin-bottom: 8px;
  box-shadow: none;
}

.btn-secondary:hover {
  background: oklch(0.28 0.01 260);
}

.btn-help {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.btn-help:hover {
  background: oklch(0.28 0.01 260);
  color: var(--text-primary);
}

.btn-danger {
  background: var(--danger);
  color: var(--text-primary);
}

.btn-danger:hover {
  background: var(--danger-hover);
}

.btn-small {
  padding: 8px 16px;
  font-size: 13px;
}

.btn-save {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-save:hover {
  background: oklch(0.28 0.01 260);
}

.btn-export {
  background: var(--accent);
  color: var(--bg-primary);
  padding: 10px 20px;
  font-size: 14px;
}

.btn-export:hover {
  background: var(--accent-hover);
}

.btn-export:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* ---- Plugin Config ---- */
.plugin-config {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 16px;
  margin-bottom: 24px;
}

.plugin-path-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.plugin-label {
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 13px;
  white-space: nowrap;
}

.plugin-path-input {
  flex: 1;
  min-width: 240px;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
  color: var(--text-primary);
  background: var(--bg-secondary);
  transition: border-color 200ms var(--ease-out),
              box-shadow 200ms var(--ease-out);
}

.plugin-path-input:focus {
  outline: none;
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px var(--accent-subtle);
}

.plugin-path-input::placeholder {
  color: var(--text-muted);
  font-size: 12px;
}

.plugin-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 12px;
}

/* ---- Editor Container ---- */
.editor-container {
  display: flex;
  gap: 24px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-md);
  flex-wrap: wrap;
  justify-content: center;
}

.crop-area {
  flex: 1;
  min-width: 300px;
  max-width: 600px;
  height: 500px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  overflow: hidden;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
}

.placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: var(--text-muted);
  font-size: 16px;
  gap: 8px;
}

.placeholder p {
  margin: 0;
}

.drop-hint {
  font-size: 13px;
  color: var(--accent);
}

/* ---- Control Panel ---- */
.control-panel {
  width: 280px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: 20px;
  border: 1px solid var(--border);
}

.control-section {
  margin-bottom: 24px;
}

.control-section:last-child {
  margin-bottom: 0;
}

.control-section h3 {
  margin-bottom: 12px;
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.size-info {
  margin-bottom: 8px;
  font-size: 13px;
  color: var(--text-muted);
}

.slider {
  width: 100%;
  height: 4px;
  border-radius: 2px;
  background: var(--bg-tertiary);
  outline: none;
  appearance: none;
  margin-bottom: 8px;
  cursor: pointer;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--accent);
  border: none;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: transform 150ms var(--ease-out);
}

.slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}

.slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--accent);
  border: none;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: transform 150ms var(--ease-out);
}

.slider::-moz-range-thumb:hover {
  transform: scale(1.15);
}

.preview-area {
  width: 100%;
  height: 180px;
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.preview-placeholder {
  color: var(--text-muted);
  font-size: 13px;
}

/* ---- Modal ---- */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  animation: overlayIn 200ms var(--ease-out);
}

@keyframes overlayIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 440px;
  box-shadow: var(--shadow-lg);
  animation: modalIn 300ms var(--ease-out);
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: translateY(-16px) scale(0.97);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 16px;
}

.modal-header h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: 18px;
  font-family: 'Blueaka_Bold', 'Blueaka', sans-serif;
}

.modal-close {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  transition: color 150ms var(--ease-out),
              background 150ms var(--ease-out);
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: var(--radius-sm);
}

.modal-close:hover {
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

.modal-body {
  padding: 0 24px 24px;
}

.help-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.help-list li {
  padding: 12px 0 12px 28px;
  position: relative;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
  border-bottom: 1px solid var(--border);
}

.help-list li:last-child {
  border-bottom: none;
}

.help-list li::before {
  content: '';
  position: absolute;
  left: 4px;
  top: 18px;
  width: 8px;
  height: 8px;
  border-radius: 2px;
  background: var(--accent);
  transform: rotate(45deg);
}

/* ---- Responsive ---- */
@media (max-width: 768px) {
  .avatar-editor {
    padding: 16px;
  }

  .editor-container {
    flex-direction: column;
    padding: 16px;
    gap: 16px;
  }

  .control-panel {
    width: 100%;
  }

  .crop-area {
    height: 360px;
    min-width: unset;
    max-width: unset;
  }

  .plugin-path-row {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>




