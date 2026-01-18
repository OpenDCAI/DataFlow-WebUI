import axios from 'axios'

let ax = axios.create()

// config here
if (import.meta.env.MODE == 'production') {
    ax.defaults.baseURL = import.meta.env.VITE_BACKEND_URL
} else {
    ax.defaults.baseURL = '/api'
}

ax.interceptors.request.use(
    (config) => {
        if (
            config.headers['Content-Type'].includes('x-www-form-urlencoded') ||
            config.headers['Content-Type'].includes('multipart/form-data')
        ) {
            let formData = new FormData()
            for (let item in config.data) {
                if (config.data[item]) {
                    if (Array.isArray(config.data[item])) {
                        for (let i of config.data[item]) {
                            formData.append(item, i)
                        }
                    } else formData.append(item, config.data[item])
                }
            }
            config.data = formData
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

export default ax
