const TOKEN_KEY = "access_token";

// Frontend chỉ đọc payload JWT để quyết định cách hiển thị giao diện.
// Quyền thật vẫn luôn được FastAPI kiểm tra lại ở phía server.
function decodeJwtPayload(token) {
  try {
    const payloadPart = token.split(".")[1];

    if (!payloadPart) {
      return null;
    }

    const normalized = payloadPart
      .replace(/-/g, "+")
      .replace(/_/g, "/");
    const padded = normalized.padEnd(
      normalized.length + ((4 - (normalized.length % 4)) % 4),
      "="
    );
    const binary = window.atob(padded);
    const bytes = Uint8Array.from(
      binary,
      (character) => character.charCodeAt(0)
    );
    const jsonText = new TextDecoder().decode(bytes);

    return JSON.parse(jsonText);
  } catch {
    return null;
  }
}

export function saveSession(accessToken) {
  localStorage.setItem(TOKEN_KEY, accessToken);
  return getSession();
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
}

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getSession() {
  const accessToken = getAccessToken();

  if (!accessToken) {
    return null;
  }

  const payload = decodeJwtPayload(accessToken);

  if (!payload?.sub || !payload?.role) {
    clearSession();
    return null;
  }

  // Tự loại token đã hết hạn để không hiển thị giao diện cũ sai quyền.
  if (payload.exp && payload.exp * 1000 <= Date.now()) {
    clearSession();
    return null;
  }

  return {
    id: Number(payload.sub),
    username: payload.username,
    role: payload.role,
    mustChangePassword: Boolean(payload.must_change_password),
    accessToken,
  };
}

export function getRoleLabel(role) {
  if (role === "SYSTEM_ADMIN") {
    return "Quản trị hệ thống";
  }

  if (role === "SHOP_OWNER") {
    return "Chủ quán";
  }

  return "Không xác định";
}

export function isBackOfficeRole(role) {
  return role === "SYSTEM_ADMIN" || role === "SHOP_OWNER";
}
