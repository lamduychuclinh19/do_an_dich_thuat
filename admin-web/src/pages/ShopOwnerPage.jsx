import { useCallback, useEffect, useState } from "react";
import api from "../services/api";
import "./ShopOwnerPage.css";

const EMPTY_FORM = {
  username: "",
  full_name: "",
  phone: "",
  email: "",
};

function getApiErrorMessage(error, fallbackMessage) {
  const detail = error.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  return fallbackMessage;
}

function formatDateTime(value) {
  if (!value) {
    return "Chưa đăng nhập";
  }

  return new Date(value).toLocaleString("vi-VN");
}

function ShopOwnerPage() {
  const [shopOwners, setShopOwners] = useState([]);
  const [keyword, setKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [isLoading, setIsLoading] = useState(true);
  const [processingKey, setProcessingKey] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const loadShopOwners = useCallback(async () => {
    try {
      setErrorMessage("");

      const params = {};
      const normalizedKeyword = keyword.trim();

      if (normalizedKeyword) {
        // Backend dùng cùng một keyword để tìm tên quán hoặc SĐT.
        params.keyword = normalizedKeyword;
      }

      if (statusFilter !== "all") {
        params.is_active = statusFilter === "active";
      }

      const response = await api.get(
        "/api/admin/shop-owners",
        { params }
      );
      setShopOwners(response.data);
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Không thể tải danh sách chủ quán."
        )
      );
    } finally {
      setIsLoading(false);
    }
  }, [keyword, statusFilter]);

  useEffect(() => {
    // Trì hoãn ngắn để không gọi API sau từng phím gõ quá nhanh.
    const timeoutId = window.setTimeout(() => {
      setIsLoading(true);
      loadShopOwners();
    }, 300);

    return () => window.clearTimeout(timeoutId);
  }, [loadShopOwners]);

  const changeAccountStatus = async (owner, nextStatus) => {
    const actionName = nextStatus ? "mở khóa" : "khóa";
    const confirmed = window.confirm(
      `Cậu có chắc muốn ${actionName} tài khoản "${owner.username}" không?`
    );

    if (!confirmed) {
      return;
    }

    const operationKey = `${owner.id}-${nextStatus}`;

    try {
      setProcessingKey(operationKey);
      setErrorMessage("");
      setSuccessMessage("");

      const response = await api.patch(
        `/api/admin/shop-owners/${owner.id}`,
        { is_active: nextStatus }
      );

      setShopOwners((currentOwners) =>
        currentOwners.map((currentOwner) =>
          currentOwner.id === owner.id
            ? response.data
            : currentOwner
        )
      );
      setSuccessMessage(
        `Đã ${actionName} tài khoản ${owner.username}.`
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          `Không thể ${actionName} tài khoản.`
        )
      );
    } finally {
      setProcessingKey("");
    }
  };

  const resetPassword = async (owner) => {
    const confirmed = window.confirm(
      `Đặt lại mật khẩu của "${owner.username}" về abc12345?`
    );

    if (!confirmed) {
      return;
    }

    const operationKey = `${owner.id}-reset`;

    try {
      setProcessingKey(operationKey);
      setErrorMessage("");
      setSuccessMessage("");

      const response = await api.post(
        `/api/admin/shop-owners/${owner.id}/reset-password`
      );
      setSuccessMessage(response.data.message);
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          "Không thể đặt lại mật khẩu."
        )
      );
    } finally {
      setProcessingKey("");
    }
  };

  const handleCreated = (createdOwner) => {
    setShopOwners((currentOwners) => [
      createdOwner,
      ...currentOwners,
    ]);
    setSuccessMessage(
      "Đã tạo tài khoản. Mật khẩu mặc định là abc12345."
    );
  };

  return (
    <div className="owner-page">
      <div className="owner-heading">
        <div>
          <p>QUẢN LÝ NỘI DUNG</p>
          <h1>Chủ quán</h1>
          
        </div>

        <div className="owner-heading-actions">
          <div className="owner-summary">
            <strong>{shopOwners.length}</strong>
            <span>chủ quán</span>
          </div>
          <button
            type="button"
            className="add-owner-button"
            onClick={() => setIsCreateOpen(true)}
          >
            Thêm
          </button>
        </div>
      </div>

      <section className="owner-container">
        <div className="owner-toolbar">
          <div className="owner-search-box">
            <span>⌕</span>
            <input
              type="search"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              placeholder="Tìm theo số điện thoại"
            />
          </div>

          <select
            className="owner-status-filter"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
          >
            <option value="all">Tất cả trạng thái</option>
            <option value="active">Đang hoạt động</option>
            <option value="locked">Đã khóa</option>
          </select>
        </div>

        {errorMessage && (
          <div className="owner-message error">{errorMessage}</div>
        )}
        {successMessage && (
          <div className="owner-message success">{successMessage}</div>
        )}

        <div className="owner-table-wrapper">
          <table className="owner-table">
            <thead>
              <tr>
                <th>Mã </th>
                <th>Tài khoản</th>
                <th>Họ tên</th>
                <th>Liên hệ</th>
                <th>Trạng thái</th>
                <th>Lần đăng nhập cuối</th>
                <th>Ngày tạo</th>
              </tr>
            </thead>

            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan="10" className="owner-empty-cell">
                    Đang tải dữ liệu...
                  </td>
                </tr>
              ) : shopOwners.length === 0 ? (
                <tr>
                  <td colSpan="10" className="owner-empty-cell">
                    Không tìm thấy chủ quán phù hợp.
                  </td>
                </tr>
              ) : (
                shopOwners.map((owner) => (
                  <tr key={owner.id}>
                    <td className="owner-id">#{owner.id}</td>
                    <td>
                      <strong>{owner.username}</strong>
                      {owner.must_change_password && (
                        <small className="password-note">
                          Cần đổi mật khẩu
                        </small>
                      )}
                    </td>
                    <td>{owner.full_name || "Chưa cập nhật"}</td>
                    
                    <td>
                      <div className="owner-contact">
                        <span>{owner.phone || "Chưa có SĐT"}</span>
                        <small>{owner.email || "Chưa có email"}</small>
                      </div>
                    </td>
                    <td>
                      <span
                        className={
                          owner.is_active
                            ? "owner-status active"
                            : "owner-status locked"
                        }
                      >
                        {owner.is_active ? "Hoạt động" : "Đã khóa"}
                      </span>
                    </td>
                    <td>{formatDateTime(owner.last_login_at)}</td>
                    <td>{formatDateTime(owner.created_at)}</td>
                    <td>
                      <div className="owner-actions">
                        <button
                          type="button"
                          className="owner-action lock"
                          disabled={
                            !owner.is_active ||
                            processingKey === `${owner.id}-false`
                          }
                          onClick={() =>
                            changeAccountStatus(owner, false)
                          }
                        >
                          Khóa
                        </button>
                        <button
                          type="button"
                          className="owner-action unlock"
                          disabled={
                            owner.is_active ||
                            processingKey === `${owner.id}-true`
                          }
                          onClick={() =>
                            changeAccountStatus(owner, true)
                          }
                        >
                          Mở khóa
                        </button>
                        <button
                          type="button"
                          className="owner-action reset"
                          disabled={
                            processingKey === `${owner.id}-reset`
                          }
                          onClick={() => resetPassword(owner)}
                        >
                          Đặt lại mật khẩu
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <CreateShopOwnerModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onCreated={handleCreated}
      />
    </div>
  );
}

function CreateShopOwnerModal({ isOpen, onClose, onCreated }) {
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  if (!isOpen) {
    return null;
  }

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((currentData) => ({
      ...currentData,
      [name]: value,
    }));
  };

  const handleClose = () => {
    setFormData(EMPTY_FORM);
    setErrorMessage("");
    onClose();
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      setIsSaving(true);
      setErrorMessage("");
      const response = await api.post(
        "/api/admin/shop-owners",
        formData
      );
      onCreated(response.data);
      handleClose();
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(error, "Không thể tạo tài khoản chủ quán.")
      );
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="owner-modal-backdrop" role="presentation">
      <section
        className="owner-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-owner-title"
      >
        <div className="owner-modal-heading">
          <div>
            <p>TÀI KHOẢN MỚI</p>
            <h2 id="create-owner-title">Thêm chủ quán</h2>
          </div>
          <button type="button" onClick={handleClose}>×</button>
        </div>

        <form onSubmit={handleSubmit}>
          <label htmlFor="owner-username">Tên đăng nhập</label>
          <input
            id="owner-username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            minLength="3"
            required
          />

          <label htmlFor="owner-full-name">Họ và tên</label>
          <input
            id="owner-full-name"
            name="full_name"
            value={formData.full_name}
            onChange={handleChange}
            minLength="2"
            required
          />

          <label htmlFor="owner-phone">Số điện thoại</label>
          <input
            id="owner-phone"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            pattern="0[0-9]{9}"
            placeholder="Ví dụ: 0912345678"
            required
          />

          <label htmlFor="owner-email">Email</label>
          <input
            id="owner-email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            required
          />

          <p className="owner-default-password">
            Mật khẩu mặc định: <strong>abc12345</strong>
          </p>

          {errorMessage && (
            <div className="owner-message error">{errorMessage}</div>
          )}

          <div className="owner-modal-actions">
            <button type="button" onClick={handleClose}>
              Hủy
            </button>
            <button type="submit" disabled={isSaving}>
              {isSaving ? "Đang tạo..." : "Tạo tài khoản"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

export default ShopOwnerPage;
