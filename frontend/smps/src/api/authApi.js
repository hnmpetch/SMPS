import axios from "axios";

export const loginUser = async (userdata) => {

    try{
        const res = await axios.post('http://127.0.0.1:4002/api/auth/login', userdata);

        localStorage.setItem('token', res.data.token);

        return res.data;
    } catch(e) {
        throw e
    }

}

