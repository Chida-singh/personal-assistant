import React, { Component, useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Menu } from "lucide-react";
import Sidebar from "./components/Sidebar";
import DashboardPage from "./pages/DashboardPage";
import ChatPage from "./pages/ChatPage";
import FinancePage from "./pages/FinancePage";
import TodoPage from "./pages/TodoPage";
import NotesPage from "./pages/NotesPage";
import CalendarPage from "./pages/CalendarPage";
import SettingsPage from "./pages/SettingsPage";
import VaultPage from "./pages/VaultPage";
import HabitsPage from "./pages/HabitsPage";
import JournalPage from "./pages/JournalPage";
import LoginPage from "./pages/LoginPage";
import { getToken } from "./api";

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, info: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, info) {
    this.setState({ error, info });
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 40, background: "#1a0505", color: "#fca5a5", minHeight: "100vh" }}>
          <h2>Application Error</h2>
          <pre>{this.state.error && this.state.error.toString()}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  const [token, setAuthToken] = useState(getToken());
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    function handleLogout() {
      setAuthToken("");
    }
    window.addEventListener("auth:logout", handleLogout);
    return () => window.removeEventListener("auth:logout", handleLogout);
  }, []);

  if (!token) {
    return <LoginPage onLoginSuccess={(tok) => setAuthToken(tok)} />;
  }

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div className="app-layout">
          {/* Mobile Topbar */}
          <header className="mobile-topbar">
            <div className="mobile-brand">
              <img src="/logo.png" alt="" style={{ height: 20, width: 20, borderRadius: 4 }} />
              <div className="mobile-brand-title">Cookie</div>
            </div>
            <button
              className="mobile-menu-btn"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle navigation menu"
            >
              <Menu size={18} />
            </button>
          </header>

          {/* Sidebar and Backdrop */}
          <Sidebar
            isOpen={mobileMenuOpen}
            onClose={() => setMobileMenuOpen(false)}
          />
          {mobileMenuOpen && (
            <div
              className="sidebar-backdrop"
              onClick={() => setMobileMenuOpen(false)}
              aria-hidden="true"
            />
          )}

          {/* Main Content Area */}
          <main className="main-content">
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/journal" element={<JournalPage />} />
              <Route path="/finance" element={<FinancePage />} />
              <Route path="/todos" element={<TodoPage />} />
              <Route path="/habits" element={<HabitsPage />} />
              <Route path="/notes" element={<NotesPage />} />
              <Route path="/calendar" element={<CalendarPage />} />
              <Route path="/vault" element={<VaultPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
