const enrollmentModel = require('../models/enrollmentModel');

async function buildFinancialReport() {
    const rows = await enrollmentModel.getFinancialReport();
    return rows.map(r => ({
        course: r.course,
        revenue: r.revenue,
        enrollment_count: r.enrollment_count,
    }));
}

module.exports = { buildFinancialReport };
