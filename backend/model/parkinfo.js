const { DataTypes } = require("sequelize");
const { sequelize } = require("../database");


const parkinfo = sequelize.define("parking_info", {
    id: {
        type: DataTypes.INTEGER,
        allowNull: false,
        primaryKey: true
    },
    park_id: {
        type: DataTypes.INTEGER,
        allowNull: false,
    },
    user_id: {
        type: DataTypes.STRING,
        allowNull: false
    },
    starttime: {
        type: DataTypes.TIME,
        allowNull: false,
    },
    endtime: {
        type: DataTypes.TIME,
        allowNull: false
    }
}, {
    tableName: "parkinfo",
    timestamps: false
})

module.exports = {
    parkinfo
}