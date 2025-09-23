const { Sequelize } = require("sequelize");


const sequelize = new Sequelize("smps", "root", "", {
    host: "127.0.0.1",
    dialect: "mysql"
});

sequelize.authenticate()
    .then( () => {
        console.log("Connect to database success full!")
    })
    .catch( (e) => {
        console.error(`Fail to connect to database error: ${e}`)
    });


module.exports = {
    sequelize
}