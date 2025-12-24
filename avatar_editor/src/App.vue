<script setup>
import { ref, onMounted } from 'vue'

const imageUrl = ref('')
const cropSize = ref(300)
const scale = ref(1)
const previewUrl = ref('')
const cropper = ref(null)
const isImageLoaded = ref(false)
const fileInput = ref(null)

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
      // 检查是否在Electron环境中
      if (typeof window !== 'undefined' && window.electronAPI && typeof window.electronAPI.saveImage === 'function') {
        // 使用Electron原生保存功能
        const result = await window.electronAPI.saveImage(previewUrl.value, 'cropped_image.png')
        if (result.success) {
          console.log('图片保存成功:', result.filePath)
        } else {
          console.log('图片保存取消或失败:', result.message)
        }
      } else {
        // 开发环境下的回退方案
        const link = document.createElement('a')
        link.href = previewUrl.value
        link.download = 'cropped_image.png'
        link.click()
      }
    } catch (error) {
      console.error('保存图片失败:', error)
    }
  }
}

// 重置位置
const resetPosition = () => {
  if (cropper.value) {
    // 重新初始化缩放
    scale.value = 1
  }
}

// 监听缩放变化
const handleScaleChange = (value) => {
  scale.value = value
  // 通过props :scale="scale"自动更新，不需要手动调用方法
}

// 监听裁剪尺寸变化
const handleCropSizeChange = (value) => {
  cropSize.value = value
}

onMounted(() => {
  // 初始化时可以加载一个默认图片作为示例
  imageUrl.value = ''
})
</script>

<template>
  <div class="avatar-editor">
    <h1 class="title">千星头像编辑器</h1>
    
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
    </div>
    
    <div class="editor-container">
      <div class="crop-area">
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
          <p>请选择图片开始编辑</p>
        </div>
      </div>
      
      <div class="control-panel">
        <div class="control-section">
          <h3>缩放控制</h3>
          <div class="scale-info">
            <span>缩放比例: {{ Math.round(scale * 100) }}%</span>
          </div>
          <input 
            type="range" 
            min="0.1" 
            max="3" 
            step="0.01" 
            v-model.number="scale"
            @input="handleScaleChange(scale)"
            class="slider"
          />
        </div>
        
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
          <button class="btn btn-secondary" @click="resetPosition">重置位置</button>
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
  </div>
</template>

<style scoped>
.avatar-editor {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Arial', sans-serif;
  background: linear-gradient(90deg, #56ab2f 0%, #a8e063 100%);
  min-height: 100vh;
  color: #333;
}

.title {
  text-align: center;
  color: white;
  font-size: 28px;
  margin-bottom: 30px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
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
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: #999;
  font-size: 18px;
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

.scale-info, .size-info {
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
</style>




