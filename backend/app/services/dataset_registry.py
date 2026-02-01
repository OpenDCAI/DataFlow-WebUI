import yaml, os, hashlib
import json
from typing import Dict, List
from app.core.config import settings
from loguru import logger
import pandas as pd

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
        
        df: pd.DataFrame = read_func(file_path)
        return df.iloc[start:end].to_json(orient="records")
    
    def list_supported_file_types(self):
        return list(self.pandas_read_func_map.keys())
    
    def get_other_visualization_data(self, ds:dict):
        file_type = ds.get("type","").lower()
        file_path = ds.get("root","")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} does not exist. Please check the path.")
        media_type = self.media_type_map.get(file_type, "application/octet-stream")
        return file_path, media_type


class DatasetRegistry:
    def __init__(self, path: str | None = None, scan: bool = True):
        self.path = path or settings.DATA_REGISTRY
        self._ensure()
        if scan:
            self.scan_all_datasets()

    def scan_all_datasets(self) -> int:
        """
        扫描 DATAFLOW_CORE_DIR/example_data 下的所有 pipeline，
        并把其中的文件全部注册/更新到当前 registry 中。

        返回本次扫描注册/更新的数据集数量。
        """
        dataset_dir = os.path.join(settings.DATAFLOW_CORE_DIR, "example_data")
        if not os.path.exists(dataset_dir):
            logger.warning(f"[dataset] example_data directory not found: {dataset_dir}")
            return 0

        total_cnt = 0

        for pipeline_name in os.listdir(dataset_dir):
            pipeline_path = os.path.join(dataset_dir, pipeline_name)
            if not os.path.isdir(pipeline_path):
                continue

            cnt = 0
            for root, dirs, files in os.walk(pipeline_path):
                for file in files:
                    file_path = os.path.join(root, file)

                    ds_dict = {
                        "name": f"{pipeline_name}-{file}",
                        "root": file_path,
                        "pipeline": pipeline_name,
                        "meta": {},
                    }

                    try:
                        # 直接用 registry 的方法，避免依赖 API 层的 DatasetIn / register_dataset
                        self.add_or_update(ds_dict)
                        cnt += 1
                    except FileNotFoundError as e:
                        logger.warning(f"[dataset] Skip missing file '{file_path}': {e}")
                    except Exception as e:
                        logger.exception(
                            f"[dataset] Failed to register dataset from '{file_path}': {e}"
                        )

            logger.info(f"[dataset] Registered {cnt} datasets from pipeline '{pipeline_name}'.")
            total_cnt += cnt

        logger.info(f"[dataset] Total {total_cnt} datasets registered from '{dataset_dir}'.")
        return total_cnt
                # logging.info(f"Registered dataset from {relative_path}.")

    def _ensure(self):
        if not os.path.exists(self.path):
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                yaml.safe_dump({"datasets": {}}, f, allow_unicode=True)

    def _read(self) -> Dict:
        with open(self.path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {"datasets": {}}

    def _write(self, data: Dict):
        with open(self.path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

    def _count_file_entries(self, file_path: str) -> int:
        """统计文件中的条目数量"""
        # 根据文件类型使用不同的方法计算条目数
        file_ext = file_path.split('.')[-1].lower()
        
        try:
            if file_ext in ['csv', 'jsonl', 'txt', 'log']:
                # 对于文本类文件，按行计数
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return sum(1 for _ in f)
            elif file_ext == 'json':
                # 对于JSON文件，尝试加载并计算
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return len(data)
                    elif isinstance(data, dict):
                        # 如果是字典，返回键的数量
                        return len(data)
                    else:
                        return 1  # 单个值
            else:
                # 对于其他类型文件，默认为1个条目
                return 1
        except Exception:
            # 出错时返回0
            return 0
    
    def list(self) -> List[Dict]:
        logger.info("Starting to read all dataset information")
        """返回所有数据集列表，每个数据集包含条目数和文件大小信息"""
        datasets = list(self._read()["datasets"].values())
        return datasets
    
    def _load_file_hash(self, file_path: str) -> str:
        """计算文件的 MD5 哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def add_or_update(self, ds: Dict):
        data = self._read()
        # 计算一个稳定 id（基于路径）
        ds_id = hashlib.md5(ds["root"].encode("utf-8")).hexdigest()[:10]
        ds["id"] = ds_id
        try: 
            ds["hash"] = self._load_file_hash(ds["root"])
            
            # 计算文件大小（字节）
            ds["file_size"] = os.path.getsize(ds["root"])
            
            # 计算文件条目数
            ds["num_samples"] = self._count_file_entries(ds["root"])
            
        except Exception:
            raise FileNotFoundError(f"Cannot read file at {ds['root']}")
        
        ds['type'] = ds.get('root','').split('.')[-1].lower()
        ds["added_at"] = pd.Timestamp.now().isoformat()
        
        # 覆盖或新增
        datasets = data.get("datasets",{})
        datasets[ds_id] = ds
        data["datasets"] = datasets
        self._write(data)
        return ds

    def get(self, ds_id: str) -> Dict | None:
        return self._read()["datasets"].get(ds_id)
    
    def remove(self, ds_id: str):
        data = self._read()
        datasets = data.get("datasets", {})
        if ds_id in datasets:
            del datasets[ds_id]
            data["datasets"] = datasets
            self._write(data)
            return True
        return False
    
    def preview(self, ds_id: str, num_lines: int = 5) -> List[Dict]:
        """获取数据集文件的前几行内容预览，支持json、jsonl和parquet格式
        
        Args:
            ds_id: 数据集ID
            num_lines: 要预览的行数
            
        Returns:
            包含预览内容的列表，每个元素是一个字典
        """
        ds = self.get(ds_id)
        if not ds:
            raise FileNotFoundError(f"Dataset with id {ds_id} not found")
        
        file_path = ds["root"]
        file_type = ds.get("type", "").lower()
        
        # 检查是否支持预览的文件类型
        supported_types = ["json", "jsonl", "parquet"]
        is_supported = file_type in supported_types
        
        preview_list = []
        if is_supported:
            try:
                if file_type == "jsonl":
                    # 对于jsonl文件，读取前num_lines行并解析为dict
                    with open(file_path, "r", encoding="utf-8") as f:
                        for i, line in enumerate(f):
                            if i >= num_lines:
                                break
                            preview_list.append(json.loads(line.strip()))
                elif file_type == "json":
                    # 对于json文件，读取整个文件并尝试解析
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            # 如果是列表，只取前num_lines个元素
                            preview_list = data[:num_lines]
                        else:
                            # 如果是字典，将其作为单个元素添加到列表中
                            preview_list = [data]
                elif file_type == "parquet":
                    # 对于parquet文件，使用pandas读取前num_lines行并转换为list of dict
                    import pandas as pd
                    df = pd.read_parquet(file_path, nrows=num_lines)
                    preview_list = df.to_dict(orient="records")
            except Exception as e:
                # 出错时返回空列表
                preview_list = []
        
        return preview_list
    
    def get_columns(self, ds_id: str) -> List[str]:
        """获取数据集的列名，支持json、jsonl和parquet格式
        
        Args:
            ds_id: 数据集ID
            
        Returns:
            列名列表，如果不支持则返回空列表
        """
        ds = self.get(ds_id)
        if not ds:
            raise FileNotFoundError(f"Dataset with id {ds_id} not found")
        
        file_path = ds["root"]
        file_type = ds.get("type", "").lower()
        
        # 检查是否支持获取列名的文件类型
        supported_types = ["json", "jsonl", "parquet"]
        is_supported = file_type in supported_types
        
        columns = []
        if is_supported:
            try:
                if file_type == "jsonl":
                    # 对于jsonl文件，读取第一行并解析为JSON，然后提取键名
                    with open(file_path, "r", encoding="utf-8") as f:
                        first_line = f.readline()
                        if first_line:
                            import json
                            first_record = json.loads(first_line)
                            if isinstance(first_record, dict):
                                columns = list(first_record.keys())
                elif file_type == "json":
                    # 对于json文件，读取整个文件并提取键名
                    with open(file_path, "r", encoding="utf-8") as f:
                        import json
                        data = json.load(f)
                        if isinstance(data, list) and len(data) > 0:
                            # 如果是列表，取第一个元素的键名
                            if isinstance(data[0], dict):
                                columns = list(data[0].keys())
                        elif isinstance(data, dict):
                            # 如果是字典，直接取键名
                            columns = list(data.keys())
                elif file_type == "parquet":
                    # 对于parquet文件，使用pandas读取文件并获取列名
                    import pandas as pd
                    df = pd.read_parquet(file_path, nrows=1)
                    columns = list(df.columns)
            except Exception:
                # 出错时返回空列表
                columns = []
        
        return columns
