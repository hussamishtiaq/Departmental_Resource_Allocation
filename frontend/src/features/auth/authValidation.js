const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateLogin({ email, password }) {
  const errors = {};
  if (!EMAIL_RE.test(email)) errors.email = "Enter a valid email address";
  if (!password) errors.password = "Password is required";
  return errors;
}

export function validateRegister({ full_name, email, password, confirm }) {
  const errors = {};
  if (full_name.trim().length < 2) errors.full_name = "Enter your full name";
  if (!EMAIL_RE.test(email)) errors.email = "Enter a valid email address";
  if (password.length < 8) errors.password = "At least 8 characters";
  else if (!/[A-Za-z]/.test(password) || !/\d/.test(password))
    errors.password = "Use both letters and digits";
  if (confirm !== password) errors.confirm = "Passwords do not match";
  return errors;
}
