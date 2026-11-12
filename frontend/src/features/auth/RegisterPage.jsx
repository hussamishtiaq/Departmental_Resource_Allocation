import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import ErrorMessage from "../../components/feedback/ErrorMessage";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import { useAuth } from "../../hooks/useAuth";
import { getErrorMessage } from "../../services/apiClient";
import * as authApi from "./authApi";
import { validateRegister } from "./authValidation";

export default function RegisterPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", confirm: "" });
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  const onChange = (e) => {
    setApiError("");
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  async function onSubmit(e) {
    e.preventDefault();
    const found = validateRegister(form);
    setErrors(found);
    if (Object.keys(found).length) return;
    setSubmitting(true);
    try {
      await authApi.register({
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        password: form.password,
      });
      await login(form.email.trim(), form.password);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setApiError(getErrorMessage(err, "Registration failed"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 p-4">
      <form onSubmit={onSubmit} noValidate className="w-full max-w-sm space-y-4 rounded-lg bg-white p-6 shadow">
        <h1 className="text-2xl font-bold">Create account</h1>
        <ErrorMessage message={apiError} />
        <Input label="Full name" name="full_name" value={form.full_name} onChange={onChange} error={errors.full_name} />
        <Input label="Email" name="email" type="email" autoComplete="email" value={form.email} onChange={onChange} error={errors.email} />
        <Input label="Password" name="password" type="password" autoComplete="new-password" value={form.password} onChange={onChange} error={errors.password} />
        <Input label="Confirm password" name="confirm" type="password" autoComplete="new-password" value={form.confirm} onChange={onChange} error={errors.confirm} />
        <Button type="submit" loading={submitting} className="w-full">Register</Button>
        <p className="text-center text-sm text-slate-500">
          Already registered? <Link to="/login" className="text-indigo-600 hover:underline">Sign in</Link>
        </p>
        <p className="text-center text-xs text-slate-400">New accounts are students; a senior member assigns your role.</p>
      </form>
    </main>
  );
}
