const { DataTypes } = require("sequelize");
const { sequelize } = require("../database");



const User_lot = sequelize.define("User_lot", {
    id: {
        type: DataTypes.INTEGER,
        allowNull: false,
        primaryKey: true
    },
    user_id: {
        type: DataTypes.STRING,
        allowNull: false,
    },
    slot: {
        type: DataTypes.INTEGER,
        allowNull: false
    },
    timestamp: {
        type: DataTypes.TIME,
        allowNull: false
    }
}, {
    tableName: "user_lot",
    timestamps: true
})

module.exports = {
    User_lot
}