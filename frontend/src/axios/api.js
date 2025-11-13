/* eslint-disable */
// More information: https://github.com/minskiter/openapijs
import axios from './config.js'
import * as Axios from 'axios'
import * as UserModel from './model.js'

// fix vite error.
const CancelTokenSource = Axios.CancelTokenSource;


export class datasets {
 
  /**
  * @summary 返回目前所有注册的数据集列表
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

export class operators {
 
  /**
  * @summary 返回目前所有注册的算子列表
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
