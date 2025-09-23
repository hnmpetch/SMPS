const { User } = require("../model/user");
const jwt = require('jsonwebtoken');


const sec_token = process.env.JWT;

const missinfo = {
                "status": 404,
                "message": "Missing Infomation",
                "success": false
            };



const server_fail = {
                "status": 501,
                "message": "Server catch",
                "success": false
            };


async function check_token(token) {
    
    const decoded = await jwt.verify(token, sec_token);

    if(decoded.username == null) {
        return false
    }

    return decoded


}

async function login(req, res) {
    
    try{
        const { username, password } = req.body();

        if (!username || !password) {
            return res.status(400).json({ message: 'Username and password are required' });
        }


        try {
            
            
            const User_unverify = await User.findOne({
                where: {
                    username : username
                }
            })


            const match = await bcrypt.compare(password, User_unverify.password);

            
            if (!match) {
                return res.status(401).json({
                    "message": "Username or Password invalid."
                })
            }
            
            
            
            const user_token = {
                "id": User_unverify.id,
                "username": username,
            }

            const token = await jwt.sign(user_token, sec_token, { expiresIn: '30d' })
            
            
            return res.status(200).json({
                "id": User_unverify.id,
                "username": User_unverify.username,
                "token": token
            })
        }catch (e) {
            console.error(e)
            return res.status(501).json(server_fail);
        }
    }catch (e) {
        console.error(e)
        return res.status(501).json(server_fail);
    }

}


module.exports = {
    login
}