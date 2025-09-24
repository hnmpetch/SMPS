const { User } = require("../model/user")
const bcrypt = require('bcrypt')

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

async function getAllusers(req, res) {
    
    const users = await User.findAll();

    return res.json(users);


}

async function getUser(req, res) {
    try {
        const id = req.param.id

        if (!id) {
            return req.status(404).json(missinfo)
        }

        const user = await User.findAll({
            where: {
                id: id
            }
        })
        

        return res.json(user)
    } catch (e) {
        console.error(e)
        return res.status(501).json(server_fail)
    }
}


async function registerUser(req, res) {
    try{
        const { username, password, email } = req.body;

        console.log(req);
        console.log(req.body);

        if (!username || !password || !email) {
            return res.status(404).json(missinfo)
        }

        try {
            const alredyUser = await User.findOne({
                where: {
                    username: username
                }
            })

            if (alredyUser != null){
                return res.status(401).json({
                    "status": 401,
                    "message": "User has alerdy register",
                    "success": false
                })
            }
        } catch (e) {
            console.error(e)
            return res.status(501).json(server_fail);
        }

        try {
            
            const hashpassword = await bcrypt.hash(password, 20);
            const newUser = await User.create({
                username: username,
                password: hashpassword,
                email: email,
            });

            if(!newUser) {
                return res.status(501).json({
                    "status": 501,
                    "message": "Fail to register user",
                    "success": true
                })
            };

            return res.json({
                "status": 200,
                "message": "success register user",
                "success": true,
                "data": newUser.toJSON()
            });

        } catch (e) {
            console.error(e)
            return res.status(501).json(server_fail);
        }
    } catch(e) {
        console.error(e)
        return res.status(501).json(server_fail);
    }
}


async function deleteUser(req, res) {
    const id = req.params.id;
    
    if (id == null) {
        return res.status(404).send("No id")
    }

    const alreadyuser = User.findAll({
    where: {
        id: id
    }
    })

    if (alreadyuser == null) {
        return res.status(400).send("User not in table")
    }

    try {
        const deleteuser = User.destroy({
            where: {
            id: id
            }
        });

        if (!deleteuser) {
            return res.status(404).send("Fail to delete user");
        }
    } catch (err) {
        return res.status(404).send("Fail to delete user");
    }

    return res.json({"message": "Success"})
}



module.exports = {
    getAllusers,
    getUser,
    registerUser,
    deleteUser
}