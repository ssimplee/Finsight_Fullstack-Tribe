import React, { useEffect, useRef, useState } from "react";
import { ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";
import PageContainer from "../components/layout/PageContainer";
import ProgressPanel from "../components/layout/ProgressPanel";
import SectionCard from "../components/ui/SectionCard";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import ImageUpload from "../components/consultation/ImageUpload";
import CaseForm from "../components/consultation/CaseForm";
import FollowUpQuestion from "../components/consultation/FollowUpQuestion";
import { useConsultation } from "../context/ConsultationContext";
import { mockObservation } from "../data/mockCase";
import {
  createCase,
  getFollowUpQuestions,
  requestAnalysis,
  submitFollowUpAnswers,
  uploadFishImage,
} from "../services/api";

const waterQualityLabels = {
  temperatureC: "Temperature",
  ph: "pH",
  dissolvedOxygenMgL: "Dissolved oxygen",
  ammoniaMgL: "Ammonia",
  nitriteMgL: "Nitrite",
  nitrateMgL: "Nitrate",
};

function validateCaseForm(caseForm) {
  const nextErrors = {};

  if (!caseForm.species.trim()) {
    nextErrors.species = "Species is required before the case can be triaged.";
  }

  if (!caseForm.lifeStage) {
    nextErrors.lifeStage = "Select the current life stage.";
  }

  if (
    caseForm.visibleSymptoms.length === 0 &&
    caseForm.behavioralSigns.length === 0 &&
    !caseForm.additionalObservations.trim()
  ) {
    nextErrors.clinicalSigns =
      "Add at least one visible symptom, behavioral sign, or additional observation.";
  }

  Object.entries(caseForm.waterQuality).forEach(([field, value]) => {
    if (value !== "" && Number(value) < 0) {
      nextErrors[field] = `${waterQualityLabels[field]} cannot be negative.`;
    }
  });

  if (
    caseForm.waterQuality.ph !== "" &&
    (Number(caseForm.waterQuality.ph) < 0 ||
      Number(caseForm.waterQuality.ph) > 14)
  ) {
    nextErrors.ph = "pH must stay between 0 and 14.";
  }

  return nextErrors;
}

export default function ConsultationPage() {
  const router = useRouter();
  const followUpSectionRef = useRef(null);
  const [errors, setErrors] = useState({});
  const [followUpQuestions, setFollowUpQuestions] = useState([]);
  const [isSubmitting, setSubmitting] = useState(false);
  const [submissionMessage, setSubmissionMessage] = useState("");
  const [submissionError, setSubmissionError] = useState("");
  const {
    consultation,
    loadSampleCase,
    setAnalysisRequested,
    setCaseId,
    setConsultationStage,
    setCurrentStep,
    setFollowUpAnswer,
    setObservation,
    setUploadedImage,
    toggleMultiSelect,
    updateCaseField,
    updateWaterQualityField,
  } = useConsultation();

  const phValue = consultation.caseForm.waterQuality.ph;
  const phWarning =
    phValue !== "" && (Number(phValue) < 6 || Number(phValue) > 9)
      ? "This pH value is outside a common tilapia production range. Please confirm the measurement."
      : "";

  useEffect(() => {
    setCurrentStep(consultation.consultationStage === "followUp" ? 3 : 1);
  }, [consultation.consultationStage]);

  useEffect(() => {
    if (consultation.consultationStage === "followUp") {
      followUpSectionRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  }, [consultation.consultationStage]);

  const handleContinue = async (event) => {
    event.preventDefault();

    const nextErrors = validateCaseForm(consultation.caseForm);
    setErrors(nextErrors);
    setSubmissionError("");

    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    setSubmitting(true);

    try {
      const response = await createCase(consultation.caseForm);
      setCaseId(response.caseId);

      if (consultation.imageFile) {
        await uploadFishImage(response.caseId, consultation.imageFile);
      }

      const questions = await getFollowUpQuestions(response.caseId);
      setFollowUpQuestions(questions);
      setObservation(mockObservation);
      setConsultationStage("followUp");
      setSubmissionMessage(
        consultation.imageFile
          ? "Image preview preserved. Review the observation summary and answer the follow-up questions."
          : "Continuing without an uploaded image. The observation summary remains mock data for the prototype.",
      );
    } catch (error) {
      setSubmissionError(
        "FinSight could not prepare the case record. Please review the inputs and try again.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleRunAnalysis = async () => {
    setSubmissionError("");
    setSubmitting(true);

    try {
      await submitFollowUpAnswers(
        consultation.caseId,
        consultation.followUpAnswers,
      );
      await requestAnalysis(consultation.caseId);
      setAnalysisRequested(true);
      router.push("/analysis");
    } catch (error) {
      setSubmissionError(
        "FinSight could not queue the mock analysis. Return to the intake step and try again.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  const completedSteps =
    consultation.consultationStage === "followUp" ? [1, 2] : [];

  return (
    <PageContainer>
      <div className="page-layout page-layout--with-sidebar">
        <div className="page-layout__content">
          <SectionCard
            eyebrow="Case intake"
            title="Capture the case before FinSight compares causes."
          >
            <form onSubmit={handleContinue}>
              <div className="stack-lg">
                {consultation.isSampleCase ? (
                  <div className="inline-message inline-message--info">
                    Sample case loaded. You can continue the full demo without
                    uploading an image.
                  </div>
                ) : null}

                <ImageUpload
                  error={errors.image}
                  imageAltText={consultation.imageAltText}
                  imagePreviewUrl={consultation.imagePreviewUrl}
                  onFileSelected={setUploadedImage}
                  onLoadSampleCase={loadSampleCase}
                  onRemoveImage={() => setUploadedImage(null)}
                />

                <CaseForm
                  caseForm={consultation.caseForm}
                  errors={errors}
                  onFieldChange={updateCaseField}
                  onToggleSelection={toggleMultiSelect}
                  onWaterQualityChange={updateWaterQualityField}
                  phWarning={phWarning}
                />

                {submissionError ? (
                  <div className="inline-message inline-message--error">
                    {submissionError}
                  </div>
                ) : null}

                <div className="form-actions">
                  <Button
                    type="submit"
                    loading={isSubmitting}
                    iconRight={<ArrowRight size={16} aria-hidden="true" />}
                  >
                    Continue to Image Observation
                  </Button>
                </div>
              </div>
            </form>
          </SectionCard>

          {consultation.consultationStage === "followUp" && consultation.observation ? (
            <div ref={followUpSectionRef} className="stack-lg">
              <SectionCard
                eyebrow="Image observation"
                title="Observed findings from the mock image review"
                actions={<Badge tone="warning">{consultation.observation.label}</Badge>}
              >
                {submissionMessage ? (
                  <p className="section-intro">{submissionMessage}</p>
                ) : null}

                <div className="observation-grid">
                  <div>
                    <h3>Visible findings detected</h3>
                    <ul className="report-list">
                      {consultation.observation.findings.map((finding) => (
                        <li key={finding}>{finding}</li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h3>Image limitations</h3>
                    <ul className="report-list">
                      {consultation.observation.limitations.map((limitation) => (
                        <li key={limitation}>{limitation}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </SectionCard>

              <SectionCard
                eyebrow="Adaptive follow-up"
                title="Answer additional questions before the evidence analysis runs."
              >
                <div className="stack-lg">
                  {followUpQuestions.map((question) => (
                    <FollowUpQuestion
                      key={question.id}
                      answer={consultation.followUpAnswers[question.id]}
                      onChange={(nextValue) =>
                        setFollowUpAnswer(question.id, nextValue)
                      }
                      question={question}
                    />
                  ))}

                  {submissionError ? (
                    <div className="inline-message inline-message--error">
                      {submissionError}
                    </div>
                  ) : null}

                  <div className="form-actions form-actions--split">
                    <Button
                      variant="ghost"
                      onClick={() => setConsultationStage("intake")}
                    >
                      Back to Case Intake
                    </Button>
                    <Button onClick={handleRunAnalysis} loading={isSubmitting}>
                      Run Evidence Analysis
                    </Button>
                  </div>
                </div>
              </SectionCard>
            </div>
          ) : null}
        </div>

        <div className="page-layout__sidebar">
          <ProgressPanel
            currentStep={consultation.consultationStage === "followUp" ? 3 : 1}
            completedSteps={completedSteps}
          />
        </div>
      </div>
    </PageContainer>
  );
}
