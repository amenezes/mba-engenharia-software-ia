const reportService = require('../services/reportService');

async function financialReport(req, res, next) {
    try {
        const report = await reportService.buildFinancialReport();
        res.json(report);
    } catch (err) {
        next(err);
    }
}

module.exports = { financialReport };
