export class ApiResponse_DatasetOut_ {
  
    /**
     *
     * @param {undefined} success 
     * @param {Number} code 业务错误码，0 表示成功
     * @param {String} message 
     */ 
    constructor(success = undefined,code = undefined,message = undefined,data = undefined,meta = undefined){
        this.success = success
        this.code = code
        this.message = message
        this.data = data
        this.meta = meta
    }
       
    /**
     * 
     * @type {undefined}
     */
    success=undefined   
    /**
     * 业务错误码，0 表示成功
     * @type {Number}
     */
    code=undefined   
    /**
     * 
     * @type {String}
     */
    message=undefined
    
}
export class ApiResponse_List_OperatorSchema__ {
  
    /**
     *
     * @param {undefined} success 
     * @param {Number} code 业务错误码，0 表示成功
     * @param {String} message 
     */ 
    constructor(success = undefined,code = undefined,message = undefined,data = undefined,meta = undefined){
        this.success = success
        this.code = code
        this.message = message
        this.data = data
        this.meta = meta
    }
       
    /**
     * 
     * @type {undefined}
     */
    success=undefined   
    /**
     * 业务错误码，0 表示成功
     * @type {Number}
     */
    code=undefined   
    /**
     * 
     * @type {String}
     */
    message=undefined
    
}
export class ApiResponse_list_DatasetOut__ {
  
    /**
     *
     * @param {undefined} success 
     * @param {Number} code 业务错误码，0 表示成功
     * @param {String} message 
     */ 
    constructor(success = undefined,code = undefined,message = undefined,data = undefined,meta = undefined){
        this.success = success
        this.code = code
        this.message = message
        this.data = data
        this.meta = meta
    }
       
    /**
     * 
     * @type {undefined}
     */
    success=undefined   
    /**
     * 业务错误码，0 表示成功
     * @type {Number}
     */
    code=undefined   
    /**
     * 
     * @type {String}
     */
    message=undefined
    
}
export class DatasetIn {
  
    /**
     *
     * @param {String} name 
     * @param {String} root 
     * @param {String} pipeline 指定一个或多个该数据集适合的 pipeline
     * @param {undefined} meta 
     */ 
    constructor(name = undefined,root = undefined,pipeline = undefined,meta = undefined){
        this.name = name
        this.root = root
        this.pipeline = pipeline
        this.meta = meta
    }
       
    /**
     * 
     * @type {String}
     */
    name=undefined   
    /**
     * 
     * @type {String}
     */
    root=undefined   
    /**
     * 指定一个或多个该数据集适合的 pipeline
     * @type {String}
     */
    pipeline=undefined   
    /**
     * 
     * @type {undefined}
     */
    meta=undefined
    
}
export class DatasetOut {
  
    /**
     *
     * @param {String} name 
     * @param {String} root 
     * @param {String} pipeline 指定一个或多个该数据集适合的 pipeline
     * @param {undefined} meta 
     * @param {String} id 
     * @param {Number} num_samples 
     */ 
    constructor(name = undefined,root = undefined,pipeline = undefined,meta = undefined,id = undefined,num_samples = undefined,hash = undefined){
        this.name = name
        this.root = root
        this.pipeline = pipeline
        this.meta = meta
        this.id = id
        this.num_samples = num_samples
        this.hash = hash
    }
       
    /**
     * 
     * @type {String}
     */
    name=undefined   
    /**
     * 
     * @type {String}
     */
    root=undefined   
    /**
     * 指定一个或多个该数据集适合的 pipeline
     * @type {String}
     */
    pipeline=undefined   
    /**
     * 
     * @type {undefined}
     */
    meta=undefined   
    /**
     * 
     * @type {String}
     */
    id=undefined   
    /**
     * 
     * @type {Number}
     */
    num_samples=undefined
    
}
export class HTTPValidationError {
  
    /**
     *
     * @param {Array} detail 
     */ 
    constructor(detail = undefined){
        this.detail = detail
    }
       
    /**
     * 
     * @type {Array}
     */
    detail=undefined
    
}
export class OperatorSchema {
  
    /**
     *
     * @param {String} name 
     * @param {undefined} type 
     */ 
    constructor(name = undefined,type = undefined,allowed_prompts = undefined,description = undefined){
        this.name = name
        this.type = type
        this.allowed_prompts = allowed_prompts
        this.description = description
    }
       
    /**
     * 
     * @type {String}
     */
    name=undefined   
    /**
     * 
     * @type {undefined}
     */
    type=undefined
    
}
export class ValidationError {
  
    /**
     *
     * @param {Array} loc 
     * @param {String} msg 
     * @param {String} type 
     */ 
    constructor(loc = undefined,msg = undefined,type = undefined){
        this.loc = loc
        this.msg = msg
        this.type = type
    }
       
    /**
     * 
     * @type {Array}
     */
    loc=undefined   
    /**
     * 
     * @type {String}
     */
    msg=undefined   
    /**
     * 
     * @type {String}
     */
    type=undefined
    
}
