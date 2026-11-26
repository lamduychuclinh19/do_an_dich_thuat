// Biểu mẫu đăng ký tài khoản dành cho chủ quán.
// Biểu mẫu đăng ký tài khoản dành cho chủ quán.
import { useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";
import { validateVietnamPhone } from "../utils/vietnamPhone";
import "./OwnerSignupPage.css";

const initialForm = {
  username: "",
  full_name: "",
  phone: "",
  email: "",
  password: "",
  confirmPassword: "",
};

function validateField(name, value, form) {
  const normalizedValue = String(value ?? "").trim();
  if (!normalizedValue) return "";

  if (name === "username") {
    if (/\s/.test(value)) return "Tên đăng nhập không được chứa dấu cách.";
    if (!/^[A-Za-z0-9_.-]{4,50}$/.test(value)) {
      return "Tên đăng nhập cần từ 4–50 ký tự, chỉ gồm chữ, số, dấu chấm, gạch dưới hoặc gạch ngang.";
    }
  }
  if (name === "full_name" && normalizedValue.length < 2) {
    return "Họ và tên cần có ít nhất 2 ký tự.";
  }
  if (name === "phone") {
    return validateVietnamPhone(value);
  }
  if (name === "email") {
    const [localPart, domain] = normalizedValue.toLowerCase().split("@");
    if (!localPart || !domain?.includes(".")) return "Email không đúng định dạng.";
    if (domain !== "gmail.com" || localPart.length < 2) {
      return "Email đăng ký phải là địa chỉ Gmail hợp lệ.";
    }
  }
  if (name === "password") {
    if (value.length < 8 || !/\p{L}/u.test(value) || !/\p{N}/u.test(value)) {
      return "Mật khẩu cần ít nhất 8 ký tự, gồm cả chữ và số.";
    }
  }
  if (name === "confirmPassword" && value !== form.password) {
    return "Mật khẩu xác nhận chưa khớp.";
  }
  return "";
}

function validateRequiredFields(form) {
  const requiredMessage = "Bạn chưa điền thông tin này.";
  return Object.fromEntries(
    Object.entries(form).map(([name, value]) => [
      name,
      String(value ?? "").trim()
        ? validateField(name, value, form)
        : requiredMessage,
    ])
  );
}

function getApiError(error) {
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail[0]?.msg || "Thông tin đăng ký chưa hợp lệ.";
  return "Không thể gửi phiếu đăng ký.";
}

export default function OwnerSignupPage() {
  const [form, setForm] = useState(initialForm);
  const [fieldErrors, setFieldErrors] = useState({});
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const change = (event) => {
    const { name, value } = event.target;
    const nextForm = { ...form, [name]: value };
    setForm(nextForm);
    setError("");
    setFieldErrors((current) => ({
      ...current,
      [name]: validateField(name, value, nextForm),
      ...(name === "password" && nextForm.confirmPassword
        ? { confirmPassword: validateField("confirmPassword", nextForm.confirmPassword, nextForm) }
        : {}),
    }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setMessage("");
    setError("");

    const nextErrors = validateRequiredFields(form);
    if (form.phone && !nextErrors.phone) {
      nextErrors.phone = validateVietnamPhone(form.phone, { requireComplete: true });
    }
    setFieldErrors(nextErrors);
    const firstInvalidField = Object.keys(nextErrors).find((name) => nextErrors[name]);
    if (firstInvalidField) {
      const fieldIds = {
        username: "signup-username",
        full_name: "signup-full-name",
        phone: "signup-phone",
        email: "signup-email",
        password: "signup-password",
        confirmPassword: "signup-confirm-password",
      };
      window.requestAnimationFrame(() => document.getElementById(fieldIds[firstInvalidField])?.focus());
      return;
    }

    setBusy(true);
    try {
      const registration = { ...form };
      delete registration.confirmPassword;
      await api.post("/api/auth/shop-owner-registration", registration);
      setMessage("Phiếu đăng ký đã được gửi. Bạn sẽ nhận kết quả qua email sau khi quản trị viên xem xét.");
      setForm(initialForm);
      setFieldErrors({});
    } catch (requestError) {
      setError(getApiError(requestError));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="owner-signup">
      <form className="owner-signup-card" onSubmit={submit} noValidate>
        <header className="owner-signup-heading">
          <h1>Đăng ký tài khoản</h1>
          <span>Thông tin của bạn sẽ được gửi đến quản trị viên để xét duyệt.</span>
        </header>

        <label className="signup-field" htmlFor="signup-username">
          Tên đăng nhập
          <input
            id="signup-username"
            name="username"
            value={form.username}
            onChange={change}
            autoComplete="username"
            maxLength={50}
            aria-invalid={Boolean(fieldErrors.username)}
            aria-describedby={fieldErrors.username ? "signup-username-error" : undefined}
            required
          />
          {fieldErrors.username && <small className="signup-field-error" id="signup-username-error">{fieldErrors.username}</small>}
        </label>

        <label className="signup-field" htmlFor="signup-full-name">
          Họ và tên
          <input id="signup-full-name" name="full_name" value={form.full_name} onChange={change} autoComplete="name" aria-invalid={Boolean(fieldErrors.full_name)} aria-describedby={fieldErrors.full_name ? "signup-full-name-error" : undefined} required />
          {fieldErrors.full_name && <small className="signup-field-error" id="signup-full-name-error">{fieldErrors.full_name}</small>}
        </label>

        <label className="signup-field" htmlFor="signup-phone">
          Số điện thoại
          <input
            id="signup-phone"
            name="phone"
            type="tel"
            inputMode="numeric"
            pattern="0[0-9]{9}"
            placeholder="0912345678"
            value={form.phone}
            onChange={change}
            autoComplete="tel"
            aria-invalid={Boolean(fieldErrors.phone)}
            aria-describedby={fieldErrors.phone ? "signup-phone-error" : undefined}
            required
          />
          {fieldErrors.phone && <small className="signup-field-error" id="signup-phone-error">{fieldErrors.phone}</small>}
        </label>

        <label className="signup-field" htmlFor="signup-email">
          Email
          <small className="signup-field-hint">Thông báo phê duyệt về tài khoản sẽ được gửi về email này</small>
          <input id="signup-email" name="email" type="email" value={form.email} onChange={change} autoComplete="email" aria-invalid={Boolean(fieldErrors.email)} aria-describedby={fieldErrors.email ? "signup-email-error" : undefined} required />
          {fieldErrors.email && <small className="signup-field-error" id="signup-email-error">{fieldErrors.email}</small>}
        </label>

        <label className="signup-field" htmlFor="signup-password">
          Mật khẩu
          {!fieldErrors.password && <small className="signup-field-hint" id="signup-password-hint">Ít nhất 8 ký tự, gồm cả chữ và số.</small>}
          <input
            id="signup-password"
            name="password"
            type="password"
            value={form.password}
            onChange={change}
            autoComplete="new-password"
            aria-invalid={Boolean(fieldErrors.password)}
            aria-describedby={fieldErrors.password ? "signup-password-error" : "signup-password-hint"}
            required
          />
          {fieldErrors.password && <small className="signup-field-error" id="signup-password-error">{fieldErrors.password}</small>}
        </label>

        <label className="signup-field" htmlFor="signup-confirm-password">
          Xác nhận mật khẩu
          <input
            id="signup-confirm-password"
            name="confirmPassword"
            type="password"
            value={form.confirmPassword}
            onChange={change}
            autoComplete="new-password"
            aria-invalid={Boolean(fieldErrors.confirmPassword)}
            aria-describedby={fieldErrors.confirmPassword ? "signup-confirm-error" : undefined}
            required
          />
          {fieldErrors.confirmPassword && <small className="signup-field-error" id="signup-confirm-error">{fieldErrors.confirmPassword}</small>}
        </label>

        {error && <p className="signup-form-message error">{error}</p>}
        {message && <p className="signup-form-message success">{message}</p>}
        <button className="signup-submit" type="submit" disabled={busy}>
          {busy ? "Đang gửi..." : "Gửi phiếu đăng ký"}
        </button>
        <Link className="signup-login-link" to="/login">Quay lại đăng nhập</Link>
      </form>
    </main>
  );
}
