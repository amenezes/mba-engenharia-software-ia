const express = require('express');
const router = express.Router();

router.get('/health', (req, res) => {
    res.json({ status: 'ok', database: 'connected', versao: '2.0.0', arquitetura: 'MVC' });
});

router.get('/', (req, res) => {
    res.json({
        mensagem: 'LMS API',
        versao: '2.0.0',
        arquitetura: 'MVC',
        endpoints: {
            checkout: 'POST /api/checkout',
            login: 'POST /api/login',
            financial_report: 'GET /api/admin/financial-report (auth)',
            health: 'GET /health',
        },
    });
});

module.exports = router;
