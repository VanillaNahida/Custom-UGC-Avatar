<script setup>
import { ref, onMounted } from 'vue'

const imageUrl = ref('')
const cropSize = ref(300)
const scale = ref(1)
const previewUrl = ref('')
const cropper = ref(null)
const isImageLoaded = ref(false)
const fileInput = ref(null)

const showHelp = ref(false)

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
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      imageUrl.value = e.target.result
      isImageLoaded.value = true
      setTimeout(() => {
        updatePreview()
      }, 100)
    }
    reader.readAsDataURL(file)
  }
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
  if (previewUrl.value) {
    try {
      const hash = await generateImageHash(previewUrl.value)
      const fileName = `${hash}.png`

      if (typeof window !== 'undefined' && window.electronAPI && typeof window.electronAPI.saveImage === 'function') {
        const result = await window.electronAPI.saveImage(previewUrl.value, fileName)
        if (result.success) {
          console.log('图片保存成功:', result.filePath)
        } else {
          console.log('图片保存取消或失败:', result.message)
        }
      } else {
        const link = document.createElement('a')
        link.href = previewUrl.value
        link.download = fileName
        link.click()
      }
    } catch (error) {
      console.error('保存图片失败:', error)
    }
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
  if (files && files.length > 0) {
    const file = files[0]
    if (file.type.startsWith('image/')) {
      const reader = new FileReader()
      reader.onload = (e) => {
        imageUrl.value = e.target.result
        isImageLoaded.value = true
        setTimeout(() => {
          updatePreview()
        }, 100)
      }
      reader.readAsDataURL(file)
    }
  }
}

const clearCanvas = () => {
  imageUrl.value = ''
  previewUrl.value = ''
  isImageLoaded.value = false
  scale.value = 1
}

const handlePaste = async (e) => {
  const items = e.clipboardData?.items
  if (items) {
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        const file = item.getAsFile()
        if (file) {
          const reader = new FileReader()
          reader.onload = (e) => {
            imageUrl.value = e.target.result
            isImageLoaded.value = true
            setTimeout(() => {
              updatePreview()
            }, 100)
          }
          reader.readAsDataURL(file)
          break
        }
      }
    }
  }
}

onMounted(() => {
  imageUrl.value = ''
  window.addEventListener('paste', handlePaste)
})
</script>

<template>
  <div class="avatar-editor">
    <h1 class="title">头像编辑器</h1>

    <div class="toolbar">
      <div class="file-input-wrapper">
        <button class="btn btn-primary" @click="triggerFileInput">选择图片</button>
        <input 
          ref="fileInput" 
          type="file" 
          accept="image/*" 
          class="file-input" 
          @change="handleFileChange"
        />
      </div>
      <button class="btn btn-success" @click="saveImage">保存图片</button>
      <button class="btn btn-danger" @click="clearCanvas">清空画布</button>
      <button class="btn btn-help" @click="showHelp = true">帮助</button>
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
          <button class="btn btn-secondary" @click="updatePreview">更新预览</button>
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
    
    <div v-if="isImageLoaded" class="status-bar">
      <p>图片已加载，可以开始编辑</p>
    </div>

    <!-- 帮助弹窗 -->
    <div v-if="showHelp" class="modal-overlay" @click="showHelp = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>如何使用</h2>
          <button class="modal-close" @click="showHelp = false">×</button>
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
  </div>
</template>

<style scoped>
.avatar-editor {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Blueaka', 'Arial', sans-serif;
  background: linear-gradient(90deg, #56ab2f 0%, #a8e063 100%);
  min-height: 100vh;
  color: #333;
}

.title {
  text-align: center;
  color: white;
  font-size: 28px;
  margin-bottom: 20px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
  font-family: 'Blueaka_Bold', "Blueaka", 'Arial', sans-serif;
  font-weight: 700;
}

.toolbar {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 30px;
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
  pointer-events: none; /* 添加这行，防止误触 */
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  position: relative; /* 确保按钮层级高于输入框 */
  z-index: 1; /* 确保按钮层级高于输入框 */
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}

.btn-primary {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.btn-success {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: white;
}

.btn-secondary {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  color: white;
  width: 100%;
  margin-bottom: 10px;
}

.btn-help {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-danger {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
  color: white;
}

.editor-container {
  display: flex;
  gap: 30px;
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  flex-wrap: wrap;
  justify-content: center;
}

.crop-area {
  flex: 1;
  min-width: 300px;
  max-width: 600px;
  height: 500px;
  background: #f5f5f5;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: #999;
  font-size: 18px;
}

.placeholder p {
  margin: 5px 0;
}

.drop-hint {
  font-size: 14px;
  color: #56ab2f;
  font-weight: 500;
}

.control-panel {
  width: 300px;
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.1);
}

.control-section {
  margin-bottom: 25px;
}

.control-section h3 {
  margin-bottom: 15px;
  color: #495057;
  font-size: 16px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.size-info {
  margin-bottom: 10px;
  font-size: 14px;
  color: #6c757d;
  font-weight: 500;
}

.slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: linear-gradient(to right, #56ab2f 0%, #a8e063 100%);
  outline: none;
  appearance: none;
  margin-bottom: 15px;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: white;
  border: 3px solid #56ab2f;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

.slider::-webkit-slider-thumb:hover {
  transform: scale(1.2);
  border-color: #a8e063;
}

.slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: white;
  border: 3px solid #56ab2f;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

.slider::-moz-range-thumb:hover {
  transform: scale(1.2);
  border-color: #a8e063;
}

.preview-area {
  width: 100%;
  height: 200px;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  border: 2px dashed #dee2e6;
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
  color: #999;
  font-size: 14px;
}

.status-bar {
  text-align: center;
  margin-top: 20px;
  color: white;
  font-size: 14px;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .editor-container {
    flex-direction: column;
  }
  
  .control-panel {
    width: 100%;
  }
  
  .crop-area {
    height: 400px;
  }
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 16px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  animation: modalFadeIn 0.3s ease;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
}

.modal-header h2 {
  margin: 0;
  color: #333;
  font-size: 22px;
}

.modal-close {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: #999;
  transition: color 0.2s ease;
  padding: 0;
  width: 36px;
  height: 36px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 50%;
}

.modal-close:hover {
  color: #333;
  background: #f5f5f5;
}

.modal-body {
  padding: 24px;
}

.help-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.help-list li {
  padding: 12px 0;
  padding-left: 30px;
  position: relative;
  color: #555;
  font-size: 15px;
  line-height: 1.6;
  border-bottom: 1px solid #f0f0f0;
}

.help-list li:last-child {
  border-bottom: none;
}

.help-list li::before {
  position: absolute;
  left: 0;
  color: #56ab2f;
  font-weight: bold;
  font-size: 16px;
}
</style>




