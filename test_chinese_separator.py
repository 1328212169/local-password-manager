from batch_importer import BatchImporter

# 创建测试文件路径
file_path = "test_chinese_separator.txt"

# 创建导入器实例
importer = BatchImporter()

# 测试解析文件
valid_entries, invalid_entries = importer.parse_file(file_path)

# 打印结果
print(f"有效条目数：{len(valid_entries)}")
print(f"无效条目数：{len(invalid_entries)}")

print("\n有效条目：")
for entry in valid_entries:
    print(f"  网站名：{entry['website_name']}, 网址：{entry['url']}, 账号：{entry['username']}, 密码：{entry['password']}")

print("\n无效条目：")
for invalid in invalid_entries:
    print(f"  行号：{invalid['row']}, 错误：{invalid['error']}, 数据：{invalid['data']}")
