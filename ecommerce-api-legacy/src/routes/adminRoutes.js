const express = require('express');
const router = express.Router();
const adminController = require('../controllers/adminController');
const { verifyToken, requireAdmin } = require('../middlewares/auth');

router.get('/api/admin/financial-report', verifyToken, requireAdmin, adminController.financialReport);

module.exports = router;
