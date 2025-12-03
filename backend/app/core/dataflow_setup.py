from app.core.config import settings
# import logging
from loguru import logger as logging
from app.api.v1.endpoints.datasets import register_dataset
from app.schemas.dataset import DatasetIn
def setup_dataflow_core():
    import os
    import shutil

    core_dir = settings.DATAFLOW_CORE_DIR
    if not os.path.exists(core_dir):
        os.makedirs(core_dir, exist_ok=True)
    
    if not os.listdir(core_dir):
        # 假设有一些初始文件需要复制到 core 目录
        logging.info(f"Setting up DataFlow core directory at {core_dir}")
        # 需要在core_dir工作路径下通过系统命令行执行 dataflow init指令，并归还工作路径
        os.chdir(core_dir)
        os.system("dataflow init")
        os.chdir("../..")
        logging.info("DataFlow core setup completed.")
        print("Current working directory:", os.getcwd())
    else:
        logging.info(f"DataFlow core directory at {core_dir} already set up.")

    dataset_dir = os.path.join(core_dir, "example_data")
    for pipeline_name in os.listdir(dataset_dir):
        pipeline_path = os.path.join(dataset_dir, pipeline_name)
        if os.path.isdir(pipeline_path):
            # logging.info(f"Pipeline '{pipeline_name}' found in DataFlow core.")
            # registry all files under this pipeline
            cnt = 0
            for root, dirs, files in os.walk(pipeline_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, dataset_dir)
                    payload = DatasetIn(
                        name=f"{pipeline_name}-{file}",
                        root=file_path,
                        pipeline=f"{pipeline_name}",
                        meta={}
                    )
                    register_dataset(payload)
                    cnt += 1
            logging.info(f"Registered {cnt} datasets from pipeline '{pipeline_name}'.")
                    # logging.info(f"Registered dataset from {relative_path}.")