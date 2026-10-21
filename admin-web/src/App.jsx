import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import AdminLayout from "./layouts/AdminLayout";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import PoiPage from "./pages/PoiPage";
import ProfilePage from "./pages/ProfilePage";
import ShopOwnerPage from "./pages/ShopOwnerPage";
import TranslationPage from "./pages/TranslationPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<AdminLayout />}>
            <Route
              path="/dashboard"
              element={<DashboardPage />}
            />
            <Route
              path="/pois"
              element={<PoiPage />}
            />
            <Route
              path="/translations"
              element={<TranslationPage />}
            />

            <Route
              element={
                <ProtectedRoute
                  allowedRoles={["SYSTEM_ADMIN"]}
                />
              }
            >
              <Route
                path="/shop-owners"
                element={<ShopOwnerPage />}
              />
            </Route>

            <Route
              element={
                <ProtectedRoute
                  allowedRoles={["SHOP_OWNER"]}
                />
              }
            >
              <Route
                path="/profile"
                element={<ProfilePage />}
              />
            </Route>
          </Route>
        </Route>

        <Route
          path="*"
          element={<Navigate to="/dashboard" replace />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
