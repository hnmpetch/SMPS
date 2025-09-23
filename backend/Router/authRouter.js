const express = require('express');
const router = express.Router();
const auth = require('../Controller/authController');


router.get('/' , auth.login);


module.exports = router;