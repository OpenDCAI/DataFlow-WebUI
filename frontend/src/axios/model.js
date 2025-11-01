export class HTMLItem {
  
    /**
     *
     * @param {String} name 
     * @param {String} path 
     * @param {undefined} quality 
     * @param {String} quality_status 
     */ 
    constructor(name = undefined,path = undefined,quality = undefined,quality_status = undefined){
        this.name = name
        this.path = path
        this.quality = quality
        this.quality_status = quality_status
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
    path=undefined   
    /**
     * 
     * @type {undefined}
     */
    quality=undefined   
    /**
     * 
     * @type {String}
     */
    quality_status=undefined
    
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
