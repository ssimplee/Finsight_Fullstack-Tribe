import React, { useEffect, useState } from "react";
import { CheckCircle2, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import PageContainer from "../components/layout/PageContainer";
import ProgressPanel from "../components/layout/ProgressPanel";
import SectionCard from "../components/ui/SectionCard";
import Button from "../components/ui/Button";
import { useConsultation } from "../context/ConsultationContext";

const analysisSteps = [
  "Reviewing case information",
  "Processing image observations",
  "Identifying missing information",
  "Retrieving fish-health evidence",
  "Comparing possible causes",
  "Running safety and grounding checks",
  "Preparing the report",
];

export default function AnalysisPage() {
  const router = useRouter();
  const [activeIndex, setActiveIndex] = useState(-1);
  const [isFinished, setFinished] = useState(false);
  const { consultation, setCurrentStep, setReportReady } = useConsultation();

  useEffect(() => {
    if (!consultation.caseId) {
      return undefined;
    }

    const timers = analysisSteps.map((_, index) =>
      window.setTimeout(() => {
        setActiveIndex(index);
      }, 650 * (index + 1)),
    );

    const finishTimer = window.setTimeout(() => {
      setFinished(true);
      setReportReady(true);
    }, 650 * analysisSteps.length + 650);

    const navigationTimer = window.setTimeout(() => {
      router.push("/report");
    }, 650 * analysisSteps.length + 1650);

    return () => {
      timers.forEach((timer) => window.clearTimeout(timer));
      window.clearTimeout(finishTimer);
      window.clearTimeout(navigationTimer);
    };
  }, [consultation.caseId, router]);

  useEffect(() => {
    if (isFinished) {
      setCurrentStep(6);
      return;
    }

    setCurrentStep(activeIndex >= 3 ? 5 : 4);
  }, [activeIndex, isFinished]);

  if (!consultation.caseId) {
    return (
      <PageContainer>
        <SectionCard eyebrow="Analysis unavailable" title="Start a case first.">
          <p className="section-intro">
            The mock analysis requires a case intake record. Return to the
            consultation page to begin a new triage flow.
          </p>
          <Button onClick={() => router.push("/consultation")}>
            Go to Consultation
          </Button>
        </SectionCard>
      </PageContainer>
    );
  }

  const completedSteps = [1, 2, 3];
  if (activeIndex >= 3) {
    completedSteps.push(4);
  }
  if (isFinished) {
    completedSteps.push(5);
  }

  return (
    <PageContainer>
      <div className="page-layout page-layout--with-sidebar">
        <div className="page-layout__content">
          <SectionCard
            eyebrow="Analysis in progress"
            title="FinSight is comparing the case against curated evidence."
          >
            <p className="section-intro">
              FinSight is comparing the case against curated fish-health
              evidence. No diagnosis is considered confirmed without
              appropriate testing.
            </p>

            <ol className="analysis-steps">
              {analysisSteps.map((step, index) => {
                const isActive = index === activeIndex && !isFinished;
                const isComplete = index < activeIndex || isFinished;

                return (
                  <li
                    key={step}
                    className={[
                      "analysis-steps__item",
                      isActive ? "is-active" : "",
                      isComplete ? "is-complete" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                  >
                    <span className="analysis-steps__icon">
                      {isComplete ? (
                        <CheckCircle2 size={18} aria-hidden="true" />
                      ) : isActive ? (
                        <Loader2 size={18} className="spin" aria-hidden="true" />
                      ) : (
                        <span>{index + 1}</span>
                      )}
                    </span>
                    <div>
                      <h3>{step}</h3>
                      <p>
                        {isComplete
                          ? "Complete"
                          : isActive
                            ? "Running now"
                            : "Queued"}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ol>

            {isFinished ? (
              <div className="analysis-complete">
                <p>The mock report is ready. Redirecting to the report page.</p>
                <Button onClick={() => router.push("/report")}>
                  View Assessment Report
                </Button>
              </div>
            ) : null}
          </SectionCard>
        </div>

        <div className="page-layout__sidebar">
          <ProgressPanel
            currentStep={isFinished ? 6 : activeIndex >= 3 ? 5 : 4}
            completedSteps={completedSteps}
          />
        </div>
      </div>
    </PageContainer>
  );
}
