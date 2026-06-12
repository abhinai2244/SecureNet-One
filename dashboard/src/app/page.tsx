"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated()) {
      router.replace("/dashboard");
    } else {
      router.replace("/login");
    }
  }, [router]);

  return (
    <div className="login-page">
      <div style={{ textAlign: "center" }}>
        <div className="login-header">
          <div className="logo-large">🛡️</div>
          <h1 className="text-gradient">SecureNet One</h1>
          <p className="text-muted mt-md">Loading...</p>
        </div>
      </div>
    </div>
  );
}
