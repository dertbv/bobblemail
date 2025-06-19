# ATLAS Adaptive Configuration - Quick Reference

## 🧠 **Adaptive Commit Timing System**

ATLAS now intelligently adjusts commit timing based on your work context!

### 📊 **Available Work Contexts**

| Context | Delay | Best For |
|---------|-------|----------|
| **debugging** | 2 min | Bug fixes, rapid testing iterations |
| **research** | 5 min | Experiments, analysis, exploration |
| **optimization** | 10 min | Performance improvements, tuning |
| **feature** | 15 min | Feature development, implementation |
| **refactoring** | 20 min | Code restructuring, cleanup |
| **documentation** | 30 min | Writing docs, explanations |

### 🎯 **How to Use**

#### **Manual Context Setting**
```bash
# Interactive context selection
python atlas_adaptive_cli.py set

# Direct context setting
python -c "from atlas_adaptive_config import set_work_context; set_work_context('debugging')"
```

#### **Auto-Detection**
```bash
# Auto-detect from changed files
python atlas_adaptive_cli.py detect

# Auto-detect from commit message
python -c "from atlas_adaptive_config import auto_detect_context; auto_detect_context(message='fix bug in classifier')"
```

#### **Status Checking**
```bash
# Show current configuration
python atlas_adaptive_cli.py status

# Show help
python atlas_adaptive_cli.py help
```

### 🤖 **Automatic Context Detection**

ATLAS automatically detects context based on:

#### **File Types**
- `.py` files → **feature** context
- `.md`, `.txt` files → **documentation** context  
- `.log` files → **debugging** context
- `.test.py` files → **debugging** context

#### **File Name Patterns**
- Files with "fix", "debug", "bug" → **debugging** context
- Files with "optimize", "performance" → **optimization** context
- Files with "test", "experiment" → **research** context
- Files with "refactor", "cleanup" → **refactoring** context

#### **Commit Message Keywords**
- "fix", "debug", "error" → **debugging** context
- "optimize", "improve", "enhance" → **optimization** context
- "implement", "add", "create" → **feature** context
- "doc", "readme", "explain" → **documentation** context

### ⚙️ **Integration**

#### **Works With Existing ATLAS Systems**
- ✅ Auto-commit system uses adaptive delays
- ✅ Auto-watcher respects context timing
- ✅ Manual commits still work instantly
- ✅ ATLAS memory system logs context changes

#### **Workflow Examples**

**Bug Fixing Session:**
```bash
# Set debugging context (2-minute commits)
python atlas_adaptive_cli.py set  # Choose option 1
# Make changes, auto-commits every 2 minutes
```

**Feature Development:**
```bash
# Set feature context (15-minute commits)  
python atlas_adaptive_cli.py set  # Choose option 2
# Work on features, commits every 15 minutes
```

**Performance Optimization:**
```bash
# Set optimization context (10-minute commits)
python atlas_adaptive_cli.py set  # Choose option 5
# Optimize code, commits every 10 minutes
```

### 📈 **Context Statistics**

ATLAS tracks your context usage:
- Context switches during session
- Most used context type
- Session duration
- Usage breakdown by context

### 🔧 **Configuration Files**

- **`atlas_adaptive_config.json`** - Stores current context and history
- **`.env`** - Fallback environment variables
- **`atlas_adaptive_config.py`** - Core adaptive system
- **`atlas_adaptive_cli.py`** - Command-line interface

### 💡 **Pro Tips**

1. **Let ATLAS auto-detect** - It's smart about file types and patterns
2. **Use debugging context** - For rapid iteration on bug fixes
3. **Switch contexts** - When changing work types mid-session
4. **Check status regularly** - To see your productivity patterns
5. **Trust the timing** - Each context is optimized for that work type

### 🚀 **Current Status**

- ✅ **Adaptive system active**
- ✅ **Auto-watcher using adaptive delays**
- ✅ **Auto-detection working**
- ✅ **Context persistence enabled**
- ✅ **CLI interface ready**

**Ready for intelligent, context-aware development!** 🧠
