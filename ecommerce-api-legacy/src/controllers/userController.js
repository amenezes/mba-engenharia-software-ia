const enrollmentModel = require('../models/enrollmentModel');
const userModel = require('../models/userModel');
const { signToken } = require('../services/tokenService');

async function remove(req, res, next) {
    try {
        const { id } = req.params;
        await enrollmentModel.deleteByUserId(id);
        res.json({ msg: 'Usuario e dados relacionados removidos', sucesso: true });
    } catch (err) {
        next(err);
    }
}

async function login(req, res, next) {
    try {
        const { name, eml, pwd } = req.body;
        if (!eml || !pwd) return res.status(400).json({ erro: 'email e senha obrigatorios' });
        const user = await userModel.authenticate(name || eml, eml, pwd);
        if (!user) return res.status(401).json({ erro: 'Credenciais inválidas', sucesso: false });
        const token = signToken({ sub: user.id, name: user.name, email: user.email });
        res.json({ dados: user, token, sucesso: true, mensagem: 'Login OK' });
    } catch (err) {
        next(err);
    }
}

module.exports = { remove, login };
