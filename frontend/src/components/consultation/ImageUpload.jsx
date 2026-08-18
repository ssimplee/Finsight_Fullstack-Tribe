import React, { useRef, useState } from "react";
import { Image, RefreshCcw, Trash2, Upload } from "lucide-react";
import Button from "../ui/Button";

const acceptedTypes = ["image/jpeg", "image/png"];
const largeFileThreshold = 8 * 1024 * 1024;

export default function ImageUpload({
  error,
  imageAltText,
  imagePreviewUrl,
  onFileSelected,
  onLoadSampleCase,
  onRemoveImage,
}) {
  const inputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  const [localMessage, setLocalMessage] = useState("");

  const validateAndForwardFile = (file) => {
    if (!file) {
      return;
    }

    if (!acceptedTypes.includes(file.type)) {
      setLocalMessage("Please upload a JPG or PNG image for the case preview.");
      return;
    }

    if (file.size > largeFileThreshold) {
      setLocalMessage(
        "Large image files may preview slowly. Consider using a smaller image if available.",
      );
    } else {
      setLocalMessage("");
    }

    onFileSelected(file);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragActive(false);
    validateAndForwardFile(event.dataTransfer.files?.[0]);
  };

  return (
    <div className="image-upload">
      <div
        className={[
          "image-upload__dropzone",
          dragActive ? "is-drag-active" : "",
          error ? "has-error" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        onDragEnter={(event) => {
          event.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={(event) => {
          event.preventDefault();
          setDragActive(false);
        }}
        onDragOver={(event) => {
          event.preventDefault();
        }}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".jpg,.jpeg,.png"
          className="sr-only"
          onChange={(event) => validateAndForwardFile(event.target.files?.[0])}
        />

        <div className="image-upload__copy">
          <span className="image-upload__icon">
            <Upload size={22} aria-hidden="true" />
          </span>
          <div>
            <h3>Upload a clear image of the affected fish</h3>
            <p>
              JPG or PNG, preferably showing the full body and visible lesions
            </p>
          </div>
        </div>

        <div className="image-upload__actions">
          <Button
            variant="secondary"
            onClick={() => inputRef.current?.click()}
            iconLeft={<Image size={16} aria-hidden="true" />}
          >
            Choose Image
          </Button>
          <Button variant="ghost" onClick={onLoadSampleCase}>
            Load Sample Case
          </Button>
        </div>
      </div>

      {error ? <p className="field-error">{error}</p> : null}
      {localMessage ? <p className="field-hint">{localMessage}</p> : null}

      {imagePreviewUrl ? (
        <div className="image-upload__preview-card">
          <div className="image-upload__preview-header">
            <h3>Image preview</h3>
            <div className="image-upload__preview-actions">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => inputRef.current?.click()}
                iconLeft={<RefreshCcw size={14} aria-hidden="true" />}
              >
                Replace
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={onRemoveImage}
                iconLeft={<Trash2 size={14} aria-hidden="true" />}
              >
                Remove
              </Button>
            </div>
          </div>

          <img
            src={imagePreviewUrl}
            alt={imageAltText || "Uploaded fish case preview"}
            className="image-upload__preview"
          />
        </div>
      ) : null}
    </div>
  );
}
