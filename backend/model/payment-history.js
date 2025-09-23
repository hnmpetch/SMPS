const { DataTypes } = require("sequelize");
const { sequelize } = require("../database");


const Payment = sequelize.define("Payment", {
    id: {
        type: DataTypes.UUIDV4,
        allowNull: false,
        primaryKey: true
    },
    user_id: {
        type: DataTypes.STRING,
        allowNull: false
    },
    park_id: {
        type: DataTypes.INTEGER,
        allowNull: false
    },
    park_info: {
        type: DataTypes.INTEGER,
        allowNull: false
    },
    amount: {
        type: DataTypes.FLOAT,
        allowNull: false,
        defaultValue: 0
    },
    method: {
        type: DataTypes.STRING,
        allowNull: false
    },
    success: {
        type: DataTypes.TINYINT,
        allowNull: false,
        defaultValue: 0
    }
},{
    tableName: "payment",
    timestamps: true,
    updatedAt: "update_at",
    createdAt: "create_at"
})


module.exports = {
    Payment
}