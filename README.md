# 🎮 AI Game Generator

基于人工智能的HTML5游戏生成器，用户只需用自然语言描述想要的游戏，AI就能在30秒内生成完整可玩的HTML5游戏。

## ✨ 特性

- 🤖 **AI驱动**: 使用DeepSeek大语言模型生成游戏代码
- ⚡ **快速生成**: 30秒内完成游戏开发
- 🎯 **即时预览**: 实时查看生成的游戏效果
- 📝 **代码查看**: Monaco编辑器支持语法高亮
- 📦 **一键下载**: ZIP格式打包所有游戏文件
- 🔒 **安全检查**: 内置代码安全扫描机制
- 🌊 **流式生成**: 支持实时生成进度显示

## 🛠️ 技术栈

### 后端
- **Python 3.10** - 后端开发语言
- **FastAPI** - 现代、高性能的Web框架
- **DeepSeek API** - 大语言模型API
- **Uvicorn** - ASGI服务器

### 前端
- **Vue 3** - 渐进式JavaScript框架
- **Vite** - 前端构建工具
- **Monaco Editor** - 代码编辑器
- **JSZip** - 文件压缩库

## 🚀 快速开始

### 1. 环境要求

- Python 3.10+
- Node.js 16+
- npm 8+

### 2. 项目设置

克隆项目并进入目录：
```bash
git clone <your-repo-url>
cd ai-game-generator
```

### 3. 一键启动

运行启动脚本：
```bash
chmod +x start-dev.sh
./start-dev.sh
```

启动脚本会自动：
- 检查Python环境
- 安装依赖
- 启动后端和前端服务
- 进行健康检查

### 4. 访问应用

- 🎨 **前端界面**: http://localhost:5173
- 🔧 **后端API**: http://localhost:8000
- 💊 **健康检查**: http://localhost:8000/health

## 📁 项目结构

```
ai-game-generator/
├── backend/                 # 后端代码
│   ├── app.py              # FastAPI应用主文件
│   ├── ai_engine.py        # AI引擎，DeepSeek API集成
│   ├── guard.py            # 安全检查模块
│   └── requirements.txt    # Python依赖
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── App.vue        # 主Vue组件
│   │   └── main.js        # 入口文件
│   ├── index.html         # HTML模板
│   ├── package.json       # Node.js依赖
│   └── vite.config.js     # Vite配置
├── config.env             # 环境变量配置
├── start-dev.sh           # 开发环境启动脚本
└── README.md              # 项目文档
```

## 🔧 配置说明

### 环境变量 (config.env)

```bash
# DeepSeek API配置
DEEPSEEK_API_KEY=your-deepseek-api-key

# 服务器配置
BACKEND_PORT=8000
FRONTEND_PORT=5173

# 开发环境配置
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

### API密钥获取

1. 访问 [DeepSeek官网](https://www.deepseek.com/)
2. 注册账号并申请API密钥
3. 将密钥配置到 `config.env` 文件中

## 💡 使用说明

### 基本流程

1. **输入游戏描述**
   - 在文本框中详细描述想要的游戏
   - 例如："制作一个贪吃蛇游戏，用方向键控制..."

2. **生成游戏**
   - 点击"🚀 生成游戏"按钮
   - 选择是否启用"实时流式生成"

3. **预览和下载**
   - 在左侧查看游戏预览
   - 在右侧查看生成的代码
   - 点击"📦 下载游戏文件"获取完整项目

### 示例提示词

```
制作一个简单的打砖块游戏：
- 用鼠标或键盘控制挡板左右移动
- 球撞击砖块后砖块消失
- 所有砖块消失后游戏获胜
- 球掉落到底部游戏失败
- 添加得分显示
```

```
创建一个太空射击游戏：
- 玩家飞船可以左右移动和射击
- 敌方飞船从上方随机出现
- 击中敌机获得分数
- 被敌机撞击减少生命值
- 生命值为0时游戏结束
```

## 🔒 安全特性

项目内置多层安全检查：

- **静态代码分析**: 检测危险的API调用
- **HTML标签过滤**: 防止恶意标签注入
- **外部资源限制**: 禁止加载外部资源
- **沙盒环境**: iframe沙盒运行生成的游戏

## 🔧 手动安装

如果一键启动脚本失败，可以手动安装：

### 后端安装

```bash
# 创建Python虚拟环境
python3.10 -m venv python3.10-env
source python3.10-env/bin/activate

# 安装依赖
pip install -r backend/requirements.txt

# 启动后端
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 前端安装

```bash
# 安装依赖
cd frontend
npm install

# 启动开发服务器
npm run dev
```

## 🐛 故障排除

### 常见问题

1. **后端启动失败**
   - 检查Python版本是否为3.10+
   - 确认虚拟环境已激活
   - 检查端口8000是否被占用

2. **前端编译错误**
   - 检查Node.js版本是否为16+
   - 清除node_modules重新安装
   - 检查端口5173是否被占用

3. **API调用失败**
   - 确认DEEPSEEK_API_KEY配置正确
   - 检查网络连接
   - 查看后端日志输出

4. **Monaco编辑器不显示**
   - 确认前端依赖安装完整
   - 检查浏览器控制台错误
   - 尝试刷新页面

### 日志查看

- **后端日志**: 终端输出或uvicorn日志
- **前端日志**: 浏览器开发者工具控制台

## 🤝 贡献指南

欢迎提交Bug报告、功能请求或代码贡献！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [DeepSeek](https://www.deepseek.com/) - 提供强大的AI模型
- [Vue.js](https://vuejs.org/) - 优秀的前端框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代的Python Web框架
- [Monaco Editor](https://microsoft.github.io/monaco-editor/) - 强大的代码编辑器

---

Made with ❤️ by AI Game Generator Team 