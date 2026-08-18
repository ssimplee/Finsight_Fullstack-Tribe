import React from "react";
import { Fish } from "lucide-react";
import { useRouter } from "next/navigation";
import Button from "../ui/Button";
import { useConsultation } from "../../context/ConsultationContext";

const pageDescriptions = {
  "/": "Evidence-grounded fish health triage",
  "/consultation": "Case intake and follow-up guidance",
  "/analysis": "Evidence retrieval and comparison",
  "/report": "Decision-support assessment report",
};

export default function Header({ currentPath }) {
  const router = useRouter();
  const { resetConsultation } = useConsultation();

  const handleNewConsultation = () => {
    resetConsultation();
    router.push("/consultation");
  };

  return (
    <header className="site-header">
      <div className="site-header__inner">
        <button
          type="button"
          className="site-header__brand"
          onClick={() => router.push("/")}
          aria-label="Go to FinSight home"
        >
          <span className="site-header__logo">
            <Fish size={18} aria-hidden="true" />
          </span>
          <span>
            <span className="site-header__title">FinSight</span>
            <span className="site-header__subtitle">
              Fish Health Triage Agent
            </span>
          </span>
        </button>

        <div className="site-header__meta">
          <p className="site-header__page">
            {pageDescriptions[currentPath] ?? pageDescriptions["/"]}
          </p>
          <Button variant="secondary" size="sm" onClick={handleNewConsultation}>
            New Consultation
          </Button>
        </div>
      </div>
    </header>
  );
}
