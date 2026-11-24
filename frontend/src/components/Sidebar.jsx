import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  MessageSquare,
  BarChart3,
  CheckSquare,
  StickyNote,
  Calendar,
  Settings,
  Shield,
  Flame,
  BookOpen,
  X,
} from "lucide-react";

const NAV_ITEMS = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard", end: true },
  { to: "/chat", icon: MessageSquare, label: "Chat" },
  { to: "/journal", icon: BookOpen, label: "Journal" },
  { to: "/finance", icon: BarChart3, label: "Finance" },
  { to: "/todos", icon: CheckSquare, label: "Tasks" },
  { to: "/habits", icon: Flame, label: "Habits" },
  { to: "/notes", icon: StickyNote, label: "Notes" },
  { to: "/calendar", icon: Calendar, label: "Calendar" },
  { to: "/vault", icon: Shield, label: "Vault" },
];

export default function Sidebar({ isOpen, onClose }) {
  return (
    <aside className={`sidebar${isOpen ? " open" : ""}`}>
      <div className="sidebar-brand" style={{ justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <img src="/logo.png" alt="" style={{ height: 22, width: 22, borderRadius: 4 }} />
          <div className="sidebar-brand-title">Cookie</div>
        </div>
        {isOpen && (
          <button
            onClick={onClose}
            className="btn btn-ghost"
            style={{ padding: 4, border: "none", color: "var(--text-2)" }}
          >
            <X size={16} />
          </button>
        )}
      </div>

      <div className="sidebar-section-label">Menu</div>

      {NAV_ITEMS.map(({ to, icon: Icon, label, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={onClose}
          className={({ isActive }) =>
            `sidebar-nav-btn${isActive ? " active" : ""}`
          }
        >
          <Icon />
          {label}
        </NavLink>
      ))}

      <div className="sidebar-spacer" />
      <div className="sidebar-separator" />

      <NavLink
        to="/settings"
        onClick={onClose}
        className={({ isActive }) =>
          `sidebar-nav-btn${isActive ? " active" : ""}`
        }
      >
        <Settings />
        Settings
      </NavLink>

      <div style={{ height: 8 }} />
    </aside>
  );
}
