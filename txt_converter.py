#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TXT文本格式转换脚本
输入格式：
网站名: N网
网址:
账号: zxcvbnmA186
密码: zxcvbnmA186@
--------------------------------------------------
网站名: 星辰云
网址:
账号: 18081587048
密码: agharbfbA186@
备注: 66

输出格式：
N网， `https://www.nexusmods.com/stardewvalley，zxcvbnmA186，zxcvbnmA186@`
星辰云， `https://console.starxn.com/，18081587048，agharbfbA186@备注:`  66
"""

# 网站名到网址的映射
WEBSITE_MAP = {
    'N网': 'https://www.nexusmods.com/stardewvalley',
    '星辰云': 'https://console.starxn.com/'
}

def parse_input_file(input_file):
    """解析输入文件，提取网站信息"""
    websites = []
    current_website = {}
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"错误：输入文件 '{input_file}' 不存在")
        return []
    except Exception as e:
        print(f"错误：读取文件时发生错误: {e}")
        return []
    
    # 跳过plaintext行（如果存在）
    if lines and lines[0].strip() == 'plaintext':
        lines = lines[1:]
    
    for line in lines:
        line = line.strip()
        
        # 处理分隔线
        if line.startswith('---'):
            if current_website:
                websites.append(current_website)
                current_website = {}
            continue
        
        # 解析键值对
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            if key == '网站名':
                current_website['name'] = value
            elif key == '网址':
                current_website['url'] = value
            elif key == '账号':
                current_website['username'] = value
            elif key == '密码':
                current_website['password'] = value
            elif key == '备注':
                current_website['note'] = value
    
    # 添加最后一个网站
    if current_website:
        websites.append(current_website)
    
    return websites

def format_output(websites):
    """格式化输出内容"""
    output_lines = ['']  # 开头添加空行
    
    for website in websites:
        name = website.get('name', '')
        url = website.get('url', '')
        username = website.get('username', '')
        password = website.get('password', '')
        note = website.get('note', '')
        
        # 构建内容
        if note:
            line = f"{name}，{url}，{username}，{password}，{note}"
        else:
            line = f"{name}，{url}，{username}，{password}"
        
        output_lines.append(line)
    
    return '\n'.join(output_lines)

def main():
    """主函数"""
    input_file = 'input.txt'
    output_file = 'output.txt'
    
    # 解析输入文件
    websites = parse_input_file(input_file)
    
    if not websites:
        print("警告：未解析到任何网站信息")
        return
    
    # 格式化输出
    output_content = format_output(websites)
    
    # 写入输出文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_content)
        print(f"转换完成，输出文件: {output_file}")
    except Exception as e:
        print(f"错误：写入文件时发生错误: {e}")

if __name__ == '__main__':
    main()
