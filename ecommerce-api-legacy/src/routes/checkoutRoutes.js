const express = require('express');
const router = express.Router();
const checkoutController = require('../controllers/checkoutController');

router.post('/api/checkout', async (req, res, next) => {
    try {
        const result = await checkoutController.process({
            name: req.body.usr,
            email: req.body.eml,
            pwd: req.body.pwd,
            courseId: req.body.c_id,
            cardNumber: req.body.card,
        });
        res.status(200).json(result);
    } catch (err) {
        next(err);
    }
});

module.exports = router;
