# config/test_config.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from Crypto.Cipher import AES
import base64

load_dotenv()

@dataclass
class EnvironmentConfig:
    base_url: str
    api_base_url: str
    ignore_https_errors: bool = False

class TestConfig:
    def __init__(self):
        self.environment = os.getenv("ENV", "qa").lower()
        self._load_config()

    def _load_config(self):
        configs = {
            "qa": EnvironmentConfig(
                base_url=os.getenv("QA_BASE_URL", "https://demoqa.com"),
                api_base_url=os.getenv("QA_API_BASE_URL", "https://demoqa.com"),
                ignore_https_errors=False
            ),
            "dev": EnvironmentConfig(
                base_url=os.getenv("DEV_BASE_URL", "https://dev.demoqa.com"),
                api_base_url=os.getenv("DEV_API_BASE_URL", "https://dev.demoqa.com"),
                ignore_https_errors=True
            )
        }
        self.config = configs.get(self.environment, configs["qa"])

    @property
    def base_url(self): return self.config.base_url

    @property
    def api_base_url(self): return self.config.api_base_url

    @property
    def ignore_https_errors(self): return self.config.ignore_https_errors

    def _decipher_password(self, enc_pass):  # 预留解密函数
        if not enc_pass: return ""
        key = os.getenv("SECRET_KEY", "default-key-32chars-long!!!!!").encode()[:32].ljust(32, b'\0')
        cipher = AES.new(key, AES.MODE_ECB)
        return cipher.decrypt(base64.b64decode(enc_pass)).rstrip(b'\0').decode()