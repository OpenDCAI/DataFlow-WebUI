import os
import yaml
import pytest
import tempfile
from app.services.dataset_registry import DatasetRegistry
from app.core.config import settings

# 临时测试文件路径
TEST_REGISTRY_PATH = "tests/tmp_test_registry.yaml"

@pytest.fixture
def test_registry():
    """创建一个临时的DatasetRegistry实例用于测试"""
    # 确保测试前删除临时文件
    if os.path.exists(TEST_REGISTRY_PATH):
        os.remove(TEST_REGISTRY_PATH)
    
    # 创建临时文件目录
    temp_dir = tempfile.mkdtemp()
    temp_files = []
    
    # 创建测试用的registry实例
    registry = DatasetRegistry(TEST_REGISTRY_PATH)
    
    # 创建临时数据集文件并添加到registry
    for i in range(5):
        # 创建临时CSV文件
        temp_file = tempfile.NamedTemporaryFile(suffix=f'.csv', dir=temp_dir, delete=False)
        temp_file.write(f"col1,col2\nvalue1,value2\n".encode('utf-8'))
        temp_file.close()
        temp_files.append(temp_file.name)
        
        # 添加数据集到registry
        dataset = {
            "root": temp_file.name,
            "name": f"Test Dataset {i}",
            "pipeline": "test_pipeline",
            "meta": {}
        }
        registry.add_or_update(dataset)
    
    yield registry
    
    # 测试后清理
    if os.path.exists(TEST_REGISTRY_PATH):
        os.remove(TEST_REGISTRY_PATH)
    
    # 清理临时文件
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    # 删除临时目录
    if os.path.exists(temp_dir):
        os.rmdir(temp_dir)

def test_list_all_datasets(test_registry):
    """测试列出所有数据集"""
    datasets = test_registry.list()
    assert len(datasets) == 5

def test_dataset_metadata(test_registry):
    """测试数据集的文件大小和条目数元数据"""
    datasets = test_registry.list()
    
    for dataset in datasets:
        # 检查是否包含必要的元数据字段
        assert 'file_size' in dataset
        assert 'num_samples' in dataset
        
        # 验证文件大小大于0（因为我们创建了有内容的临时文件）
        assert dataset['file_size'] > 0
        
        # 验证条目数为2（因为我们在临时文件中写入了2行）
        assert dataset['num_samples'] == 2

def test_count_file_entries_function(test_registry):
    """测试_count_file_entries方法对不同类型文件的处理"""
    # 创建测试用的临时文件
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        f.write(b"col1,col2\nvalue1,value2\nvalue3,value4\n")
        csv_file = f.name
    
    try:
        # 测试CSV文件的条目计数
        entries = test_registry._count_file_entries(csv_file)
        assert entries == 3  # 3行（1个表头+2个数据行）
    finally:
        # 清理临时文件
        if os.path.exists(csv_file):
            os.remove(csv_file)