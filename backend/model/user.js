const { DataTypes } = require("sequelize");
const { sequelize } = require("../database");


const User = sequelize.define("user", {
    id: {
        type: DataTypes.UUIDV4,
        allowNull: false,
        primaryKey: true
    },
    username: {
        type: DataTypes.STRING,
        allowNull: false
    },
    password: {
        type: DataTypes.STRING,
        allowNull: false
    },
    email: {
        type: DataTypes.STRING,
        allowNull: false
    }
},{
    tableName: "user",
    timestamps: true,
    updatedAt: "upadate_at",
    createdAt: "create_at"
})

module.exports = {
    User
}