import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing simple main.py execution...")
try:
    # 直接运行 main.py
    exec(open('main.py', encoding='utf-8').read())
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
