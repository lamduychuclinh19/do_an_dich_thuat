// Gọi API cùng origin (Flask). Nếu server báo chưa thanh toán (402) thì quay về trang thanh toán.
export async function http(method, path, { params, body } = {}) {
  const url = new URL(path, window.location.origin);
  if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  const res = await fetch(url, {
    method,
    credentials: "same-origin",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 402) { window.location.replace("/"); throw new Error("payment_required"); }
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(data?.error || `HTTP ${res.status}`);
  return data;
}
