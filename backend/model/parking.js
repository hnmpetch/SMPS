const { DataTypes } = require("sequelize");
const { sequelize } = require("../database");


const Parking = sequelize.define("Parking", {
    id: {
        type: DataTypes.INTEGER,
        allowNull: false,
        primaryKey: true
    },
    status: {
        type: DataTypes.STRING,
        allowNull: false,
        defaultValue: "FREE"
    }
},{
    tableName: "parking",
    timestamps: false

})


module.exports = {
    Parking
}