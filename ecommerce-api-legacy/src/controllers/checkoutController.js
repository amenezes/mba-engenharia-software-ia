const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const userModel = require('../models/userModel');
const { PaymentError, charge } = require('../services/paymentService');
const { hashPassword } = require('../services/passwordService');

class CheckoutError extends Error {
    constructor(message, status = 400) {
        super(message);
        this.status = status;
    }
}

async function process({ name, email, pwd, courseId, cardNumber }) {
    if (!name || !email || !pwd || !courseId || !cardNumber) {
        throw new CheckoutError('Bad Request', 400);
    }

    const course = await courseModel.findActiveById(courseId);
    if (!course) throw new CheckoutError('Curso nao encontrado', 404);

    let user = await userModel.findByEmail(email);
    if (!user) {
        const { lastID } = await userModel.create(name, email, hashPassword(pwd));
        user = await userModel.findById(lastID);
    }

    const payment = charge(cardNumber, course.price);

    const { lastID: enrollmentId } = await enrollmentModel.createEnrollment(user.id, courseId);
    await enrollmentModel.createPayment(enrollmentId, payment.amount, payment.status);
    await enrollmentModel.createAuditLog(`Checkout curso ${courseId} por ${user.id}`);

    return { msg: 'Sucesso', enrollment_id: enrollmentId };
}

module.exports = { process, CheckoutError, PaymentError };
