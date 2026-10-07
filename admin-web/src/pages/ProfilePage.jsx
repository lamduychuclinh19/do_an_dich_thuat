import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import {
  clearSession,
  getRoleLabel,
} from "../services/auth";
import "./ProfilePage.css";

const EMPTY_PROFILE = {
  full_name: "",
  phone: "",
  email: "",
};

const EMPTY_PASSWORDS = {
  current_password: "",
  new_password: "",
  confirm_password: "",
};

function getApiErrorMessage(error, fallbackMessage) {
  const detail = error.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail) && detail[0]?.msg) {
    return detail[0].msg;
  }

  return fallbackMessage;
}

function ProfilePage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [profileForm, setProfileForm] = useState(EMPTY_PROFILE);
  const [passwordForm, setPasswordForm] = useState(EMPTY_PASSWORDS);
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [profileError, setProfileError] = useState("");
  const [profileSuccess, setProfileSuccess] = useState("");
  const [passwordError, setPasswordError] = useState("");

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const response = await api.get("/api/profile/me");
        setProfile(response.data);
        setProfileForm({
          full_name: response.data.full_name || "",
          phone: response.data.phone || "",
          email: response.data.email || "",
        });
      } catch (error) {
        setProfileError(
          getApiErrorMessage(
            error,
            "Không thể tải thông tin cá nhân."
          )
        );
      } finally {
        setIsLoading(false);
      }
    };

    loadProfile();
  }, []);

  const handleProfileChange = (event) => {
    const { name, value } = event.target;
    setProfileForm((currentData) => ({
      ...currentData,
      [name]: value,
    }));
  };

  const handlePasswordChange = (event) => {
    const { name, value } = event.target;
    setPasswordForm((currentData) => ({
      ...currentData,
      [name]: value,
    }));
  };

  const saveProfile = async (event) => {
    event.preventDefault();

    try {
      setIsSavingProfile(true);
      setProfileError("");
      setProfileSuccess("");

      const response = await api.patch(
        "/api/profile/me",
        profileForm
      );
      setProfile(response.data);
      setProfileSuccess("Thông tin cá nhân đã được cập nhật.");
    } catch (error) {
      setProfileError(
        getApiErrorMessage(
          error,
          "Không thể cập nhật thông tin cá nhân."
        )
      );
    } finally {
      setIsSavingProfile(false);
    }
  };

  const changePassword = async (event) => {
    event.preventDefault();
    setPasswordError("");

    if (
      passwordForm.new_password !==
      passwordForm.confirm_password
    ) {
      setPasswordError("Xác nhận mật khẩu mới không khớp.");
      return;
    }

    try {
      setIsChangingPassword(true);
      const response = await api.patch(
        "/api/profile/me/password",
        passwordForm
      );

      window.alert(response.data.message);
      clearSession();
      navigate("/login", { replace: true });
    } catch (error) {
      setPasswordError(
        getApiErrorMessage(error, "Không thể đổi mật khẩu.")
      );
    } finally {
      setIsChangingPassword(false);
    }
  };

  if (isLoading) {
    return <div className="profile-loading">Đang tải hồ sơ...</div>;
  }

  return (
    <div className="profile-page">
      <div className="profile-heading">
      </div>

      <div className="profile-grid">
        <section className="profile-card">
          <div className="profile-card-heading">
            <div>
              <p>HỒ SƠ</p>
              <h2>Thông tin tài khoản</h2>
            </div>
            <span className="profile-role">
              {getRoleLabel(profile?.role)}
            </span>
          </div>

          {profileError && (
            <div className="profile-message error">{profileError}</div>
          )}
          {profileSuccess && (
            <div className="profile-message success">
              {profileSuccess}
            </div>
          )}

          <form className="profile-form" onSubmit={saveProfile}>
            <div className="profile-field">
              <label htmlFor="profile-full-name">Họ và tên</label>
              <input
                id="profile-full-name"
                name="full_name"
                value={profileForm.full_name}
                onChange={handleProfileChange}
                minLength="2"
                required
              />
            </div>

            <div className="profile-field">
              <label htmlFor="profile-phone">Số điện thoại</label>
              <input
                id="profile-phone"
                name="phone"
                value={profileForm.phone}
                onChange={handleProfileChange}
                pattern="0[0-9]{9}"
                required
              />
            </div>

            <div className="profile-field full-width">
              <label htmlFor="profile-email">Email</label>
              <input
                id="profile-email"
                name="email"
                type="email"
                value={profileForm.email}
                onChange={handleProfileChange}
                required
              />
            </div>

            <button
              className="profile-primary-button"
              type="submit"
              disabled={isSavingProfile}
            >
              {isSavingProfile ? "Đang lưu..." : "Lưu thông tin"}
            </button>
          </form>
        </section>

        <section className="profile-card password-card">
          <div className="profile-card-heading">
            <div>
              <p>BẢO MẬT</p>
              <h2>Đổi mật khẩu</h2>
            </div>
          </div>

          {passwordError && (
            <div className="profile-message error">{passwordError}</div>
          )}

          <form className="password-form" onSubmit={changePassword}>
            <label htmlFor="current-password">Mật khẩu hiện tại</label>
            <input
              id="current-password"
              name="current_password"
              type="password"
              value={passwordForm.current_password}
              onChange={handlePasswordChange}
              minLength="8"
              autoComplete="current-password"
              required
            />

            <label htmlFor="new-password">Mật khẩu mới</label>
            <input
              id="new-password"
              name="new_password"
              type="password"
              value={passwordForm.new_password}
              onChange={handlePasswordChange}
              minLength="8"
              autoComplete="new-password"
              required
            />

            <label htmlFor="confirm-password">
              Xác nhận mật khẩu mới
            </label>
            <input
              id="confirm-password"
              name="confirm_password"
              type="password"
              value={passwordForm.confirm_password}
              onChange={handlePasswordChange}
              minLength="8"
              autoComplete="new-password"
              required
            />

            <button
              className="profile-primary-button"
              type="submit"
              disabled={isChangingPassword}
            >
              {isChangingPassword
                ? "Đang đổi mật khẩu..."
                : "Đổi mật khẩu"}
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}

export default ProfilePage;
