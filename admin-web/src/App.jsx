import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import AdminLayout from "./layouts/AdminLayout";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import PoiPage from "./pages/PoiPage";
import ProfilePage from "./pages/ProfilePage";
import ShopOwnerPage from "./pages/ShopOwnerPage";
import TranslationPage from "./pages/TranslationPage";
import OwnerRegistrationPage from "./pages/OwnerRegistrationPage";
import OwnerSignupPage from "./pages/OwnerSignupPage";
import OwnerNotificationsPage from "./pages/OwnerNotificationsPage";
import PoiApprovalPage from "./pages/PoiApprovalPage";
import TranslationApprovalPage from "./pages/TranslationApprovalPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Trang đăng nhập là trang công khai */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/owner-signup" element={<OwnerSignupPage />} />

        {/* Tất cả trang bên trong đều phải qua ProtectedRoute */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AdminLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/pois" element={<PoiPage />} />
            <Route path="/translations" element={<TranslationPage />} />

            <Route element={<ProtectedRoute allowedRoles={["SYSTEM_ADMIN"]} />}>
              <Route path="/shop-owners" element={<ShopOwnerPage />} />
              <Route path="/owner-registrations" element={<OwnerRegistrationPage />} />
              <Route path="/poi-approvals" element={<PoiApprovalPage />} />
              <Route path="/translation-approvals" element={<TranslationApprovalPage />} />
            </Route>

            <Route element={<ProtectedRoute allowedRoles={["SHOP_OWNER"]} />}>
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/notifications" element={<OwnerNotificationsPage />} />
            </Route>
          </Route>
        </Route>

        {/* URL gõ sai hoặc không tồn tại cũng đưa về đăng nhập */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
