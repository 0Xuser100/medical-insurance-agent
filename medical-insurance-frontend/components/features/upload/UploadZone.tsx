"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useRouter } from "@/i18n/navigation";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils/cn";
import { useUploadPrescription, useProcessJob } from "@/lib/api/mutations";
import { parseError } from "@/lib/errors";
import type { UploadResponse } from "@/lib/schemas/validation";

const ACCEPTED_TYPES: Record<string, string[]> = {
  "image/jpeg": [".jpg", ".jpeg"],
  "image/png": [".png"],
  "image/gif": [".gif"],
  "image/webp": [".webp"],
  "image/tiff": [".tif", ".tiff"],
  "application/pdf": [".pdf"],
};

const MAX_SIZE = 10 * 1024 * 1024; // 10MB

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function UploadZone() {
  const t = useTranslations("upload");
  const router = useRouter();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [uploadInfo, setUploadInfo] = useState<UploadResponse | null>(null);

  const uploadMutation = useUploadPrescription();
  const processMutation = useProcessJob();

  const isUploading = uploadMutation.isPending || processMutation.isPending;

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      setErrorMsg(null);
      setUploadInfo(null);
      const file = acceptedFiles[0];
      if (!file) return;

      try {
        // Step 1: Upload
        const uploadResult = await uploadMutation.mutateAsync(file);
        setUploadInfo(uploadResult);

        // Step 2: Trigger processing
        await processMutation.mutateAsync(uploadResult.job_id);

        // Step 3: Navigate to status page
        router.push(`/prescriptions/status?jobId=${uploadResult.job_id}`);
      } catch (err) {
        const parsed = parseError(err);
        switch (parsed.type) {
          case "NETWORK_ERROR":
            setErrorMsg(t("errorNetwork"));
            break;
          case "API_ERROR":
            setErrorMsg(parsed.detail ?? t("errorUploadFailed"));
            break;
          case "VALIDATION_ERROR":
            setErrorMsg(t("errorUploadFailed"));
            break;
          default:
            setErrorMsg(t("errorUploadFailed"));
        }
      }
    },
    [uploadMutation, processMutation, router, t],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_SIZE,
    multiple: false,
    disabled: isUploading,
    onDropRejected: (rejections) => {
      const rejection = rejections[0];
      if (rejection?.errors.some((e) => e.code === "file-too-large")) {
        setErrorMsg(t("errorTooLarge"));
      } else {
        setErrorMsg(t("errorInvalidType"));
      }
    },
  });

  return (
    <div>
      <div
        {...getRootProps()}
        className={cn(
          "cursor-pointer rounded-xl border-2 border-dashed p-12 text-center transition-colors",
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-border hover:border-primary/50 hover:bg-gray-50",
          isUploading && "pointer-events-none opacity-60",
        )}
      >
        <input {...getInputProps()} />

        {isUploading ? (
          <div className="space-y-3">
            <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-primary" />
            <p className="text-sm font-medium text-foreground">
              {uploadMutation.isPending ? t("uploading") : t("processing")}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
              <svg
                width="28"
                height="28"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className="text-primary"
              >
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <div>
              <p className="text-base font-medium text-foreground">
                {t("dragDrop")}
              </p>
              <p className="mt-1 text-sm text-muted">{t("or")}</p>
              <span className="mt-2 inline-block rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">
                {t("browse")}
              </span>
            </div>
            <p className="text-xs text-muted">{t("maxSize")}</p>
          </div>
        )}
      </div>

      {uploadInfo && !errorMsg && (
        <div className="mt-3 rounded-lg bg-green-50 p-3 text-sm text-green-700">
          <p className="font-medium">{uploadInfo.message}</p>
          <p className="mt-1 text-xs text-green-600">
            {uploadInfo.filename} ({formatBytes(uploadInfo.file_size)})
          </p>
        </div>
      )}

      {errorMsg && (
        <div className="mt-3 rounded-lg bg-red-50 p-3 text-center text-sm text-red-700">
          {errorMsg}
        </div>
      )}
    </div>
  );
}
