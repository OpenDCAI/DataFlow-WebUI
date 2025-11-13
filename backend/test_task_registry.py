#!/usr/bin/env python
"""
任务注册表功能测试脚本
用于验证任务注册表的核心功能

使用方法:
    cd /data1/hzh/DataFlow-WebUI/backend
    python test_task_registry.py
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

def test_task_registry():
    """测试任务注册表的基本功能"""
    print("=" * 60)
    print("任务注册表功能测试")
    print("=" * 60)
    
    try:
        # 导入测试
        print("\n1. 导入模块测试...")
        from app.services.task_registry import TaskRegistry
        from app.schemas.task import TaskCreate, TaskUpdate, TaskOut
        print("   ✓ 模块导入成功")
        
        # 创建测试注册表
        print("\n2. 创建任务注册表实例...")
        test_registry_path = "data/test_task_registry.yaml"
        registry = TaskRegistry(path=test_registry_path)
        print(f"   ✓ 注册表创建成功: {test_registry_path}")
        
        # 测试创建任务
        print("\n3. 创建测试任务...")
        task_data = {
            "dataset_id": "test_dataset_123",
            "executor_name": "TestPipeline",
            "executor_type": "pipeline",
            "meta": {"test": "true"}
        }
        task = registry.create(task_data)
        print(f"   ✓ 任务创建成功")
        print(f"   - 任务ID: {task['id']}")
        print(f"   - 状态: {task['status']}")
        print(f"   - 创建时间: {task['created_at']}")
        
        task_id = task["id"]
        
        # 测试获取任务
        print("\n4. 获取任务详情...")
        retrieved_task = registry.get(task_id)
        assert retrieved_task is not None, "任务获取失败"
        assert retrieved_task["id"] == task_id, "任务ID不匹配"
        print(f"   ✓ 任务获取成功: {retrieved_task['executor_name']}")
        
        # 测试更新任务
        print("\n5. 更新任务状态...")
        updated_task = registry.update(task_id, {"status": "running"})
        assert updated_task["status"] == "running", "状态更新失败"
        assert updated_task["started_at"] is not None, "开始时间未设置"
        print(f"   ✓ 任务状态更新为: {updated_task['status']}")
        print(f"   - 开始时间: {updated_task['started_at']}")
        
        # 测试完成任务
        print("\n6. 完成任务...")
        completed_task = registry.update(task_id, {
            "status": "success",
            "output_id": "test_output_456"
        })
        assert completed_task["status"] == "success", "完成状态更新失败"
        assert completed_task["output_id"] == "test_output_456", "输出ID未设置"
        assert completed_task["finished_at"] is not None, "完成时间未设置"
        print(f"   ✓ 任务完成")
        print(f"   - 输出ID: {completed_task['output_id']}")
        print(f"   - 完成时间: {completed_task['finished_at']}")
        
        # 测试列表功能
        print("\n7. 测试任务列表...")
        all_tasks = registry.list()
        assert len(all_tasks) >= 1, "任务列表为空"
        print(f"   ✓ 共有 {len(all_tasks)} 个任务")
        
        # 测试状态过滤
        success_tasks = registry.list(status="success")
        print(f"   ✓ 成功任务: {len(success_tasks)} 个")
        
        # 测试统计
        print("\n8. 获取统计信息...")
        stats = registry.get_statistics()
        print(f"   ✓ 统计信息:")
        print(f"   - 总任务数: {stats['total']}")
        print(f"   - 成功: {stats['success']}")
        print(f"   - 失败: {stats['failed']}")
        print(f"   - Pipeline任务: {stats['by_executor_type']['pipeline']}")
        print(f"   - Operator任务: {stats['by_executor_type']['operator']}")
        
        # 创建更多测试任务
        print("\n9. 创建更多测试任务...")
        for i in range(3):
            test_task = {
                "dataset_id": f"dataset_{i}",
                "executor_name": f"Operator{i}",
                "executor_type": "operator",
                "meta": {"index": str(i)}
            }
            new_task = registry.create(test_task)
            # 设置不同状态
            if i == 0:
                registry.update(new_task["id"], {"status": "running"})
            elif i == 1:
                registry.update(new_task["id"], {"status": "failed", "error_message": "测试失败"})
            print(f"   ✓ 创建任务 {i+1}/3")
        
        # 最终统计
        print("\n10. 最终统计...")
        final_stats = registry.get_statistics()
        print(f"   ✓ 最终统计:")
        print(f"   - 总任务数: {final_stats['total']}")
        print(f"   - Pending: {final_stats['pending']}")
        print(f"   - Running: {final_stats['running']}")
        print(f"   - Success: {final_stats['success']}")
        print(f"   - Failed: {final_stats['failed']}")
        
        # 清理测试文件
        print("\n11. 清理测试文件...")
        if os.path.exists(test_registry_path):
            os.remove(test_registry_path)
            print(f"   ✓ 测试文件已删除: {test_registry_path}")
        
        print("\n" + "=" * 60)
        print("✓✓✓ 所有测试通过！")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_task_registry()
    # sys.exit(0 if success else 1)


