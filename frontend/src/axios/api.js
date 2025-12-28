/* eslint-disable */
// More information: https://github.com/minskiter/openapijs
import axios from './config.js'
import * as Axios from 'axios'
import * as UserModel from './model.js'

// fix vite error.
const CancelTokenSource = Axios.CancelTokenSource;


export class datasets {
 
  /**
  * @summary 返回目前所有注册的数据集列表，包含每个数据集的条目数和文件大小
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async list_datasets(cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/datasets/',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 注册一个新的数据集或更新已有数据集的信息，根据路径作为唯一主键
  * @param {UserModel.DatasetIn} [datasetin] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async register_dataset(datasetin,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'post',
        url:'/api/v1/datasets/',
        data:datasetin,
        params:{},
        headers:{
          "Content-Type":"application/json"
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 根据数据集 ID 获取数据集信息
  * @param {String} [pathds_id] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async get_dataset(pathds_id,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/datasets/'+pathds_id+'',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 根据数据集 ID 删除数据集
  * @param {String} [pathds_id] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async delete_dataset(pathds_id,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'delete',
        url:'/api/v1/datasets/'+pathds_id+'',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 获取指定数据集的 Pandas 类型样本数据,用于前端展示预览，可以通过start和end参数控制获取多少数据
  * @param {String} [pathds_id] 
  * @param {Number} [start] 
  * @param {Number} [end] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async get_pandas_data(pathds_id,start,end,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/datasets/pandas_type_sample/'+pathds_id+'',
        data:{},
        params:{start,end},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 获取指定数据集的文件类型样本数据，用于前端展示下载，可以是图片、文本等
  * @param {String} [pathds_id] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async get_file_type_data(pathds_id,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/datasets/file_type_sample/'+pathds_id+'',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 获取指定数据集的文件预览内容，支持json、jsonl和parquet格式
  * @param {String} [pathds_id] 
  * @param {Number} [num_lines] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async get_dataset_preview(pathds_id,num_lines,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/datasets/preview/'+pathds_id+'',
        data:{},
        params:{num_lines},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 获取指定数据集的列名，支持json、jsonl和parquet格式
  * @param {String} [pathds_id] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async get_dataset_columns(pathds_id,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/datasets/columns/'+pathds_id+'',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
}

// class datasets static method properties bind
/**
* @description list_datasets url链接，包含baseURL
*/
datasets.list_datasets.fullPath=`${axios.defaults.baseURL}/api/v1/datasets/`
/**
* @description list_datasets url链接，不包含baseURL
*/
datasets.list_datasets.path=`/api/v1/datasets/`
/**
* @description register_dataset url链接，包含baseURL
*/
datasets.register_dataset.fullPath=`${axios.defaults.baseURL}/api/v1/datasets/`
/**
* @description register_dataset url链接，不包含baseURL
*/
datasets.register_dataset.path=`/api/v1/datasets/`
/**
* @description get_dataset url链接，包含baseURL
*/
datasets.get_dataset.fullPath=`${axios.defaults.baseURL}/api/v1/datasets/{ds_id}`
/**
* @description get_dataset url链接，不包含baseURL
*/
datasets.get_dataset.path=`/api/v1/datasets/{ds_id}`
/**
* @description delete_dataset url链接，包含baseURL
*/
datasets.delete_dataset.fullPath=`${axios.defaults.baseURL}/api/v1/datasets/{ds_id}`
/**
* @description delete_dataset url链接，不包含baseURL
*/
datasets.delete_dataset.path=`/api/v1/datasets/{ds_id}`
/**
* @description get_pandas_data url链接，包含baseURL
*/
datasets.get_pandas_data.fullPath=`${axios.defaults.baseURL}/api/v1/datasets/pandas_type_sample/{ds_id}`
/**
* @description get_pandas_data url链接，不包含baseURL
*/
datasets.get_pandas_data.path=`/api/v1/datasets/pandas_type_sample/{ds_id}`
/**
* @description get_file_type_data url链接，包含baseURL
*/
datasets.get_file_type_data.fullPath=`${axios.defaults.baseURL}/api/v1/datasets/file_type_sample/{ds_id}`
/**
* @description get_file_type_data url链接，不包含baseURL
*/
datasets.get_file_type_data.path=`/api/v1/datasets/file_type_sample/{ds_id}`
/**
* @description get_dataset_preview url链接，包含baseURL
*/
datasets.get_dataset_preview.fullPath=`${axios.defaults.baseURL}/api/v1/datasets/preview/{ds_id}`
/**
* @description get_dataset_preview url链接，不包含baseURL
*/
datasets.get_dataset_preview.path=`/api/v1/datasets/preview/{ds_id}`
/**
* @description get_dataset_columns url链接，包含baseURL
*/
datasets.get_dataset_columns.fullPath=`${axios.defaults.baseURL}/api/v1/datasets/columns/{ds_id}`
/**
* @description get_dataset_columns url链接，不包含baseURL
*/
datasets.get_dataset_columns.path=`/api/v1/datasets/columns/{ds_id}`

export class operators {
 
  /**
  * @summary 返回注册算子列表 (简化版)
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async list_operators(cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/operators/',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 返回所有算子详细信息 (首次扫描生成，其后从缓存读取)
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async list_operators_details(cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/operators/details',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 根据算子名称返回单个算子的详细信息
  * @param {String} [pathop_name] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async get_operator_detail_by_name(pathop_name,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/operators/details/'+pathop_name+'',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
}

// class operators static method properties bind
/**
* @description list_operators url链接，包含baseURL
*/
operators.list_operators.fullPath=`${axios.defaults.baseURL}/api/v1/operators/`
/**
* @description list_operators url链接，不包含baseURL
*/
operators.list_operators.path=`/api/v1/operators/`
/**
* @description list_operators_details url链接，包含baseURL
*/
operators.list_operators_details.fullPath=`${axios.defaults.baseURL}/api/v1/operators/details`
/**
* @description list_operators_details url链接，不包含baseURL
*/
operators.list_operators_details.path=`/api/v1/operators/details`
/**
* @description get_operator_detail_by_name url链接，包含baseURL
*/
operators.get_operator_detail_by_name.fullPath=`${axios.defaults.baseURL}/api/v1/operators/details/{op_name}`
/**
* @description get_operator_detail_by_name url链接，不包含baseURL
*/
operators.get_operator_detail_by_name.path=`/api/v1/operators/details/{op_name}`

export class tasks {
 
  /**
  * @summary 列出所有任务，支持按状态和执行器类型过滤
  * @param {undefined} [status] 过滤状态: pending/running/success/failed/cancelled
  * @param {undefined} [executor_type] 过滤执行器类型: operator/pipeline
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async list_tasks(status,executor_type,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/tasks/',
        data:{},
        params:{status,executor_type},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 创建新任务
  * @param {UserModel.TaskCreate} [taskcreate] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async create_task(taskcreate,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'post',
        url:'/api/v1/tasks/',
        data:taskcreate,
        params:{},
        headers:{
          "Content-Type":"application/json"
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 获取任务统计信息
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async get_task_statistics(cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/tasks/statistics',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 获取指定任务详情
  * @param {String} [pathtask_id] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async get_task(pathtask_id,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/tasks/'+pathtask_id+'',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 更新任务状态和信息
  * @param {String} [pathtask_id] 
  * @param {UserModel.TaskUpdate} [taskupdate] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async update_task(pathtask_id,taskupdate,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'patch',
        url:'/api/v1/tasks/'+pathtask_id+'',
        data:taskupdate,
        params:{},
        headers:{
          "Content-Type":"application/json"
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 删除任务
  * @param {String} [pathtask_id] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async delete_task(pathtask_id,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'delete',
        url:'/api/v1/tasks/'+pathtask_id+'',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 启动任务（将状态设为running）
  * @param {String} [pathtask_id] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async start_task(pathtask_id,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'post',
        url:'/api/v1/tasks/'+pathtask_id+'/start',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 完成任务（将状态设为success）
  * @param {String} [pathtask_id] 
  * @param {undefined} [output_id] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async complete_task(pathtask_id,output_id,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'post',
        url:'/api/v1/tasks/'+pathtask_id+'/complete',
        data:{},
        params:{output_id},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 标记任务失败
  * @param {String} [pathtask_id] 
  * @param {undefined} [error_message] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async fail_task(pathtask_id,error_message,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'post',
        url:'/api/v1/tasks/'+pathtask_id+'/fail',
        data:{},
        params:{error_message},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 取消任务
  * @param {String} [pathtask_id] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async cancel_task(pathtask_id,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'post',
        url:'/api/v1/tasks/'+pathtask_id+'/cancel',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
}

// class tasks static method properties bind
/**
* @description list_tasks url链接，包含baseURL
*/
tasks.list_tasks.fullPath=`${axios.defaults.baseURL}/api/v1/tasks/`
/**
* @description list_tasks url链接，不包含baseURL
*/
tasks.list_tasks.path=`/api/v1/tasks/`
/**
* @description create_task url链接，包含baseURL
*/
tasks.create_task.fullPath=`${axios.defaults.baseURL}/api/v1/tasks/`
/**
* @description create_task url链接，不包含baseURL
*/
tasks.create_task.path=`/api/v1/tasks/`
/**
* @description get_task_statistics url链接，包含baseURL
*/
tasks.get_task_statistics.fullPath=`${axios.defaults.baseURL}/api/v1/tasks/statistics`
/**
* @description get_task_statistics url链接，不包含baseURL
*/
tasks.get_task_statistics.path=`/api/v1/tasks/statistics`
/**
* @description get_task url链接，包含baseURL
*/
tasks.get_task.fullPath=`${axios.defaults.baseURL}/api/v1/tasks/{task_id}`
/**
* @description get_task url链接，不包含baseURL
*/
tasks.get_task.path=`/api/v1/tasks/{task_id}`
/**
* @description update_task url链接，包含baseURL
*/
tasks.update_task.fullPath=`${axios.defaults.baseURL}/api/v1/tasks/{task_id}`
/**
* @description update_task url链接，不包含baseURL
*/
tasks.update_task.path=`/api/v1/tasks/{task_id}`
/**
* @description delete_task url链接，包含baseURL
*/
tasks.delete_task.fullPath=`${axios.defaults.baseURL}/api/v1/tasks/{task_id}`
/**
* @description delete_task url链接，不包含baseURL
*/
tasks.delete_task.path=`/api/v1/tasks/{task_id}`
/**
* @description start_task url链接，包含baseURL
*/
tasks.start_task.fullPath=`${axios.defaults.baseURL}/api/v1/tasks/{task_id}/start`
/**
* @description start_task url链接，不包含baseURL
*/
tasks.start_task.path=`/api/v1/tasks/{task_id}/start`
/**
* @description complete_task url链接，包含baseURL
*/
tasks.complete_task.fullPath=`${axios.defaults.baseURL}/api/v1/tasks/{task_id}/complete`
/**
* @description complete_task url链接，不包含baseURL
*/
tasks.complete_task.path=`/api/v1/tasks/{task_id}/complete`
/**
* @description fail_task url链接，包含baseURL
*/
tasks.fail_task.fullPath=`${axios.defaults.baseURL}/api/v1/tasks/{task_id}/fail`
/**
* @description fail_task url链接，不包含baseURL
*/
tasks.fail_task.path=`/api/v1/tasks/{task_id}/fail`
/**
* @description cancel_task url链接，包含baseURL
*/
tasks.cancel_task.fullPath=`${axios.defaults.baseURL}/api/v1/tasks/{task_id}/cancel`
/**
* @description cancel_task url链接，不包含baseURL
*/
tasks.cancel_task.path=`/api/v1/tasks/{task_id}/cancel`

export class pipelines {
 
  /**
  * @summary 列出所有Pipeline执行记录
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async list_executions(cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/pipelines/executions',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 获取Pipeline执行结果
  * @param {String} [pathexecution_id] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async get_execution_result(pathexecution_id,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/pipelines/execution/'+pathexecution_id+'',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 返回所有注册的Pipeline列表
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async list_pipelines(cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/pipelines/',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 创建一个新的Pipeline
  * @param {UserModel.PipelineIn} [pipelinein] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async create_pipeline(pipelinein,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'post',
        url:'/api/v1/pipelines/',
        data:pipelinein,
        params:{},
        headers:{
          "Content-Type":"application/json"
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 返回所有预置(template) Pipeline列表
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async list_template_pipelines(cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/pipelines/templates',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 根据ID获取Pipeline详情
  * @param {String} [pathpipeline_id] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async get_pipeline(pathpipeline_id,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/pipelines/'+pathpipeline_id+'',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 更新指定的Pipeline
  * @param {String} [pathpipeline_id] 
  * @param {UserModel.PipelineUpdateIn} [pipelineupdatein] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async update_pipeline(pathpipeline_id,pipelineupdatein,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'put',
        url:'/api/v1/pipelines/'+pathpipeline_id+'',
        data:pipelineupdatein,
        params:{},
        headers:{
          "Content-Type":"application/json"
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 删除指定的Pipeline
  * @param {String} [pathpipeline_id] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async delete_pipeline(pathpipeline_id,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'delete',
        url:'/api/v1/pipelines/'+pathpipeline_id+'',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 执行Pipeline
  * @param {undefined} [pipeline_id] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async execute_pipeline(pipeline_id,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'post',
        url:'/api/v1/pipelines/execute',
        data:{},
        params:{pipeline_id},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
}

// class pipelines static method properties bind
/**
* @description list_executions url链接，包含baseURL
*/
pipelines.list_executions.fullPath=`${axios.defaults.baseURL}/api/v1/pipelines/executions`
/**
* @description list_executions url链接，不包含baseURL
*/
pipelines.list_executions.path=`/api/v1/pipelines/executions`
/**
* @description get_execution_result url链接，包含baseURL
*/
pipelines.get_execution_result.fullPath=`${axios.defaults.baseURL}/api/v1/pipelines/execution/{execution_id}`
/**
* @description get_execution_result url链接，不包含baseURL
*/
pipelines.get_execution_result.path=`/api/v1/pipelines/execution/{execution_id}`
/**
* @description list_pipelines url链接，包含baseURL
*/
pipelines.list_pipelines.fullPath=`${axios.defaults.baseURL}/api/v1/pipelines/`
/**
* @description list_pipelines url链接，不包含baseURL
*/
pipelines.list_pipelines.path=`/api/v1/pipelines/`
/**
* @description create_pipeline url链接，包含baseURL
*/
pipelines.create_pipeline.fullPath=`${axios.defaults.baseURL}/api/v1/pipelines/`
/**
* @description create_pipeline url链接，不包含baseURL
*/
pipelines.create_pipeline.path=`/api/v1/pipelines/`
/**
* @description list_template_pipelines url链接，包含baseURL
*/
pipelines.list_template_pipelines.fullPath=`${axios.defaults.baseURL}/api/v1/pipelines/templates`
/**
* @description list_template_pipelines url链接，不包含baseURL
*/
pipelines.list_template_pipelines.path=`/api/v1/pipelines/templates`
/**
* @description get_pipeline url链接，包含baseURL
*/
pipelines.get_pipeline.fullPath=`${axios.defaults.baseURL}/api/v1/pipelines/{pipeline_id}`
/**
* @description get_pipeline url链接，不包含baseURL
*/
pipelines.get_pipeline.path=`/api/v1/pipelines/{pipeline_id}`
/**
* @description update_pipeline url链接，包含baseURL
*/
pipelines.update_pipeline.fullPath=`${axios.defaults.baseURL}/api/v1/pipelines/{pipeline_id}`
/**
* @description update_pipeline url链接，不包含baseURL
*/
pipelines.update_pipeline.path=`/api/v1/pipelines/{pipeline_id}`
/**
* @description delete_pipeline url链接，包含baseURL
*/
pipelines.delete_pipeline.fullPath=`${axios.defaults.baseURL}/api/v1/pipelines/{pipeline_id}`
/**
* @description delete_pipeline url链接，不包含baseURL
*/
pipelines.delete_pipeline.path=`/api/v1/pipelines/{pipeline_id}`
/**
* @description execute_pipeline url链接，包含baseURL
*/
pipelines.execute_pipeline.fullPath=`${axios.defaults.baseURL}/api/v1/pipelines/execute`
/**
* @description execute_pipeline url链接，不包含baseURL
*/
pipelines.execute_pipeline.path=`/api/v1/pipelines/execute`

export class prompts {
 
  /**
  * @summary 查看所有算子及其对应的 Prompt 列表
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async get_operator_prompt_mapping_api_v1_prompts_operator_mapping_get(cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/prompts/operator-mapping',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 查看所有 prompt 的信息（operator, class string, category）
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async get_prompt_info_api_v1_prompts_prompt_info_get(cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/prompts/prompt-info',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 根据算子名称获取对应的 Prompt 列表
  * @param {String} [pathoperator_name] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async get_prompts_api_v1_prompts__operator_name__get(pathoperator_name,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/prompts/'+pathoperator_name+'',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 根据 Prompt 名称返回 Prompt 类的源码
  * @param {String} [pathprompt_name] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async get_prompt_source_api_v1_prompts_source__prompt_name__get(pathprompt_name,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/prompts/source/'+pathprompt_name+'',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
}

// class prompts static method properties bind
/**
* @description get_operator_prompt_mapping_api_v1_prompts_operator_mapping_get url链接，包含baseURL
*/
prompts.get_operator_prompt_mapping_api_v1_prompts_operator_mapping_get.fullPath=`${axios.defaults.baseURL}/api/v1/prompts/operator-mapping`
/**
* @description get_operator_prompt_mapping_api_v1_prompts_operator_mapping_get url链接，不包含baseURL
*/
prompts.get_operator_prompt_mapping_api_v1_prompts_operator_mapping_get.path=`/api/v1/prompts/operator-mapping`
/**
* @description get_prompt_info_api_v1_prompts_prompt_info_get url链接，包含baseURL
*/
prompts.get_prompt_info_api_v1_prompts_prompt_info_get.fullPath=`${axios.defaults.baseURL}/api/v1/prompts/prompt-info`
/**
* @description get_prompt_info_api_v1_prompts_prompt_info_get url链接，不包含baseURL
*/
prompts.get_prompt_info_api_v1_prompts_prompt_info_get.path=`/api/v1/prompts/prompt-info`
/**
* @description get_prompts_api_v1_prompts__operator_name__get url链接，包含baseURL
*/
prompts.get_prompts_api_v1_prompts__operator_name__get.fullPath=`${axios.defaults.baseURL}/api/v1/prompts/{operator_name}`
/**
* @description get_prompts_api_v1_prompts__operator_name__get url链接，不包含baseURL
*/
prompts.get_prompts_api_v1_prompts__operator_name__get.path=`/api/v1/prompts/{operator_name}`
/**
* @description get_prompt_source_api_v1_prompts_source__prompt_name__get url链接，包含baseURL
*/
prompts.get_prompt_source_api_v1_prompts_source__prompt_name__get.fullPath=`${axios.defaults.baseURL}/api/v1/prompts/source/{prompt_name}`
/**
* @description get_prompt_source_api_v1_prompts_source__prompt_name__get url链接，不包含baseURL
*/
prompts.get_prompt_source_api_v1_prompts_source__prompt_name__get.path=`/api/v1/prompts/source/{prompt_name}`

export class serving {
 
  /**
  * @summary List Serving Instances
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async list_serving_instances_api_v1_serving__get(cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/serving/',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 创建新的 Serving 实例
  * @param {String} [name] 
  * @param {String} [cls_name] 
  * @param {array} [array] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async create_serving_instance(name,cls_name,array,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'post',
        url:'/api/v1/serving/',
        data:array,
        params:{name,cls_name},
        headers:{
          "Content-Type":"application/json"
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 获取所有可用Serving类定义
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async list_serving_classes(cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/serving/classes',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 获取指定 Serving 实例的详细信息
  * @param {String} [pathid] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async get_serving_detail(pathid,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/serving/'+pathid+'',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 更新 Serving 实例
  * @param {String} [pathid] 
  * @param {UserModel.ServingUpdateSchema} [servingupdateschema] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async update_serving_instance(pathid,servingupdateschema,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'put',
        url:'/api/v1/serving/'+pathid+'',
        data:servingupdateschema,
        params:{},
        headers:{
          "Content-Type":"application/json"
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 删除 Serving 实例
  * @param {String} [pathid] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async delete_serving_instance(pathid,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'delete',
        url:'/api/v1/serving/'+pathid+'',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 测试指定 Serving 实例的响应
  * @param {String} [pathid] 
  * @param {UserModel.ServingTestSchema} [servingtestschema] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async test_serving_instance(pathid,servingtestschema,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'post',
        url:'/api/v1/serving/'+pathid+'/test',
        data:servingtestschema,
        params:{},
        headers:{
          "Content-Type":"application/json"
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
}

// class serving static method properties bind
/**
* @description list_serving_instances_api_v1_serving__get url链接，包含baseURL
*/
serving.list_serving_instances_api_v1_serving__get.fullPath=`${axios.defaults.baseURL}/api/v1/serving/`
/**
* @description list_serving_instances_api_v1_serving__get url链接，不包含baseURL
*/
serving.list_serving_instances_api_v1_serving__get.path=`/api/v1/serving/`
/**
* @description create_serving_instance url链接，包含baseURL
*/
serving.create_serving_instance.fullPath=`${axios.defaults.baseURL}/api/v1/serving/`
/**
* @description create_serving_instance url链接，不包含baseURL
*/
serving.create_serving_instance.path=`/api/v1/serving/`
/**
* @description list_serving_classes url链接，包含baseURL
*/
serving.list_serving_classes.fullPath=`${axios.defaults.baseURL}/api/v1/serving/classes`
/**
* @description list_serving_classes url链接，不包含baseURL
*/
serving.list_serving_classes.path=`/api/v1/serving/classes`
/**
* @description get_serving_detail url链接，包含baseURL
*/
serving.get_serving_detail.fullPath=`${axios.defaults.baseURL}/api/v1/serving/{id}`
/**
* @description get_serving_detail url链接，不包含baseURL
*/
serving.get_serving_detail.path=`/api/v1/serving/{id}`
/**
* @description update_serving_instance url链接，包含baseURL
*/
serving.update_serving_instance.fullPath=`${axios.defaults.baseURL}/api/v1/serving/{id}`
/**
* @description update_serving_instance url链接，不包含baseURL
*/
serving.update_serving_instance.path=`/api/v1/serving/{id}`
/**
* @description delete_serving_instance url链接，包含baseURL
*/
serving.delete_serving_instance.fullPath=`${axios.defaults.baseURL}/api/v1/serving/{id}`
/**
* @description delete_serving_instance url链接，不包含baseURL
*/
serving.delete_serving_instance.path=`/api/v1/serving/{id}`
/**
* @description test_serving_instance url链接，包含baseURL
*/
serving.test_serving_instance.fullPath=`${axios.defaults.baseURL}/api/v1/serving/{id}/test`
/**
* @description test_serving_instance url链接，不包含baseURL
*/
serving.test_serving_instance.path=`/api/v1/serving/{id}/test`

export class text2sql_database {
 
  /**
  * @summary 列出所有已上传的sqlite数据库
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async list_databases(cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/text2sql_database/',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 获取指定db详情
  * @param {String} [pathdb_id] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async get_database_detail(pathdb_id,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/text2sql_database/'+pathdb_id+'',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 删除数据库
  * @param {String} [pathdb_id] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async delete_database(pathdb_id,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'delete',
        url:'/api/v1/text2sql_database/'+pathdb_id+'',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 上传一个sqlite数据库文件并注册
  * @param {UserModel.Body_upload_sqlite_database} [body_upload_sqlite_database] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async upload_sqlite_database(body_upload_sqlite_database,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'post',
        url:'/api/v1/text2sql_database/upload',
        data:body_upload_sqlite_database,
        params:{},
        headers:{
          "Content-Type":"multipart/form-data"
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
}

// class text2sql_database static method properties bind
/**
* @description list_databases url链接，包含baseURL
*/
text2sql_database.list_databases.fullPath=`${axios.defaults.baseURL}/api/v1/text2sql_database/`
/**
* @description list_databases url链接，不包含baseURL
*/
text2sql_database.list_databases.path=`/api/v1/text2sql_database/`
/**
* @description get_database_detail url链接，包含baseURL
*/
text2sql_database.get_database_detail.fullPath=`${axios.defaults.baseURL}/api/v1/text2sql_database/{db_id}`
/**
* @description get_database_detail url链接，不包含baseURL
*/
text2sql_database.get_database_detail.path=`/api/v1/text2sql_database/{db_id}`
/**
* @description delete_database url链接，包含baseURL
*/
text2sql_database.delete_database.fullPath=`${axios.defaults.baseURL}/api/v1/text2sql_database/{db_id}`
/**
* @description delete_database url链接，不包含baseURL
*/
text2sql_database.delete_database.path=`/api/v1/text2sql_database/{db_id}`
/**
* @description upload_sqlite_database url链接，包含baseURL
*/
text2sql_database.upload_sqlite_database.fullPath=`${axios.defaults.baseURL}/api/v1/text2sql_database/upload`
/**
* @description upload_sqlite_database url链接，不包含baseURL
*/
text2sql_database.upload_sqlite_database.path=`/api/v1/text2sql_database/upload`

export class text2sql_database_manager {
 
  /**
  * @summary 列出所有DatabaseManager配置
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async list_text2sql_database_managers(cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/text2sql_database_manager/',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 创建新的DatabaseManager
  * @param {UserModel.Text2SQLDatabaseManagerCreateSchema} [text2sqldatabasemanagercreateschema] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async create_text2sql_database_manager(text2sqldatabasemanagercreateschema,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'post',
        url:'/api/v1/text2sql_database_manager/',
        data:text2sqldatabasemanagercreateschema,
        params:{},
        headers:{
          "Content-Type":"application/json"
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 获取所有可用DatabaseManager类定义
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async list_text2sql_database_manager_classes(cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/text2sql_database_manager/classes',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 获取指定DatabaseManager配置详情
  * @param {String} [pathmgr_id] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async get_text2sql_database_manager_detail(pathmgr_id,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'get',
        url:'/api/v1/text2sql_database_manager/'+pathmgr_id+'',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 更新DatabaseManager
  * @param {String} [pathmgr_id] 
  * @param {UserModel.Text2SQLDatabaseManagerUpdateSchema} [text2sqldatabasemanagerupdateschema] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async update_text2sql_database_manager(pathmgr_id,text2sqldatabasemanagerupdateschema,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'put',
        url:'/api/v1/text2sql_database_manager/'+pathmgr_id+'',
        data:text2sqldatabasemanagerupdateschema,
        params:{},
        headers:{
          "Content-Type":"application/json"
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
 
  /**
  * @summary 删除DatabaseManager
  * @param {String} [pathmgr_id] 
  * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
  * @param {Function} [uploadProgress] 上传回调函数
  * @param {Function} [downloadProgress] 下载回调函数
  */
  static async delete_text2sql_database_manager(pathmgr_id,cancelSource,uploadProgress,downloadProgress){
    return await new Promise((resolve,reject)=>{
      let responseType = "json";
      let options = {
        method:'delete',
        url:'/api/v1/text2sql_database_manager/'+pathmgr_id+'',
        data:{},
        params:{},
        headers:{
          "Content-Type":""
        },
        onUploadProgress:uploadProgress,
        onDownloadProgress:downloadProgress
      }
      // support wechat mini program
      if (cancelSource!=undefined){
        options.cancelToken = cancelSource.token
      }
      if (responseType != "json"){
        options.responseType = responseType;
      }
      axios(options)
      .then(res=>{
        if (res.config.responseType=="blob"){
          resolve(new Blob([res.data],{
            type: res.headers["content-type"].split(";")[0]
          }))
        }else{
          resolve(res.data);
          return res.data
        }
      }).catch(err=>{
        if (err.response){
          if (err.response.data)
            reject(err.response.data)
          else
            reject(err.response);
        }else{
          reject(err)
        }
      })
    })
  }
}

// class text2sql_database_manager static method properties bind
/**
* @description list_text2sql_database_managers url链接，包含baseURL
*/
text2sql_database_manager.list_text2sql_database_managers.fullPath=`${axios.defaults.baseURL}/api/v1/text2sql_database_manager/`
/**
* @description list_text2sql_database_managers url链接，不包含baseURL
*/
text2sql_database_manager.list_text2sql_database_managers.path=`/api/v1/text2sql_database_manager/`
/**
* @description create_text2sql_database_manager url链接，包含baseURL
*/
text2sql_database_manager.create_text2sql_database_manager.fullPath=`${axios.defaults.baseURL}/api/v1/text2sql_database_manager/`
/**
* @description create_text2sql_database_manager url链接，不包含baseURL
*/
text2sql_database_manager.create_text2sql_database_manager.path=`/api/v1/text2sql_database_manager/`
/**
* @description list_text2sql_database_manager_classes url链接，包含baseURL
*/
text2sql_database_manager.list_text2sql_database_manager_classes.fullPath=`${axios.defaults.baseURL}/api/v1/text2sql_database_manager/classes`
/**
* @description list_text2sql_database_manager_classes url链接，不包含baseURL
*/
text2sql_database_manager.list_text2sql_database_manager_classes.path=`/api/v1/text2sql_database_manager/classes`
/**
* @description get_text2sql_database_manager_detail url链接，包含baseURL
*/
text2sql_database_manager.get_text2sql_database_manager_detail.fullPath=`${axios.defaults.baseURL}/api/v1/text2sql_database_manager/{mgr_id}`
/**
* @description get_text2sql_database_manager_detail url链接，不包含baseURL
*/
text2sql_database_manager.get_text2sql_database_manager_detail.path=`/api/v1/text2sql_database_manager/{mgr_id}`
/**
* @description update_text2sql_database_manager url链接，包含baseURL
*/
text2sql_database_manager.update_text2sql_database_manager.fullPath=`${axios.defaults.baseURL}/api/v1/text2sql_database_manager/{mgr_id}`
/**
* @description update_text2sql_database_manager url链接，不包含baseURL
*/
text2sql_database_manager.update_text2sql_database_manager.path=`/api/v1/text2sql_database_manager/{mgr_id}`
/**
* @description delete_text2sql_database_manager url链接，包含baseURL
*/
text2sql_database_manager.delete_text2sql_database_manager.fullPath=`${axios.defaults.baseURL}/api/v1/text2sql_database_manager/{mgr_id}`
/**
* @description delete_text2sql_database_manager url链接，不包含baseURL
*/
text2sql_database_manager.delete_text2sql_database_manager.path=`/api/v1/text2sql_database_manager/{mgr_id}`
