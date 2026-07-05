// Config carregada de variaveis de ambiente (sem hardcoded).
module.exports = {
    port: process.env.PORT || 3000,
    dbUser: process.env.DB_USER,
    dbPass: process.env.DB_PASS,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    smtpUser: process.env.SMTP_USER || 'no-reply@example.com',
    jwtSecret: process.env.JWT_SECRET || 'dev-only-change-me',
    jwtExpirationHours: parseInt(process.env.JWT_EXPIRATION_HOURS || '8', 10),
    isProd: process.env.NODE_ENV === 'production',
    seedUserPassword: (() => {
        const pwd = process.env.SEED_USER_PASSWORD;
        if (!pwd) {
            throw new Error('Variável de ambiente obrigatória não definida: SEED_USER_PASSWORD');
        }
        return pwd;
    })(),
};
