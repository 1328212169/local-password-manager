import json
import base64
import secrets
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerificationError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
import hmac

class CryptoManager:
    def __init__(self):
        self.ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=1, hash_len=32, type=Type.ID)
        self.salt_length = 16
        self.nonce_length = 12
    
    def derive_key(self, master_password: str, salt: bytes) -> bytes:
        """使用 Argon2id 从主密码和 salt 派生加密密钥"""
        key = self.ph.hash(master_password, salt=salt).encode()
        # 提取哈希值部分
        hash_part = key.split(b'$')[-1]
        return hash_part[:32]
    
    def generate_salt(self) -> bytes:
        """生成 16 字节随机 salt"""
        return secrets.token_bytes(self.salt_length)
    
    def generate_nonce(self) -> bytes:
        """生成 12 字节随机 nonce"""
        return secrets.token_bytes(self.nonce_length)
    
    def encrypt_data(self, key: bytes, plaintext: dict) -> tuple[bytes, bytes]:
        """使用 AES-256-GCM 加密数据"""
        nonce = self.generate_nonce()
        aesgcm = AESGCM(key)
        plaintext_json = json.dumps(plaintext, ensure_ascii=False).encode('utf-8')
        ciphertext = aesgcm.encrypt(nonce, plaintext_json, None)
        return nonce, ciphertext
    
    def decrypt_data(self, key: bytes, nonce: bytes, ciphertext: bytes) -> dict:
        """使用 AES-256-GCM 解密数据"""
        aesgcm = AESGCM(key)
        plaintext_json = aesgcm.decrypt(nonce, ciphertext, None)
        return json.loads(plaintext_json.decode('utf-8'))
    
    def save_encrypted_db(self, file_path: str, master_password: str, data: dict, entries_order: list) -> None:
        """保存加密数据库"""
        # 生成 salt
        salt = self.generate_salt()
        # 派生密钥
        key = self.derive_key(master_password, salt)
        # 加密数据
        nonce, ciphertext = self.encrypt_data(key, data)
        
        # 构建数据库结构
        db = {
            "salt": base64.b64encode(salt).decode('utf-8'),
            "nonce": base64.b64encode(nonce).decode('utf-8'),
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
            "entries_order": entries_order
        }
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
    
    def load_encrypted_db(self, file_path: str, master_password: str) -> tuple[dict, list]:
        """加载加密数据库"""
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        # 解码 base64 数据
        salt = base64.b64decode(db["salt"])
        nonce = base64.b64decode(db["nonce"])
        ciphertext = base64.b64decode(db["ciphertext"])
        entries_order = db["entries_order"]
        
        # 派生密钥
        key = self.derive_key(master_password, salt)
        
        # 解密数据
        try:
            data = self.decrypt_data(key, nonce, ciphertext)
            return data, entries_order
        except Exception as e:
            raise VerificationError("解密失败，主密码可能不正确")
    
    def verify_master_password(self, file_path: str, master_password: str) -> bool:
        """验证主密码是否正确"""
        try:
            self.load_encrypted_db(file_path, master_password)
            return True
        except VerificationError:
            return False
        except Exception as e:
            return False
    
    def change_master_password(self, file_path: str, old_password: str, new_password: str) -> bool:
        """更改主密码"""
        try:
            # 加载现有数据
            data, entries_order = self.load_encrypted_db(file_path, old_password)
            # 用新密码重新加密保存
            self.save_encrypted_db(file_path, new_password, data, entries_order)
            return True
        except Exception as e:
            return False
