#!/bin/bash

# 确保在项目根目录
cd "$(dirname "$0")"

echo "🧹 清理旧构建..."
rm -rf build/ dist/

echo "📦 开始 PyInstaller 打包..."
# 需要先安装 pyinstaller: pip install pyinstaller
pyinstaller chatagentcore.spec

if [ $? -eq 0 ]; then
    echo "✅ 打包成功！"
    echo "📂 输出文件位于: dist/chatagent-service"
    
    # 验证文件大小
    du -h dist/chatagent-service
    
    echo ""
    echo "💡 交付建议："
    echo "请将 dist/chatagent-service 和 deploy/chatagent.service 一并打包给用户。"
else
    echo "❌ 打包失败，请检查错误日志。"
    exit 1
fi
