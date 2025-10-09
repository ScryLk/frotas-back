# Implementação - Card de Login com Troca de Senha Integrada

## 🎯 Objetivo

Criar uma experiência de login fluida onde a troca de senha no primeiro acesso acontece **no mesmo card**, sem parecer que redirecionou para outra página.

---

## 💻 Implementação com React

### LoginCard.jsx (Componente Único)

```jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, changeFirstAccessPassword } from '../services/authService';
import './LoginCard.css';

const LoginCard = () => {
  // Estados do login
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // Estados da troca de senha
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Controle de fluxo
  const [step, setStep] = useState('login'); // 'login' ou 'change-password'
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await login(username, password);
    setLoading(false);

    if (result.success) {
      if (result.requirePasswordChange) {
        // Transição suave para troca de senha no mesmo card
        setStep('change-password');
      } else {
        navigate('/dashboard');
      }
    } else {
      setError(result.message || 'Erro ao fazer login');
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setError('');

    // Validação básica
    if (newPassword.length < 10) {
      setError('A senha deve ter no mínimo 10 caracteres');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('As senhas não conferem');
      return;
    }

    setLoading(true);
    const result = await changeFirstAccessPassword(newPassword, confirmPassword);
    setLoading(false);

    if (result.success) {
      // Transição suave para o dashboard
      navigate('/dashboard');
    } else {
      // Exibe erros do backend
      if (result.errors?.confirm_password) {
        setError(result.errors.confirm_password[0]);
      } else if (result.errors?.new_password) {
        setError(result.errors.new_password[0]);
      } else {
        setError(result.message || 'Erro ao trocar senha');
      }
    }
  };

  return (
    <div className="login-container">
      <div className={`login-card ${step === 'change-password' ? 'change-password-mode' : ''}`}>

        {/* Header do Card */}
        <div className="card-header">
          <h2>
            {step === 'login' ? '🔐 Login' : '🔑 Primeiro Acesso'}
          </h2>
          <p className="card-subtitle">
            {step === 'login'
              ? 'Entre com suas credenciais'
              : 'Defina uma nova senha para continuar'}
          </p>
        </div>

        {/* Formulário de Login */}
        {step === 'login' && (
          <form onSubmit={handleLogin} className="fade-in">
            <div className="form-group">
              <label htmlFor="username">Usuário</label>
              <input
                type="text"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Digite seu usuário"
                required
                disabled={loading}
                autoFocus
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Senha</label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Digite sua senha"
                required
                disabled={loading}
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <button type="submit" className="submit-btn" disabled={loading}>
              {loading ? 'Entrando...' : 'Entrar'}
            </button>
          </form>
        )}

        {/* Formulário de Troca de Senha */}
        {step === 'change-password' && (
          <form onSubmit={handlePasswordChange} className="fade-in">
            <div className="welcome-message">
              <p>Olá, <strong>{username}</strong>! 👋</p>
              <p className="info-text">Por segurança, defina uma nova senha para continuar.</p>
            </div>

            <div className="form-group">
              <label htmlFor="newPassword">Nova Senha</label>
              <input
                type="password"
                id="newPassword"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Mínimo 10 caracteres"
                required
                disabled={loading}
                autoFocus
              />
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Confirmar Senha</label>
              <input
                type="password"
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Digite a senha novamente"
                required
                disabled={loading}
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <button type="submit" className="submit-btn" disabled={loading}>
              {loading ? 'Alterando...' : 'Confirmar Nova Senha'}
            </button>

            <div className="password-requirements">
              <p><strong>Requisitos da senha:</strong></p>
              <ul>
                <li className={newPassword.length >= 10 ? 'valid' : ''}>
                  Mínimo de 10 caracteres
                </li>
                <li>Não pode ser similar ao seu nome de usuário</li>
                <li>Não pode ser uma senha muito comum</li>
                <li className={!/^\d+$/.test(newPassword) ? 'valid' : ''}>
                  Não pode ser totalmente numérica
                </li>
              </ul>
            </div>
          </form>
        )}

      </div>
    </div>
  );
};

export default LoginCard;
```

---

## 🎨 LoginCard.css

```css
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 450px;
  width: 100%;
  transition: all 0.4s ease;
}

/* Animação suave ao trocar de step */
.login-card.change-password-mode {
  max-width: 500px;
}

/* Header do Card */
.card-header {
  text-align: center;
  margin-bottom: 30px;
}

.card-header h2 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 28px;
}

.card-subtitle {
  color: #666;
  margin: 0;
  font-size: 14px;
}

/* Form Groups */
.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.form-group input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e1e8ed;
  border-radius: 8px;
  font-size: 16px;
  transition: all 0.3s;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-group input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

/* Welcome Message */
.welcome-message {
  background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 25px;
  border-left: 4px solid #667eea;
}

.welcome-message p {
  margin: 0;
  color: #333;
}

.welcome-message p:first-child {
  font-size: 16px;
  margin-bottom: 5px;
}

.welcome-message .info-text {
  font-size: 14px;
  color: #666;
}

/* Error Message */
.error-message {
  background-color: #fee;
  color: #c33;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  border-left: 4px solid #c33;
  font-size: 14px;
  animation: shake 0.3s;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

/* Submit Button */
.submit-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Password Requirements */
.password-requirements {
  margin-top: 25px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.password-requirements p {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 14px;
}

.password-requirements ul {
  margin: 0;
  padding-left: 20px;
  color: #666;
  font-size: 13px;
}

.password-requirements li {
  margin-bottom: 6px;
  transition: all 0.3s;
}

.password-requirements li.valid {
  color: #28a745;
  font-weight: 600;
}

.password-requirements li.valid::before {
  content: '✓ ';
  margin-right: 5px;
}

/* Animações */
.fade-in {
  animation: fadeIn 0.4s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsivo */
@media (max-width: 480px) {
  .login-card {
    padding: 30px 20px;
  }

  .card-header h2 {
    font-size: 24px;
  }
}
```

---

## 🔄 Fluxo da Experiência

```
┌─────────────────────────────────────┐
│        CARD DE LOGIN                │
│                                     │
│  🔐 Login                           │
│  Entre com suas credenciais         │
│                                     │
│  [Username: _________]              │
│  [Password: _________]              │
│                                     │
│  [ Entrar ]                         │
└─────────────────────────────────────┘
              ↓ (Login bem-sucedido)
              ↓ (require_password_change = true)
              ↓ (Animação suave - fade in/out)
┌─────────────────────────────────────┐
│      MESMO CARD (Transformado)      │
│                                     │
│  🔑 Primeiro Acesso                 │
│  Defina uma nova senha              │
│                                     │
│  ┌────────────────────────────────┐│
│  │ Olá, usuario! 👋               ││
│  │ Por segurança, defina uma nova ││
│  │ senha para continuar.          ││
│  └────────────────────────────────┘│
│                                     │
│  [Nova Senha: __________]           │
│  [Confirmar:  __________]           │
│                                     │
│  [ Confirmar Nova Senha ]           │
│                                     │
│  ✅ Requisitos da senha:            │
│  • Mínimo de 10 caracteres          │
│  • Não pode ser similar ao username │
└─────────────────────────────────────┘
              ↓
              ↓ (Senha alterada)
              ↓
        [ DASHBOARD ]
```

---

## ✨ Recursos Implementados

### 1. **Transição Suave entre Estados**
- Usa `step` state para controlar qual formulário mostrar
- Animação `fade-in` ao trocar de formulário
- Mesmo card, sem redirecionamento

### 2. **Feedback Visual em Tempo Real**
- Validação de senha com checkmarks ✓
- Mensagem de boas-vindas personalizada
- Contadores de caracteres (opcional)

### 3. **UX Aprimorada**
- AutoFocus nos campos corretos
- Estados de loading
- Mensagens de erro contextuais
- Animação de shake nos erros

### 4. **Design Responsivo**
- Funciona em mobile e desktop
- Ajuste de tamanho suave ao trocar de step

---

## 🎯 Versão Alternativa - Com Animação de Slide

Se preferir um efeito de slide lateral:

```css
/* Adicione ao CSS */
.login-card {
  position: relative;
  overflow: hidden;
}

.form-container {
  transition: transform 0.4s ease;
}

.login-card.change-password-mode .form-container {
  transform: translateX(-100%);
}

.slide-in-right {
  animation: slideInRight 0.4s ease;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
```

---

## 📝 Uso no Router

```jsx
// App.jsx ou Routes.jsx
import LoginCard from './components/LoginCard';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginCard />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
```

**Nota:** Não precisa de rota separada para `/first-access-password-change` porque tudo acontece no mesmo componente!

---

## 🧪 Teste a Experiência

1. Acesse `/login`
2. Faça login com um usuário que precisa trocar senha
3. O card se transforma suavemente
4. Defina a nova senha
5. Redireciona para o dashboard

**Resultado:** Experiência fluida, sem parecer que mudou de página! ✨
