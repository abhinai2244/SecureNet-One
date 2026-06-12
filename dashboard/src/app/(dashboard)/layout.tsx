"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { isAuthenticated, logout, getCurrentUser } from "@/lib/api";
import type { User } from "@/types";

const navItems = [
  { label: "Dashboard", icon: "📊", href: "/dashboard", section: "overview" },
  { label: "Devices", icon: "💻", href: "/devices", section: "management" },
  { label: "Policies", icon: "🔒", href: "/policies", section: "management" },
  { label: "Users", icon: "👥", href: "/users", section: "management" },
  { label: "DNS Logs", icon: "🌐", href: "/logs", section: "monitoring" },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    setUser(getCurrentUser());
  }, [router]);

  const sections = [
    { key: "overview", label: "Overview" },
    { key: "management", label: "Management" },
    { key: "monitoring", label: "Monitoring" },
  ];

  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon">🛡️</div>
          <span className="logo-text">SecureNet One</span>
        </div>

        <nav className="sidebar-nav">
          {sections.map((section) => {
            const items = navItems.filter((item) => item.section === section.key);
            if (items.length === 0) return null;
            return (
              <div className="nav-section" key={section.key}>
                <div className="nav-section-title">{section.label}</div>
                {items.map((item) => (
                  <a
                    key={item.href}
                    href={item.href}
                    className={`nav-item ${pathname === item.href ? "active" : ""}`}
                    onClick={(e) => {
                      e.preventDefault();
                      router.push(item.href);
                    }}
                  >
                    <span className="nav-icon">{item.icon}</span>
                    <span>{item.label}</span>
                  </a>
                ))}
              </div>
            );
          })}
        </nav>

        {/* User info at bottom */}
        <div
          style={{
            padding: "var(--space-lg)",
            borderTop: "1px solid var(--border-default)",
          }}
        >
          <div className="flex items-center gap-md">
            <div className="avatar">
              {user?.full_name?.charAt(0)?.toUpperCase() || "U"}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="text-sm truncate" style={{ fontWeight: 500 }}>
                {user?.full_name || "User"}
              </div>
              <div className="text-xs text-muted truncate">{user?.role || "user"}</div>
            </div>
            <button
              className="btn btn-ghost btn-icon"
              onClick={logout}
              title="Logout"
              id="logout-btn"
            >
              🚪
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {/* Header */}
        <header className="header">
          <h2 className="header-title">
            {navItems.find((n) => n.href === pathname)?.label || "Dashboard"}
          </h2>
          <div className="header-actions">
            <div className="header-search">
              <span className="search-icon">🔍</span>
              <input
                type="text"
                className="input"
                placeholder="Search..."
                id="global-search"
              />
            </div>
            <button className="btn btn-ghost btn-icon" title="Notifications">
              🔔
            </button>
          </div>
        </header>

        {/* Page Content */}
        <div className="page-content">{children}</div>
      </main>
    </div>
  );
}
