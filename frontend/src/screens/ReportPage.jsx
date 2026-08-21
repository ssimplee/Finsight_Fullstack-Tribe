import React, { useEffect, useState } from "react";
import { Clock3, Printer, ShieldAlert } from "lucide-react";
import { useRouter } from "next/navigation";
import PageContainer from "../components/layout/PageContainer";
import SectionCard from "../components/ui/SectionCard";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import DiagnosisCard from "../components/report/DiagnosisCard";
import EvidenceCompleteness from "../components/report/EvidenceCompleteness";
import EvidenceList from "../components/report/EvidenceList";
import MissingInformation from "../components/report/MissingInformation";
import ActionList from "../components/report/ActionList";
import SourceModal from "../components/report/SourceModal";
import { useConsultation } from "../context/ConsultationContext";
import { getReport } from "../services/api";

function formatTimestamp(timestamp) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(timestamp));
}

function EvidenceBucket({ items, title }) {
  return (
    <div className="visual-bucket">
      <h3>{title}</h3>
      <div className="visual-bucket__items">
        {items.map((item) => (
          <div key={item.id} className="visual-bucket__item">
            <Badge tone={item.label === "OBSERVED" ? "success" : "default"}>
              {item.label}
            </Badge>
            <span>{item.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ReportPage() {
  const router = useRouter();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedSourceId, setSelectedSourceId] = useState("");
  const { consultation, resetConsultation, setCurrentStep } = useConsultation();

  useEffect(() => {
    setCurrentStep(6);
  }, []);

  useEffect(() => {
    let isMounted = true;

    const loadReport = async () => {
      if (!consultation.caseId) {
        setError("No mock case is available. Start a new consultation first.");
        setLoading(false);
        return;
      }

      try {
        const reportResponse = await getReport(consultation.caseId);

        if (isMounted) {
          setReport(reportResponse);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(
            "FinSight could not load the assessment report. Restart the consultation to rebuild the case state.",
          );
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadReport();

    return () => {
      isMounted = false;
    };
  }, [consultation.caseId]);

  const handleRestart = () => {
    resetConsultation();
    router.push("/consultation");
  };

  if (loading) {
    return (
      <PageContainer>
        <SectionCard eyebrow="Loading report" title="Preparing the assessment.">
          <p className="section-intro">
            FinSight is loading the assessment report and evidence summary.
          </p>
        </SectionCard>
      </PageContainer>
    );
  }

  if (error || !report) {
    return (
      <PageContainer>
        <SectionCard eyebrow="Report unavailable" title="The assessment is missing.">
          <p className="section-intro">{error}</p>
          <Button onClick={() => router.push("/consultation")}>
            Return to Consultation
          </Button>
        </SectionCard>
      </PageContainer>
    );
  }

  const selectedSource = report.sources.find(
    (source) => source.id === selectedSourceId,
  );

  return (
    <PageContainer className="report-page">
      <div className="report-summary">
        <div>
          <p className="report-summary__eyebrow">Assessment report</p>
          <h1>Fish-health triage assessment</h1>
        </div>

        <div className="report-summary__actions print-hidden">
          <Button variant="secondary" onClick={handleRestart}>
            Start New Consultation
          </Button>
          <Button
            variant="ghost"
            onClick={() => window.print()}
            iconLeft={<Printer size={16} aria-hidden="true" />}
          >
            Print Report
          </Button>
        </div>
      </div>

      <div className="safety-banner">
        <ShieldAlert size={18} aria-hidden="true" />
        <p>
          This assessment is a decision-support result, not a confirmed
          diagnosis. Laboratory testing or professional examination may still be
          required.
        </p>
      </div>

      {report.summary ? (
        <SectionCard eyebrow="Clinical Summary" title="Assessment conclusion">
          <p className="section-intro" style={{ whiteSpace: "pre-wrap" }}>
            {report.summary}
          </p>
        </SectionCard>
      ) : null}

      <div className="summary-grid">
        <div className="summary-grid__item">
          <span>Case ID</span>
          <strong>{report.caseId}</strong>
        </div>
        <div className="summary-grid__item">
          <span>Species</span>
          <strong>{report.fish.species}</strong>
        </div>
        <div className="summary-grid__item">
          <span>Assessment status</span>
          <strong>{report.status.assessment}</strong>
        </div>
        <div className="summary-grid__item">
          <span>Confirmation status</span>
          <strong>{report.status.confirmation}</strong>
        </div>
        <div className="summary-grid__item">
          <span>Uncertainty</span>
          <strong>{report.status.uncertainty}</strong>
        </div>
        <div className="summary-grid__item">
          <span>
            <Clock3 size={14} aria-hidden="true" />
            Generated
          </span>
          <strong>{formatTimestamp(report.generatedAt)}</strong>
        </div>
      </div>

      <nav className="report-anchor-nav print-hidden" aria-label="Report sections">
        <a href="#visual-assessment">Visual Assessment</a>
        <a href="#differential-assessment">Differential Assessment</a>
        <a href="#evidence-review">Evidence Review</a>
        <a href="#recommended-actions">Recommended Actions</a>
      </nav>

      <section id="visual-assessment">
        <SectionCard eyebrow="Visual Assessment" title="Observed and reported signals">
          <div className="visual-grid">
            <EvidenceBucket
              title="Observed"
              items={report.observations.visual}
            />
            <EvidenceBucket
              title="User-reported"
              items={report.observations.userReported}
            />
            <EvidenceBucket title="Unknown" items={report.observations.unknown} />
          </div>
        </SectionCard>
      </section>

      <section id="differential-assessment">
        <SectionCard
          eyebrow="Differential Assessment"
          title="Possible causes compared side by side"
        >
          <div className="diagnosis-grid">
            {report.differential.map((item) => (
              <DiagnosisCard key={item.id} item={item} />
            ))}
          </div>
        </SectionCard>
      </section>

      <section id="evidence-review">
        <div className="report-two-column">
          <SectionCard eyebrow="Evidence Review" title="Evidence Completeness">
            <EvidenceCompleteness items={report.evidenceCompleteness} />
          </SectionCard>

          <SectionCard eyebrow="Missing Information" title="Still needed">
            <MissingInformation items={report.missingInformation} />
          </SectionCard>
        </div>

        <SectionCard eyebrow="Evidence Sources" title="Evidence source summaries">
          <EvidenceList
            items={report.sources}
            onSelect={(sourceId) => setSelectedSourceId(sourceId)}
          />
        </SectionCard>
      </section>

      <section id="recommended-actions">
        <div className="report-two-column">
          <SectionCard
            eyebrow="Recommended Confirmation"
            title="Suggested checks"
          >
            <ActionList items={report.recommendedConfirmation} />
          </SectionCard>

          <SectionCard eyebrow="Safe Next Actions" title="Immediate safeguards">
            <ActionList items={report.recommendedActions} />
          </SectionCard>
        </div>

        <SectionCard eyebrow="Escalation" title="When expert support is needed" tone="warning">
          <ActionList items={report.escalation} />
        </SectionCard>
      </section>

      <SourceModal
        source={selectedSource}
        onClose={() => setSelectedSourceId("")}
      />
    </PageContainer>
  );
}
