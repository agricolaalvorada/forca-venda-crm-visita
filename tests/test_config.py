import os
import sys

# adiciona a pasta raiz (APP_SYNC_FV) ao sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app_sync_fv.config import AppConfig

cfg = AppConfig.from_env()
print("URL:", cfg.api_url)
print("KEY (cortada):", cfg.api_key[:5] + "*****")
print("Batch size:", cfg.batch_size)
