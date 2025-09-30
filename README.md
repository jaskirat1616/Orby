# Orby

The local-first AI CLI with agentic powers. Connect Ollama, LM Studio, Hugging Face — no cloud required.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Local AI](https://img.shields.io/badge/local-AI-green.svg)](https://ollama.ai/)

## 🚀 Features

### 🔥 Enhanced CLI with Premium UI
- **Gemini/Claude-style Interface**: Rich panels, colors, and professional typography
- **TUI Mode**: Text-based user interface with panels like htop
- **Web Dashboard**: Streamlit-like web interface for visual monitoring
- **Session Management**: Save, load, and manage conversation sessions

### 🤖 Advanced Agentic Capabilities
- **Built-in Tools**: Shell commands, web search, file system access, code execution
- **Plugin System**: Extend functionality with custom tools
- **Auto Mode**: Let Orby chain multiple reasoning steps autonomously
- **Memory Layer**: Ephemeral (session) + persistent (project-level) memory

### 🧠 Model Management
- **Multi-backend Support**: Ollama, LM Studio, vLLM, ExLlama, GPT4All
- **Auto-detection**: Automatically discovers locally installed models
- **Dynamic Switching**: `orby use mistral` or `orby use llama3-70b`
- **Benchmarking**: Rank models by performance with `orby benchmark`

### 💻 Developer Experience Superpowers
- **Repo-aware Coding**: Multi-file context awareness
- **Refactoring & Debugging**: Claude/Gemini-style coding abilities
- **Live Mode**: Background monitoring with proactive suggestions
- **Context Control**: Embeddings, summaries, and RAG from local docs

### 🌐 Modern AI Integrations
- **Built-in RAG**: From local files (PDF, Markdown, code)
- **Voice Mode**: Local speech-to-text with Whisper
- **Vision Mode**: Image processing with LLaVA or similar
- **Streaming Outputs**: Token-level updates with timing metrics

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/orby/orby.git
cd orby

# Install with all optional dependencies
pip install -e ".[voice,vision,web]"

# Or install minimal version
pip install -e .
```

## 🚀 Quick Start

### 1. Start a Chat Session
```bash
orby chat
```

### 2. List Available Models
```bash
orby models
```

### 3. Benchmark Your Models
```bash
orby benchmark
```

### 4. Search Your Codebase
```bash
orby search "function that processes images"
```

### 5. Launch TUI Mode
```bash
orby tui
```

## 🛠️ Commands

### Core Commands
```bash
orby chat [--model MODEL] [--auto] [--tui] [--session SESSION]
orby run "Your prompt here" [--model MODEL]
orby models
orby config [show|set|create-profile|use-profile]
```

### Enhanced Commands
```bash
orby use MODEL_NAME           # Switch to a different model
orby benchmark                # Benchmark available models
orby search QUERY             # Search for context in your project
orby tui                      # Launch TUI mode
orby live                     # Start live monitoring mode
orby plugins                  # List available plugins
orby install-plugin FILE      # Install a custom plugin
orby memory                   # Show memory statistics
orby clear-memory             # Clear all memory
orby context                  # Show current context
```

## 🎯 Advanced Features

### Model Management
```bash
# Auto-detect and switch between models
orby models
orby use llama3.70b:latest
orby benchmark
```

### Session Management
```bash
# In chat mode:
/save session_name
/load session_name
/reset
/auto  # Toggle auto-approve mode
```

### Live Mode
```bash
orby live  # Monitor file changes and get proactive suggestions
```

### Plugin System
```bash
orby plugins
orby install-plugin my_custom_tool.py
```

## 🧪 Example Usage

### Interactive Chat with Tools
```
$ orby chat
┌──────────────────────────────────────────────────────────────────────────────┐
│ ORBY                                                                         │
│ Local-first AI CLI with agentic powers                                       │
├──────────────────────────────────────────────────────────────────────────────┤
│ Connected: ollama | Model: llama3.1:latest                                    │
└──────────────────────────────────────────────────────────────────────────────┘

You > Show me the files in the current directory
┌───────────── You ──────────────┐
│ > Show me the files in the current directory │
└────────────────────────────────┘
⠋ Processing...
┌──────────────────────────────────── Orby ────────────────────────────────────┐
│ ✦                                                                            │
│ I can help you list files in the current directory. Would you like me to   │
│ run 'ls -la'?                                                                │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Code Assistance
```
$ orby run "Refactor this Python function to use list comprehension"
┌───────────── You ──────────────┐
│ > Refactor this Python function to use list comprehension                     │
└────────────────────────────────┘
⠋ Processing...
┌──────────────────────────────────── Orby ────────────────────────────────────┐
│ ✦                                                                            │
│ I can help you refactor Python code. Please provide the function you'd      │
│ like me to refactor, and I'll convert it to use list comprehensions.         │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Model Benchmarking
```
$ orby benchmark
┌────────────────────────────────── Benchmark Results ──────────────────────────────────┐
│ Rank  Model                    Backend     Score                                     │
│ 1     llama3.1:latest        ollama      95.2                                      │
│ 2     mistral:latest         ollama      92.8                                      │
│ 3     gemma2:latest          ollama      88.5                                      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

## 🧰 Configuration

### Default Configuration
```yaml
# ~/.orby/config.yml
default_model: llama3.1:latest
default_backend: ollama
ollama_url: http://localhost:11434
lmstudio_url: http://localhost:1234
```

### Profiles
```bash
orby config create-profile development
orby config create-profile production
orby config use-profile development
```

## 🔧 Supported Backends

- **Ollama**: Local model serving with automatic model management
- **LM Studio**: Desktop app with API-compatible interface
- **vLLM**: High-throughput serving engine
- **ExLlama**: Optimized inference for GGUF models
- **GPT4All**: Cross-platform local models

## 📚 Documentation

### Tools
- `shell`: Execute secure shell commands
- `code`: Execute code snippets in sandboxed environments
- `file`: Read, write, and manipulate files
- `web`: Fetch web content and perform searches
- `vision`: Process images with local vision models
- `voice`: Transcribe audio with local speech recognition

### Memory System
- **Session Memory**: Ephemeral conversation history
- **Persistent Memory**: Project-level knowledge retention
- **Context Aware**: Automatic retrieval of relevant information

### Plugin Architecture
```python
# Example custom plugin
from orby.plugins import ToolPlugin

class MyCustomTool(ToolPlugin):
    @property
    def name(self) -> str:
        return "my_tool"
    
    @property
    def description(self) -> str:
        return "My custom tool that does amazing things"
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        # Your custom logic here
        return {"status": "success", "result": "Custom tool executed"}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

### Development Setup
```bash
git clone https://github.com/orby/orby.git
cd orby
pip install -e ".[dev]"
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Inspired by Gemini CLI and Anthropic Claude
- Built with ❤️ for the local AI community
- Special thanks to the Ollama, LM Studio, and Hugging Face teams

---

**Orby** - The local-first AI CLI that puts agentic power in your terminal.