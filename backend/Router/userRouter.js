const express = require('express');
const router = express.Router();
const user = require('../Controller/userController');

router.get('/', user.getAllusers);
router.get('/:id', user.getUser);
router.post('/register', user.registerUser);
router.delete('/delete/:id', user.deleteUser);

module.exports = router