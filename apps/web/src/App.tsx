import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import EvalRun from "./pages/EvalRun";
import History from "./pages/History";
import Settings from "./pages/Settings";

function App() {
  return (
    <HashRouter>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<Login />} />

        {/* Protected (auth guard will be added in Phase 6) */}
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/eval/new" element={<EvalRun />} />
        <Route path="/eval/:id" element={<Dashboard />} />
        <Route path="/history" element={<History />} />
        <Route path="/settings" element={<Settings />} />

        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </HashRouter>
  );
}

export default App;
