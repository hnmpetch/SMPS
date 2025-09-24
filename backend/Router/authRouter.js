const express = require('express');
const router = express.Router();
const auth = require('../Controller/authController');


router.post('/login' , auth.login);


module.exports = router;