import csv
import uuid
from datetime import datetime

class BatchImporter:
    def __init__(self):
        self.valid_entries = []
        self.invalid_entries = []
    
    def parse_file(self, file_path: str) -> tuple[list, list]:
        """解析批量导入文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            tuple: (有效条目列表, 无效条目列表)
        """
        self.valid_entries = []
        self.invalid_entries = []
        
        try:
            # 尝试多种编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.readlines()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                self.invalid_entries.append({
                    'row': 0,
                    'data': [],
                    'error': '无法解析文件编码，请确保文件使用UTF-8或GBK编码'
                })
                return self.valid_entries, self.invalid_entries
            
            # 处理文件内容
            processed_rows = []
            
            for line in content:
                stripped_line = line.strip()
                # 跳过空行和注释行（以#开头）
                if stripped_line and not stripped_line.startswith('#'):
                    processed_rows.append(stripped_line)
            
            if file_path.endswith('.csv'):
                # 使用csv模块处理csv文件
                reader = csv.reader(processed_rows)
            else:  # .txt 文件
                # 处理TXT文件，支持更灵活的格式
                reader = []
                for line in processed_rows:
                    line_processed = line
                    # 统一将中文逗号转换为英文逗号
                    line_processed = line_processed.replace('，', ',')
                    # 统一将中文分号转换为英文分号
                    line_processed = line_processed.replace('；', ';')
                    
                    # 支持多种分隔符：中英文逗号、中英文分号、制表符
                    if ',' in line_processed:
                        row = line_processed.split(',')
                    elif ';' in line_processed:
                        row = line_processed.split(';')
                    elif '\t' in line_processed:
                        row = line_processed.split('\t')
                    else:
                        # 如果没有明确分隔符，尝试用空格分隔
                        row = line_processed.split()
                    reader.append([cell.strip() for cell in row])
            
            for row_num, row in enumerate(reader, 1):
                # 跳过空行或全空单元格的行
                if not row or all(cell == '' for cell in row):
                    continue
                
                # 确保行有足够的列
                if len(row) < 4:
                    self.invalid_entries.append({
                        'row': row_num,
                        'data': row,
                        'error': f'缺少必要字段，当前行只有{len(row)}列，至少需要4列（网站名,网址,账号,密码）'
                    })
                    continue
                
                # 解析字段
                website_name = row[0]
                url = row[1]
                username = row[2]
                password = row[3]
                note = row[4] if len(row) >= 5 else ''
                
                # 验证必要字段
                missing_fields = []
                if not website_name:
                    missing_fields.append('网站名')
                if not url:
                    missing_fields.append('网址')
                if not username:
                    missing_fields.append('账号')
                if not password:
                    missing_fields.append('密码')
                
                if missing_fields:
                    self.invalid_entries.append({
                        'row': row_num,
                        'data': row,
                        'error': f'以下字段不能为空：{', '.join(missing_fields)}'
                    })
                    continue
                
                # 格式化 URL
                if url and not (url.startswith('http://') or url.startswith('https://')):
                    url = 'https://' + url
                
                # 创建有效条目
                entry = {
                    'id': str(uuid.uuid4()),
                    'website_name': website_name,
                    'url': url,
                    'username': username,
                    'password': password,
                    'note': note,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                self.valid_entries.append(entry)
        
        except Exception as e:
            self.invalid_entries.append({
                'row': 0,
                'data': [],
                'error': f'文件读取错误：{str(e)}'
            })
        
        return self.valid_entries, self.invalid_entries
    
    def get_preview_data(self, file_path: str, max_preview: int = 10) -> tuple[list, list, int]:
        """获取导入预览数据
        
        Args:
            file_path: 文件路径
            max_preview: 最大预览行数
            
        Returns:
            tuple: (预览条目列表, 无效条目列表, 总有效条目数)
        """
        valid_entries, invalid_entries = self.parse_file(file_path)
        return valid_entries[:max_preview], invalid_entries, len(valid_entries)
    
    def import_entries(self, file_path: str) -> list:
        """导入条目
        
        Args:
            file_path: 文件路径
            
        Returns:
            list: 有效条目列表
        """
        valid_entries, _ = self.parse_file(file_path)
        return valid_entries
