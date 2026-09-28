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