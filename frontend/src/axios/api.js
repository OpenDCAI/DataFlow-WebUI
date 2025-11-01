/* eslint-disable */
// More information: https://github.com/minskiter/openapijs
import axios from './config.js'
import * as Axios from 'axios'
import * as UserModel from './model.js'

// fix vite error.
const CancelTokenSource = Axios.CancelTokenSource;


export class Web {

    /**
    * @summary Get the status of the HTML scanning
    * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
    * @param {Function} [uploadProgress] 上传回调函数
    * @param {Function} [downloadProgress] 下载回调函数
    */
    static async GetScanStatus(cancelSource, uploadProgress, downloadProgress) {
        return await new Promise((resolve, reject) => {
            let responseType = "json";
            let options = {
                method: 'get',
                url: '/scan_status',
                data: {},
                params: {},
                headers: {
                    "Content-Type": ""
                },
                onUploadProgress: uploadProgress,
                onDownloadProgress: downloadProgress
            }
            // support wechat mini program
            if (cancelSource != undefined) {
                options.cancelToken = cancelSource.token
            }
            if (responseType != "json") {
                options.responseType = responseType;
            }
            axios(options)
                .then(res => {
                    if (res.config.responseType == "blob") {
                        resolve(new Blob([res.data], {
                            type: res.headers["content-type"].split(";")[0]
                        }))
                    } else {
                        resolve(res.data);
                        return res.data
                    }
                }).catch(err => {
                    if (err.response) {
                        if (err.response.data)
                            reject(err.response.data)
                        else
                            reject(err.response);
                    } else {
                        reject(err)
                    }
                })
        })
    }

    /**
    * @summary List all HTML files
    * @param {Number} [offset] 
    * @param {Number} [limit] 
    * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
    * @param {Function} [uploadProgress] 上传回调函数
    * @param {Function} [downloadProgress] 下载回调函数
    */
    static async ListHTMLFiles(offset, limit, cancelSource, uploadProgress, downloadProgress) {
        return await new Promise((resolve, reject) => {
            let responseType = "json";
            let options = {
                method: 'get',
                url: '/list_html',
                data: {},
                params: { offset, limit },
                headers: {
                    "Content-Type": ""
                },
                onUploadProgress: uploadProgress,
                onDownloadProgress: downloadProgress
            }
            // support wechat mini program
            if (cancelSource != undefined) {
                options.cancelToken = cancelSource.token
            }
            if (responseType != "json") {
                options.responseType = responseType;
            }
            axios(options)
                .then(res => {
                    if (res.config.responseType == "blob") {
                        resolve(new Blob([res.data], {
                            type: res.headers["content-type"].split(";")[0]
                        }))
                    } else {
                        resolve(res.data);
                        return res.data
                    }
                }).catch(err => {
                    if (err.response) {
                        if (err.response.data)
                            reject(err.response.data)
                        else
                            reject(err.response);
                    } else {
                        reject(err)
                    }
                })
        })
    }

    /**
    * @summary Get the count of all HTML files
    * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
    * @param {Function} [uploadProgress] 上传回调函数
    * @param {Function} [downloadProgress] 下载回调函数
    */
    static async GetHTMLFileCount(cancelSource, uploadProgress, downloadProgress) {
        return await new Promise((resolve, reject) => {
            let responseType = "json";
            let options = {
                method: 'get',
                url: '/list_html_count',
                data: {},
                params: {},
                headers: {
                    "Content-Type": ""
                },
                onUploadProgress: uploadProgress,
                onDownloadProgress: downloadProgress
            }
            // support wechat mini program
            if (cancelSource != undefined) {
                options.cancelToken = cancelSource.token
            }
            if (responseType != "json") {
                options.responseType = responseType;
            }
            axios(options)
                .then(res => {
                    if (res.config.responseType == "blob") {
                        resolve(new Blob([res.data], {
                            type: res.headers["content-type"].split(";")[0]
                        }))
                    } else {
                        resolve(res.data);
                        return res.data
                    }
                }).catch(err => {
                    if (err.response) {
                        if (err.response.data)
                            reject(err.response.data)
                        else
                            reject(err.response);
                    } else {
                        reject(err)
                    }
                })
        })
    }

    /**
    * @summary Get the web page with the given name
    * @param {String} [name] Name of the web page
    * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
    * @param {Function} [uploadProgress] 上传回调函数
    * @param {Function} [downloadProgress] 下载回调函数
    */
    static async GetWeb(name, cancelSource, uploadProgress, downloadProgress) {
        return await new Promise((resolve, reject) => {
            let responseType = "json";
            let options = {
                method: 'get',
                url: '/web',
                data: {},
                params: { name },
                headers: {
                    "Content-Type": ""
                },
                onUploadProgress: uploadProgress,
                onDownloadProgress: downloadProgress
            }
            // support wechat mini program
            if (cancelSource != undefined) {
                options.cancelToken = cancelSource.token
            }
            if (responseType != "json") {
                options.responseType = responseType;
            }
            axios(options)
                .then(res => {
                    if (res.config.responseType == "blob") {
                        resolve(new Blob([res.data], {
                            type: res.headers["content-type"].split(";")[0]
                        }))
                    } else {
                        resolve(res.data);
                        return res.data
                    }
                }).catch(err => {
                    if (err.response) {
                        if (err.response.data)
                            reject(err.response.data)
                        else
                            reject(err.response);
                    } else {
                        reject(err)
                    }
                })
        })
    }

    /**
    * @summary Get the web page with the given name, and rewrite the static path
    * @param {undefined} [name] 
    * @param {undefined} [rewrite_from] 
    * @param {undefined} [rewrite_to] 
    * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
    * @param {Function} [uploadProgress] 上传回调函数
    * @param {Function} [downloadProgress] 下载回调函数
    */
    static async GetWebWithRewrite(name, rewrite_from, rewrite_to, cancelSource, uploadProgress, downloadProgress) {
        return await new Promise((resolve, reject) => {
            let responseType = "json";
            let options = {
                method: 'get',
                url: '/web/rewrite',
                data: {},
                params: { name, rewrite_from, rewrite_to },
                headers: {
                    "Content-Type": ""
                },
                onUploadProgress: uploadProgress,
                onDownloadProgress: downloadProgress
            }
            // support wechat mini program
            if (cancelSource != undefined) {
                options.cancelToken = cancelSource.token
            }
            if (responseType != "json") {
                options.responseType = responseType;
            }
            axios(options)
                .then(res => {
                    if (res.config.responseType == "blob") {
                        resolve(new Blob([res.data], {
                            type: res.headers["content-type"].split(";")[0]
                        }))
                    } else {
                        resolve(res.data);
                        return res.data
                    }
                }).catch(err => {
                    if (err.response) {
                        if (err.response.data)
                            reject(err.response.data)
                        else
                            reject(err.response);
                    } else {
                        reject(err)
                    }
                })
        })
    }

    /**
    * @summary Get a quality job
    * @param {Number} [job_num] 
    * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
    * @param {Function} [uploadProgress] 上传回调函数
    * @param {Function} [downloadProgress] 下载回调函数
    */
    static async GetWebQualityJob(job_num, cancelSource, uploadProgress, downloadProgress) {
        return await new Promise((resolve, reject) => {
            let responseType = "json";
            let options = {
                method: 'get',
                url: '/web/quality/job/get',
                data: {},
                params: { job_num },
                headers: {
                    "Content-Type": ""
                },
                onUploadProgress: uploadProgress,
                onDownloadProgress: downloadProgress
            }
            // support wechat mini program
            if (cancelSource != undefined) {
                options.cancelToken = cancelSource.token
            }
            if (responseType != "json") {
                options.responseType = responseType;
            }
            axios(options)
                .then(res => {
                    if (res.config.responseType == "blob") {
                        resolve(new Blob([res.data], {
                            type: res.headers["content-type"].split(";")[0]
                        }))
                    } else {
                        resolve(res.data);
                        return res.data
                    }
                }).catch(err => {
                    if (err.response) {
                        if (err.response.data)
                            reject(err.response.data)
                        else
                            reject(err.response);
                    } else {
                        reject(err)
                    }
                })
        })
    }

    /**
    * @summary Submit a quality job
    * @param {array} [array] 
    * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
    * @param {Function} [uploadProgress] 上传回调函数
    * @param {Function} [downloadProgress] 下载回调函数
    */
    static async SubmitWebQualityJob(array, cancelSource, uploadProgress, downloadProgress) {
        return await new Promise((resolve, reject) => {
            let responseType = "json";
            let options = {
                method: 'post',
                url: '/web/quality/job/submit',
                data: array,
                params: {},
                headers: {
                    "Content-Type": "application/json"
                },
                onUploadProgress: uploadProgress,
                onDownloadProgress: downloadProgress
            }
            // support wechat mini program
            if (cancelSource != undefined) {
                options.cancelToken = cancelSource.token
            }
            if (responseType != "json") {
                options.responseType = responseType;
            }
            axios(options)
                .then(res => {
                    if (res.config.responseType == "blob") {
                        resolve(new Blob([res.data], {
                            type: res.headers["content-type"].split(";")[0]
                        }))
                    } else {
                        resolve(res.data);
                        return res.data
                    }
                }).catch(err => {
                    if (err.response) {
                        if (err.response.data)
                            reject(err.response.data)
                        else
                            reject(err.response);
                    } else {
                        reject(err)
                    }
                })
        })
    }

    /**
    * @summary Get quality jobs status
    * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
    * @param {Function} [uploadProgress] 上传回调函数
    * @param {Function} [downloadProgress] 下载回调函数
    */
    static async GetWebQualityJobStatus(cancelSource, uploadProgress, downloadProgress) {
        return await new Promise((resolve, reject) => {
            let responseType = "json";
            let options = {
                method: 'get',
                url: '/web/quality/job/status',
                data: {},
                params: {},
                headers: {
                    "Content-Type": ""
                },
                onUploadProgress: uploadProgress,
                onDownloadProgress: downloadProgress
            }
            // support wechat mini program
            if (cancelSource != undefined) {
                options.cancelToken = cancelSource.token
            }
            if (responseType != "json") {
                options.responseType = responseType;
            }
            axios(options)
                .then(res => {
                    if (res.config.responseType == "blob") {
                        resolve(new Blob([res.data], {
                            type: res.headers["content-type"].split(";")[0]
                        }))
                    } else {
                        resolve(res.data);
                        return res.data
                    }
                }).catch(err => {
                    if (err.response) {
                        if (err.response.data)
                            reject(err.response.data)
                        else
                            reject(err.response);
                    } else {
                        reject(err)
                    }
                })
        })
    }
}

// class Web static method properties bind
/**
* @description GetScanStatus url链接，包含baseURL
*/
Web.GetScanStatus.fullPath = `${axios.defaults.baseURL}/scan_status`
/**
* @description GetScanStatus url链接，不包含baseURL
*/
Web.GetScanStatus.path = `/scan_status`
/**
* @description ListHTMLFiles url链接，包含baseURL
*/
Web.ListHTMLFiles.fullPath = `${axios.defaults.baseURL}/list_html`
/**
* @description ListHTMLFiles url链接，不包含baseURL
*/
Web.ListHTMLFiles.path = `/list_html`
/**
* @description GetHTMLFileCount url链接，包含baseURL
*/
Web.GetHTMLFileCount.fullPath = `${axios.defaults.baseURL}/list_html_count`
/**
* @description GetHTMLFileCount url链接，不包含baseURL
*/
Web.GetHTMLFileCount.path = `/list_html_count`
/**
* @description GetWeb url链接，包含baseURL
*/
Web.GetWeb.fullPath = `${axios.defaults.baseURL}/web`
/**
* @description GetWeb url链接，不包含baseURL
*/
Web.GetWeb.path = `/web`
/**
* @description GetWebWithRewrite url链接，包含baseURL
*/
Web.GetWebWithRewrite.fullPath = `${axios.defaults.baseURL}/web/rewrite`
/**
* @description GetWebWithRewrite url链接，不包含baseURL
*/
Web.GetWebWithRewrite.path = `/web/rewrite`
/**
* @description GetWebQualityJob url链接，包含baseURL
*/
Web.GetWebQualityJob.fullPath = `${axios.defaults.baseURL}/web/quality/job/get`
/**
* @description GetWebQualityJob url链接，不包含baseURL
*/
Web.GetWebQualityJob.path = `/web/quality/job/get`
/**
* @description SubmitWebQualityJob url链接，包含baseURL
*/
Web.SubmitWebQualityJob.fullPath = `${axios.defaults.baseURL}/web/quality/job/submit`
/**
* @description SubmitWebQualityJob url链接，不包含baseURL
*/
Web.SubmitWebQualityJob.path = `/web/quality/job/submit`
/**
* @description GetWebQualityJobStatus url链接，包含baseURL
*/
Web.GetWebQualityJobStatus.fullPath = `${axios.defaults.baseURL}/web/quality/job/status`
/**
* @description GetWebQualityJobStatus url链接，不包含baseURL
*/
Web.GetWebQualityJobStatus.path = `/web/quality/job/status`

export class common {

    /**
    * @summary Home
    * @param {CancelTokenSource} [cancelSource] Axios Cancel Source 对象，可以取消该请求
    * @param {Function} [uploadProgress] 上传回调函数
    * @param {Function} [downloadProgress] 下载回调函数
    */
    static async home__get(cancelSource, uploadProgress, downloadProgress) {
        return await new Promise((resolve, reject) => {
            let responseType = "json";
            let options = {
                method: 'get',
                url: '/',
                data: {},
                params: {},
                headers: {
                    "Content-Type": ""
                },
                onUploadProgress: uploadProgress,
                onDownloadProgress: downloadProgress
            }
            // support wechat mini program
            if (cancelSource != undefined) {
                options.cancelToken = cancelSource.token
            }
            if (responseType != "json") {
                options.responseType = responseType;
            }
            axios(options)
                .then(res => {
                    if (res.config.responseType == "blob") {
                        resolve(new Blob([res.data], {
                            type: res.headers["content-type"].split(";")[0]
                        }))
                    } else {
                        resolve(res.data);
                        return res.data
                    }
                }).catch(err => {
                    if (err.response) {
                        if (err.response.data)
                            reject(err.response.data)
                        else
                            reject(err.response);
                    } else {
                        reject(err)
                    }
                })
        })
    }
}

// class common static method properties bind
/**
* @description home__get url链接，包含baseURL
*/
common.home__get.fullPath = `${axios.defaults.baseURL}/`
/**
* @description home__get url链接，不包含baseURL
*/
common.home__get.path = `/`
