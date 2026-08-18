import React, { createContext, useContext, useEffect, useState } from "react";
import {
  createInitialConsultationState,
  sampleCaseData,
} from "../data/mockCase";

const ConsultationContext = createContext(null);

function revokePreviewUrl(previewUrl) {
  if (previewUrl && previewUrl.startsWith("blob:")) {
    URL.revokeObjectURL(previewUrl);
  }
}

export function ConsultationProvider({ children }) {
  const [consultation, setConsultation] = useState(
    createInitialConsultationState(),
  );

  useEffect(() => {
    return () => {
      revokePreviewUrl(consultation.imagePreviewUrl);
    };
  }, [consultation.imagePreviewUrl]);

  const updateCaseField = (field, value) => {
    setConsultation((currentState) => ({
      ...currentState,
      caseForm: {
        ...currentState.caseForm,
        [field]: value,
      },
    }));
  };

  const updateWaterQualityField = (field, value) => {
    setConsultation((currentState) => ({
      ...currentState,
      caseForm: {
        ...currentState.caseForm,
        waterQuality: {
          ...currentState.caseForm.waterQuality,
          [field]: value,
        },
      },
    }));
  };

  const toggleMultiSelect = (field, value) => {
    setConsultation((currentState) => {
      const values = currentState.caseForm[field];
      const nextValues = values.includes(value)
        ? values.filter((entry) => entry !== value)
        : [...values, value];

      return {
        ...currentState,
        caseForm: {
          ...currentState.caseForm,
          [field]: nextValues,
        },
      };
    });
  };

  const setUploadedImage = (file) => {
    setConsultation((currentState) => {
      revokePreviewUrl(currentState.imagePreviewUrl);

      if (!file) {
        return {
          ...currentState,
          imageFile: null,
          imagePreviewUrl: "",
          imageAltText: "",
        };
      }

      const imagePreviewUrl = URL.createObjectURL(file);

      return {
        ...currentState,
        imageFile: file,
        imagePreviewUrl,
        imageAltText: `Uploaded fish case image: ${file.name}`,
        isSampleCase: false,
      };
    });
  };

  const loadSampleCase = () => {
    setConsultation((currentState) => {
      revokePreviewUrl(currentState.imagePreviewUrl);

      return {
        ...createInitialConsultationState(),
        caseForm: {
          ...sampleCaseData.caseForm,
        },
        followUpAnswers: {
          ...sampleCaseData.followUpAnswers,
        },
        isSampleCase: true,
      };
    });
  };

  const setFollowUpAnswer = (questionId, nextValue) => {
    setConsultation((currentState) => ({
      ...currentState,
      followUpAnswers: {
        ...currentState.followUpAnswers,
        [questionId]: {
          ...currentState.followUpAnswers[questionId],
          ...nextValue,
        },
      },
    }));
  };

  const setObservation = (observation) => {
    setConsultation((currentState) => ({
      ...currentState,
      observation,
    }));
  };

  const setConsultationStage = (consultationStage) => {
    setConsultation((currentState) => ({
      ...currentState,
      consultationStage,
    }));
  };

  const setCurrentStep = (currentStep) => {
    setConsultation((currentState) => ({
      ...currentState,
      currentStep,
    }));
  };

  const setCaseId = (caseId) => {
    setConsultation((currentState) => ({
      ...currentState,
      caseId,
    }));
  };

  const setAnalysisRequested = (analysisRequested) => {
    setConsultation((currentState) => ({
      ...currentState,
      analysisRequested,
    }));
  };

  const setReportReady = (reportReady) => {
    setConsultation((currentState) => ({
      ...currentState,
      reportReady,
    }));
  };

  const resetConsultation = () => {
    setConsultation((currentState) => {
      revokePreviewUrl(currentState.imagePreviewUrl);
      return createInitialConsultationState();
    });
  };

  return (
    <ConsultationContext.Provider
      value={{
        consultation,
        updateCaseField,
        updateWaterQualityField,
        toggleMultiSelect,
        setUploadedImage,
        loadSampleCase,
        setFollowUpAnswer,
        setObservation,
        setConsultationStage,
        setCurrentStep,
        setCaseId,
        setAnalysisRequested,
        setReportReady,
        resetConsultation,
      }}
    >
      {children}
    </ConsultationContext.Provider>
  );
}

export function useConsultation() {
  const context = useContext(ConsultationContext);

  if (!context) {
    throw new Error("useConsultation must be used within ConsultationProvider.");
  }

  return context;
}
