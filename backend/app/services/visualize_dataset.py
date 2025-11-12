import pandas as pd
from app.services.dataset_registry import _DATASET_REGISTRY
import os
class VisualizeDatasetService:
    def __init__(self):
        self.pandas_read_func_map = {
            "csv": pd.read_csv,
            "excel": pd.read_excel,
            "json": pd.read_json,
            "parquet": pd.read_parquet,
            "pickle": pd.read_pickle,
            "jsonl": lambda path: pd.read_json(path, lines=True),
        }
        self.media_type_map = {
            "txt": "text/plain",
            "md": "text/markdown",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "pdf": "application/pdf",
            "doc": "application/msword",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "ppt": "application/vnd.ms-powerpoint",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        }
    
    def get_pandas_read_function(self, ds:dict, start:int=0, end:int=5):
        file_type = ds.get("type","").lower()
        file_path = ds.get("root","")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} does not exist. Please check the path.")
        if file_type not in self.pandas_read_func_map:
            raise ValueError(f"File type {file_type} is not supported for pandas visualization.")

        read_func = self.pandas_read_func_map.get(file_type, None)
        if not read_func:
            raise ValueError(f"No read function found for type: {file_type}")
        
        df = read_func(file_path)
        return df.iloc[start:end].to_dict(orient="records")
    
    def list_supported_file_types(self):
        return list(self.pandas_read_func_map.keys())
    
    def get_other_visualization_data(self, ds:dict):
        file_type = ds.get("type","").lower()
        file_path = ds.get("root","")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} does not exist. Please check the path.")
        media_type = self.media_type_map.get(file_type, "application/octet-stream")
        return file_path, media_type
