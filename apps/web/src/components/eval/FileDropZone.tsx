/** Drag & drop zone for file upload with textarea fallback. */

import { useState, useRef, useCallback, type DragEvent } from "react";
import { Upload, FileText, X } from "lucide-react";
import { cn } from "../../lib/cn";

interface Props {
  label: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  accept?: string;
  maxSizeKB?: number;
}

export default function FileDropZone({
  label,
  placeholder,
  value,
  onChange,
  accept = ".md,.yaml,.yml",
  maxSizeKB = 100,
}: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      setError(null);
      const sizeKB = file.size / 1024;
      if (sizeKB > maxSizeKB) {
        setError(
          `File exceeds ${maxSizeKB}KB limit (${Math.round(sizeKB)}KB). Reduce the content.`,
        );
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target?.result;
        if (typeof text === "string") {
          onChange(text);
          setFileName(file.name);
        }
      };
      reader.readAsText(file);
    },
    [maxSizeKB, onChange],
  );

  const onDragOver = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const clearFile = () => {
    setFileName(null);
    onChange("");
    setError(null);
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
        {fileName && (
          <button
            onClick={clearFile}
            className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600"
          >
            <FileText className="h-3 w-3" />
            {fileName}
            <X className="h-3 w-3" />
          </button>
        )}
      </div>

      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={cn(
          "relative rounded-lg border-2 border-dashed transition-colors",
          isDragging
            ? "border-indigo-400 bg-indigo-50 dark:border-indigo-500 dark:bg-indigo-950/30"
            : "border-gray-300 dark:border-gray-600",
        )}
      >
        {!value && (
          <div
            className="flex cursor-pointer flex-col items-center gap-2 p-6"
            onClick={() => fileRef.current?.click()}
            onKeyDown={(e) =>
              e.key === "Enter" && fileRef.current?.click()
            }
            role="button"
            tabIndex={0}
          >
            <Upload className="h-8 w-8 text-gray-400" />
            <p className="text-sm text-gray-500">
              Drop a file here or{" "}
              <span className="text-indigo-600 underline">browse</span>
            </p>
            <p className="text-xs text-gray-400">
              {accept} &middot; Max {maxSizeKB}KB
            </p>
          </div>
        )}

        <input
          ref={fileRef}
          type="file"
          accept={accept}
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />

        {(value || isDragging) && (
          <textarea
            value={value}
            onChange={(e) => {
              onChange(e.target.value);
              setFileName(null);
            }}
            placeholder={placeholder}
            rows={8}
            className="w-full resize-y rounded-lg border-0 bg-transparent p-3 font-mono text-sm text-gray-900 placeholder-gray-400 focus:ring-0 dark:text-gray-100"
          />
        )}
      </div>

      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
