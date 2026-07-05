const express = require('express');
const router = express.Router();
const userController = require('../controllers/userController');
const { verifyToken } = require('../middlewares/auth');

router.delete('/api/users/:id', verifyToken, userController.remove);
router.post('/api/login', userController.login);

module.exports = router;
