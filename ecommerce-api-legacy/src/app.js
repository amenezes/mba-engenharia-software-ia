const express = require('express');
const { initDb } = require('./db');
const { errorHandler, notFound } = require('./middlewares/errorHandler');

async function createApp() {
    const app = express();
    app.use(express.json({ limit: '1mb' }));

    await initDb();

    app.use(require('./routes'));
    app.use(require('./routes/checkoutRoutes'));
    app.use(require('./routes/adminRoutes'));
    app.use(require('./routes/userRoutes'));

    app.use(notFound);
    app.use(errorHandler);

    return app;
}

const config = require('./config');

if (require.main === module) {
    createApp().then(app => {
        app.listen(config.port, () => {
            console.log(`LMS API (MVC) rodando na porta ${config.port}...`);
        });
    }).catch(err => {
        console.error('Falha ao iniciar:', err);
        process.exit(1);
    });
}

module.exports = { createApp };
