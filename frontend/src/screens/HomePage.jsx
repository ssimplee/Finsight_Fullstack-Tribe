import React from "react";
import { ArrowRight, FileText, Image, MessageSquare } from "lucide-react";
import { useRouter } from "next/navigation";
import PageContainer from "../components/layout/PageContainer";
import SectionCard from "../components/ui/SectionCard";
import Button from "../components/ui/Button";
import { useConsultation } from "../context/ConsultationContext";

const featureCards = [
  {
    id: "feature-intake",
    title: "Multimodal Case Intake",
    description:
      "Review images, clinical signs, water-quality context, and management history together.",
    icon: <Image size={18} aria-hidden="true" />,
  },
  {
    id: "feature-follow-up",
    title: "Adaptive Follow-up",
    description:
      "Collect missing evidence through case-specific questions before comparing causes.",
    icon: <MessageSquare size={18} aria-hidden="true" />,
  },
  {
    id: "feature-report",
    title: "Evidence-grounded Report",
    description:
      "Surface possible causes, supporting evidence, uncertainty, and safe next actions.",
    icon: <FileText size={18} aria-hidden="true" />,
  },
];

export default function HomePage() {
  const router = useRouter();
  const { resetConsultation } = useConsultation();

  const handleStart = () => {
    resetConsultation();
    router.push("/consultation");
  };

  return (
    <PageContainer>
      <section className="hero">
        <div className="hero__content">
          <p className="hero__eyebrow">Aquaculture triage workflow</p>
          <h1>Diagnose fish health through a multimodal conversation.</h1>
          <p className="hero__description">
            Combine images, symptoms, water-quality data and recent farming
            history to build an evidence-grounded fish-health assessment.
          </p>

          <div className="hero__actions">
            <Button
              onClick={handleStart}
              iconRight={<ArrowRight size={16} aria-hidden="true" />}
            >
              Start New Consultation
            </Button>
            <p className="hero__note">
              FinSight supports diagnostic triage and does not replace
              laboratory confirmation or professional veterinary advice.
            </p>
          </div>
        </div>

        <div className="hero__panel">
          <div className="hero__stat">
            <span>Workflow</span>
            <strong>
              Upload evidence {"->"} Answer follow-up questions {"->"} Review the
              report
            </strong>
          </div>
          <div className="hero__grid">
            <div>
              <span>Input types</span>
              <strong>Image, symptoms, water quality, husbandry history</strong>
            </div>
            <div>
              <span>Decision model</span>
              <strong>Observed findings first, differential comparison second</strong>
            </div>
            <div>
              <span>Safety stance</span>
              <strong>No condition is shown as confirmed without further testing</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="feature-grid">
        {featureCards.map((feature) => (
          <SectionCard
            key={feature.id}
            title={feature.title}
            eyebrow="Core capability"
          >
            <div className="feature-card">
              <span className="feature-card__icon">{feature.icon}</span>
              <p>{feature.description}</p>
            </div>
          </SectionCard>
        ))}
      </section>
    </PageContainer>
  );
}
