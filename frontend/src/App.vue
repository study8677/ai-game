<template>
  <div class="app">
    <!-- 标题栏 -->
    <header class="header">
      <div class="container">
        <h1 class="title">🎮 AI Game Generator</h1>
        <p class="subtitle">用自然语言描述，30秒生成可玩的HTML5游戏</p>
      </div>
    </header>

    <!-- 主要内容区域 -->
    <main class="main">
      <div class="container">
        <!-- 输入区域 -->
        <div class="input-section">
          <div class="input-group">
            <label for="gamePrompt" class="input-label">
              描述您想要的游戏
            </label>
            <textarea
              id="gamePrompt"
              v-model="gamePrompt"
              class="game-input"
              placeholder="例如：制作一个简单的贪吃蛇游戏，用方向键控制蛇移动，吃到食物会变长，撞墙或撞到自己就失败..."
              rows="4"
              :disabled="isGenerating"
            ></textarea>
          </div>
          
          <div class="controls">
            <button 
              @click="generateGame" 
              class="generate-btn"
              :disabled="!gamePrompt.trim() || isGenerating"
            >
              <span v-if="isGenerating" class="loading-spinner"></span>
              {{ isGenerating ? '生成中...' : '🚀 生成游戏' }}
            </button>
            
            <div class="options">
              <label class="checkbox-label">
                <input type="checkbox" v-model="streamMode" :disabled="isGenerating">
                <span class="checkmark"></span>
                实时流式生成
              </label>
            </div>
          </div>
        </div>

        <!-- 进度显示 -->
        <div v-if="isGenerating || generationLogs.length > 0" class="progress-section">
          <div class="progress-header">
            <h3>生成进度</h3>
            <div v-if="isGenerating" class="progress-bar">
              <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
            </div>
          </div>
          
          <div class="logs">
            <div 
              v-for="(log, index) in generationLogs" 
              :key="index"
              class="log-item"
              :class="log.type"
            >
              <span class="log-time">{{ formatTime(log.time) }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </div>

        <!-- 结果显示区域 -->
        <div v-if="gameFiles && Object.keys(gameFiles).length > 0" class="result-section">
          <div class="result-header">
            <h3>🎉 游戏生成完成！</h3>
            <div class="result-actions">
              <button @click="downloadGame" class="download-btn">
                📦 下载游戏文件
              </button>
              <button @click="openGameInNewWindow" class="test-btn">
                🎮 新窗口测试
              </button>
              <button @click="showHtmlContent" class="debug-btn">
                🔍 查看HTML
              </button>
              <button @click="clearResult" class="clear-btn">
                🗑️ 清除结果
              </button>
            </div>
          </div>

          <!-- 游戏预览和代码查看 -->
          <div class="game-display">
            <!-- 预览区域 -->
            <div class="preview-section">
              <h4>游戏预览</h4>
              <div class="game-frame">
                <div v-if="!gameHtml" class="preview-placeholder">
                  🎮 游戏预览将在这里显示
                </div>
                <iframe
                  v-else
                  ref="gameIframe"
                  :srcdoc="gameHtml"
                  sandbox="allow-scripts allow-same-origin allow-modals allow-popups"
                  class="game-iframe"
                  frameborder="0"
                  @load="onIframeLoad"
                  @error="onIframeError"
                ></iframe>
              </div>
            </div>

            <!-- 代码查看区域 -->
            <div class="code-section">
              <div class="file-tabs">
                <button
                  v-for="(content, filename) in gameFiles"
                  :key="filename"
                  @click="activeFile = filename"
                  class="file-tab"
                  :class="{ active: activeFile === filename }"
                >
                  {{ filename }}
                </button>
              </div>
              
              <div class="code-editor">
                <div ref="monacoEditor" class="monaco-container"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- 错误显示 -->
        <div v-if="errorMessage" class="error-section">
          <div class="error-message">
            <span class="error-icon">❌</span>
            <span>{{ errorMessage }}</span>
            <button @click="errorMessage = ''" class="error-close">×</button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import * as monaco from 'monaco-editor'
import JSZip from 'jszip'

export default {
  name: 'App',
  data() {
    return {
      gamePrompt: '',
      isGenerating: false,
      streamMode: true,
      gameFiles: {},
      activeFile: '',
      gameHtml: '',
      generationLogs: [],
      progressPercent: 0,
      errorMessage: '',
      monacoInstance: null,
      eventSource: null
    }
  },
  mounted() {
    this.initMonaco()
  },
  beforeUnmount() {
    if (this.eventSource) {
      this.eventSource.close()
    }
    if (this.monacoInstance) {
      this.monacoInstance.dispose()
    }
  },
  watch: {
    activeFile(newFile) {
      if (newFile && this.gameFiles[newFile] && this.monacoInstance) {
        this.updateEditorContent()
      }
    }
  },
  methods: {
    async generateGame() {
      if (!this.gamePrompt.trim()) return
      
      this.isGenerating = true
      this.generationLogs = []
      this.progressPercent = 0
      this.errorMessage = ''
      this.gameFiles = {}
      this.gameHtml = ''
      
      this.addLog('开始生成游戏...', 'info')
      
      try {
        if (this.streamMode) {
          await this.generateGameStream()
        } else {
          await this.generateGameSync()
        }
      } catch (error) {
        console.error('生成失败:', error)
        this.errorMessage = '游戏生成失败: ' + error.message
        this.addLog('生成失败: ' + error.message, 'error')
      } finally {
        this.isGenerating = false
      }
    },
    
    async generateGameStream() {
      const apiUrl = 'http://localhost:8000/generateGame'
      
      this.eventSource = new EventSource(`${apiUrl}?` + new URLSearchParams({
        prompt: this.gamePrompt,
        stream: 'true'
      }))
      
      return new Promise((resolve, reject) => {
        this.eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleStreamData(data)
            
            if (data.type === 'complete' || data.type === 'end') {
              this.eventSource.close()
              this.eventSource = null
              resolve()
            } else if (data.type === 'error') {
              this.eventSource.close()
              this.eventSource = null
              reject(new Error(data.message || '未知错误'))
            }
          } catch (error) {
            console.error('解析流数据错误:', error)
          }
        }
        
        this.eventSource.onerror = (error) => {
          console.error('EventSource错误:', error)
          this.eventSource.close()
          this.eventSource = null
          reject(new Error('连接中断，请重试'))
        }
      })
    },
    
    async generateGameSync() {
      const response = await fetch('http://localhost:8000/generateGame', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: this.gamePrompt,
          stream: false
        })
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '请求失败')
      }
      
      const result = await response.json()
      this.progressPercent = 100
      this.addLog('游戏生成完成！', 'success')
      this.processGameFiles(result.files)
    },
    
    handleStreamData(data) {
      switch (data.type) {
        case 'start':
          this.addLog(data.message, 'info')
          break
          
        case 'progress':
          this.addLog(data.message, 'info')
          this.progressPercent = Math.min((data.length || 0) / 50, 90)
          break
          
        case 'file':
          this.addLog(`收到文件: ${data.name}`, 'success')
          if (!this.gameFiles[data.name]) {
            this.gameFiles[data.name] = atob(data.content)
            if (!this.activeFile) {
              this.activeFile = data.name
            }
          }
          break
          
        case 'complete':
          this.progressPercent = 100
          this.addLog(data.message || '游戏生成完成！', 'success')
          if (data.files) {
            this.processGameFiles(data.files)
          }
          break
          
        case 'warning':
          this.addLog(data.message, 'warning')
          break
          
        case 'error':
          this.addLog(data.message, 'error')
          this.errorMessage = data.message
          break
      }
    },
    
    processGameFiles(files) {
      console.log('=== 开始处理游戏文件 ===')
      console.log('接收到的files对象:', files)
      
      // 解码Base64文件内容
      for (const [filename, content] of Object.entries(files)) {
        console.log(`处理文件: ${filename}, base64长度: ${content.length}`)
        try {
          this.gameFiles[filename] = atob(content)
          console.log(`解码后文件 ${filename} 内容长度: ${this.gameFiles[filename].length}`)
          console.log(`文件 ${filename} 前100字符:`, this.gameFiles[filename].substring(0, 100))
        } catch (error) {
          console.error(`解码文件 ${filename} 失败:`, error)
        }
      }
      
      console.log('最终的gameFiles:', Object.keys(this.gameFiles))
      
      // 设置默认活动文件
      if (!this.activeFile && Object.keys(this.gameFiles).length > 0) {
        this.activeFile = Object.keys(this.gameFiles).find(name => 
          name.endsWith('.html') || name.endsWith('.htm')
        ) || Object.keys(this.gameFiles)[0]
        console.log('设置活动文件:', this.activeFile)
      }
      
      // 创建游戏预览URL
      this.createGamePreview()
      
      // 更新Monaco编辑器内容
      this.$nextTick(() => {
        this.updateEditorContent()
      })
    },
    
    createGamePreview() {
      console.log('=== 开始创建游戏预览 ===')
      console.log('当前gameFiles:', Object.keys(this.gameFiles))
      
      // 找到HTML文件
      const htmlFile = Object.keys(this.gameFiles).find(name => 
        name.endsWith('.html') || name.endsWith('.htm')
      )
      
      console.log('找到的HTML文件:', htmlFile)
      
      if (!htmlFile) {
        console.error('未找到HTML文件')
        this.addLog('未找到HTML文件，无法预览游戏', 'error')
        return
      }
      
      let htmlContent = this.gameFiles[htmlFile]
      console.log('原始HTML内容长度:', htmlContent.length)
      console.log('原始HTML内容前500字符:', htmlContent.substring(0, 500))
      
      if (!htmlContent || htmlContent.length < 10) {
        console.error('HTML内容为空或过短')
        this.addLog('HTML内容无效，无法预览游戏', 'error')
        return
      }
      
      // 简单处理：确保基本的HTML结构
      if (!htmlContent.includes('<!DOCTYPE html')) {
        htmlContent = '<!DOCTYPE html>\n' + htmlContent
      }
      
      if (!htmlContent.includes('<html')) {
        htmlContent = htmlContent.replace('<!DOCTYPE html>', '<!DOCTYPE html>\n<html lang="zh-CN">')
        htmlContent += '\n</html>'
      }
      
      if (!htmlContent.includes('<head')) {
        htmlContent = htmlContent.replace('<html', '<html>\n<head>\n<meta charset="UTF-8">\n<title>游戏</title>\n</head>')
      }
      
      if (!htmlContent.includes('charset=')) {
        htmlContent = htmlContent.replace('<head>', '<head>\n<meta charset="UTF-8">')
      }
      
      console.log('处理后的HTML内容长度:', htmlContent.length)
      console.log('处理后的HTML内容前800字符:', htmlContent.substring(0, 800))
      
      try {
        // 直接设置HTML内容
        this.gameHtml = htmlContent
        console.log('设置游戏HTML内容成功')
        
        // 添加日志
        this.addLog('游戏预览已生成', 'success')
        
        // Vue会自动更新iframe的srcdoc属性
        this.$nextTick(() => {
          console.log('iframe内容已更新')
        })
        
      } catch (error) {
        console.error('设置游戏HTML失败:', error)
        this.addLog(`设置游戏HTML失败: ${error.message}`, 'error')
      }
    },
    
    initMonaco() {
      this.$nextTick(() => {
        if (this.$refs.monacoEditor) {
          this.monacoInstance = monaco.editor.create(this.$refs.monacoEditor, {
            value: '// 请选择一个文件查看代码',
            language: 'html',
            theme: 'vs-dark',
            readOnly: true,
            automaticLayout: true,
            fontSize: 14,
            lineNumbers: 'on',
            wordWrap: 'on'
          })
        }
      })
    },
    
    updateEditorContent() {
      if (this.monacoInstance && this.activeFile && this.gameFiles[this.activeFile]) {
        const content = this.gameFiles[this.activeFile]
        const language = this.getLanguageForFile(this.activeFile)
        
        const model = monaco.editor.createModel(content, language)
        this.monacoInstance.setModel(model)
      }
    },
    
    getLanguageForFile(filename) {
      if (filename.endsWith('.html') || filename.endsWith('.htm')) return 'html'
      if (filename.endsWith('.css')) return 'css'
      if (filename.endsWith('.js')) return 'javascript'
      return 'text'
    },
    
    async downloadGame() {
      if (!this.gameFiles || Object.keys(this.gameFiles).length === 0) return
      
      const zip = new JSZip()
      
      // 添加所有文件到ZIP
      for (const [filename, content] of Object.entries(this.gameFiles)) {
        zip.file(filename, content)
      }
      
      // 添加README
      const indexFileName = 'index' + '.' + 'html'
      const readme = `# AI Generated Game

这是由AI游戏生成器创建的游戏。

## 游戏描述
${this.gamePrompt}

## 运行方式
直接在浏览器中打开 ${indexFileName} 文件即可开始游戏。

## 文件说明
${Object.keys(this.gameFiles).map(name => `- ${name}`).join('\n')}

生成时间: ${new Date().toLocaleString()}
`
      
      zip.file('README.md', readme)
      
      // 生成并下载ZIP文件
      const content = await zip.generateAsync({ type: 'blob' })
      const url = URL.createObjectURL(content)
      const a = document.createElement('a')
      a.href = url
      a.download = 'ai-generated-game.zip'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      
      this.addLog('游戏文件已下载', 'success')
    },
    
    clearResult() {
      this.gameFiles = {}
      this.activeFile = ''
      this.gameHtml = ''
      this.generationLogs = []
      this.progressPercent = 0
      this.errorMessage = ''
      
      if (this.monacoInstance) {
        const model = monaco.editor.createModel('// 请选择一个文件查看代码', 'html')
        this.monacoInstance.setModel(model)
      }
    },
    
    addLog(message, type = 'info') {
      this.generationLogs.push({
        time: new Date(),
        message,
        type
      })
      
      // 自动滚动到最新日志
      this.$nextTick(() => {
        const logsContainer = document.querySelector('.logs')
        if (logsContainer) {
          logsContainer.scrollTop = logsContainer.scrollHeight
        }
      })
    },
    
    formatTime(time) {
      return time.toLocaleTimeString()
    },
    
    onIframeLoad() {
      console.log('游戏加载完成')
      try {
        const iframe = this.$refs.gameIframe
        if (iframe && iframe.contentDocument) {
          // 检查iframe内容是否正常加载
          const doc = iframe.contentDocument
          console.log('iframe文档标题:', doc.title)
          console.log('iframe文档编码:', doc.characterSet)
          
          // 添加一些调试信息
          if (doc.body) {
            console.log('iframe内容长度:', doc.body.innerHTML.length)
          }
        }
      } catch (error) {
        console.warn('无法访问iframe内容（可能是跨域限制）:', error.message)
      }
    },
    
    onIframeError(event) {
      console.error('iframe加载出错:', event)
      this.addLog('游戏预览加载失败', 'error')
    },
    
    async openGameInNewWindow() {
      if (!this.gameHtml) return
      
      const newWindow = window.open('', '_blank')
      if (newWindow) {
        newWindow.document.write(this.gameHtml)
        newWindow.document.close()
        newWindow.focus()
      }
    },
    
    async showHtmlContent() {
      if (!this.gameFiles || !this.gameFiles[this.activeFile]) return
      
      const content = this.gameFiles[this.activeFile]
      const newWindow = window.open('', '_blank')
      if (newWindow) {
        newWindow.document.write(content)
        newWindow.document.close()
      }
    }
  }
}
</script>

<style scoped>
.app {
  min-height: 100vh;
  color: white;
}

.header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  padding: 2rem 0;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

.title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  background: linear-gradient(45deg, #fff, #a8edea);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
}

.main {
  padding: 2rem 0;
}

.input-section {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 1rem;
  padding: 2rem;
  margin-bottom: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.input-group {
  margin-bottom: 1.5rem;
}

.input-label {
  display: block;
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.game-input {
  width: 100%;
  padding: 1rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 1rem;
  resize: vertical;
  min-height: 100px;
}

.game-input::placeholder {
  color: rgba(255, 255, 255, 0.7);
}

.game-input:focus {
  outline: none;
  border-color: #a8edea;
  box-shadow: 0 0 0 3px rgba(168, 237, 234, 0.3);
}

.controls {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.generate-btn {
  background: linear-gradient(45deg, #667eea, #764ba2);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 0.5rem;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.generate-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}

.generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.loading-spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
}

.checkbox-label input {
  margin: 0;
}

.progress-section,
.result-section,
.error-section {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 1rem;
  padding: 2rem;
  margin-bottom: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.progress-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.progress-bar {
  width: 200px;
  height: 6px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.3s ease;
}

.logs {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 0.5rem;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.2);
}

.log-item {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.log-time {
  color: rgba(255, 255, 255, 0.7);
  font-family: monospace;
  white-space: nowrap;
}

.log-item.error .log-message {
  color: #ff6b6b;
}

.log-item.success .log-message {
  color: #51cf66;
}

.log-item.warning .log-message {
  color: #ffd43b;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.result-actions {
  display: flex;
  gap: 1rem;
}

.download-btn,
.test-btn,
.clear-btn,
.debug-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.download-btn {
  background: linear-gradient(45deg, #51cf66, #37b24d);
  color: white;
}

.test-btn {
  background: linear-gradient(45deg, #339af0, #1c7ed6);
  color: white;
}

.clear-btn {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.debug-btn {
  background: linear-gradient(45deg, #339af0, #1c7ed6);
  color: white;
}

.download-btn:hover,
.test-btn:hover,
.clear-btn:hover,
.debug-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}

.game-display {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

@media (max-width: 768px) {
  .game-display {
    grid-template-columns: 1fr;
  }
}

.preview-section h4,
.code-section h4 {
  margin-bottom: 1rem;
  font-size: 1.2rem;
}

.game-frame {
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 0.5rem;
  overflow: hidden;
  background: white;
}

.game-iframe {
  width: 100%;
  height: 400px;
  display: block;
}

.preview-placeholder {
  width: 100%;
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
  font-size: 1.2rem;
  border-radius: 0.5rem;
}

.file-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.file-tab {
  padding: 0.5rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 0.25rem;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
}

.file-tab:hover {
  background: rgba(255, 255, 255, 0.2);
}

.file-tab.active {
  background: linear-gradient(45deg, #667eea, #764ba2);
  border-color: transparent;
}

.monaco-container {
  height: 400px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 0.5rem;
  overflow: hidden;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(255, 107, 107, 0.2);
  border: 1px solid rgba(255, 107, 107, 0.5);
  border-radius: 0.5rem;
  color: #ff6b6b;
}

.error-close {
  background: none;
  border: none;
  color: #ff6b6b;
  font-size: 1.5rem;
  cursor: pointer;
  margin-left: auto;
}
</style> 