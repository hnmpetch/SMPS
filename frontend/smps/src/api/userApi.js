import axios from "axios";

export const registerUser = async (userdata) => {

    try{
        const res = await axios.post('http://127.0.0.1:4002/api/users/register', userdata);
        return res.data;
    } catch(e) {
        throw e
    }

}

