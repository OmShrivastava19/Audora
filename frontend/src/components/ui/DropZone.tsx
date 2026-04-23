import { useCallback, type ReactNode } from 'react';
import { useDropzone, type Accept } from 'react-dropzone';
import { Upload, FileAudio, FileText, X } from 'lucide-react';
import { cn, formatFileSize } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

interface DropZoneProps {
  onFileSelect: (file: File) => void;
  accept?: Accept;
  maxSize?: number;
  label: string;
  sublabel?: string;
  icon?: ReactNode;
  selectedFile?: File | null;
  onClear?: () => void;
  className?: string;
}

export function DropZone({
  onFileSelect,
  accept,
  maxSize = 500 * 1024 * 1024,
  label,
  sublabel,
  icon,
  selectedFile,
  onClear,
  className,
}: DropZoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFileSelect(acceptedFiles[0]);
      }
    },
    [onFileSelect]
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept,
    maxSize,
    multiple: false,
  });

  const rejected = fileRejections.length > 0;

  return (
    <div className={cn('space-y-2', className)}>
      <div
        {...getRootProps()}
        className={cn(
          'relative rounded-xl border-2 border-dashed p-8 text-center transition-all duration-300 cursor-pointer',
          'hover:border-accent/50 hover:bg-accent/[0.03]',
          isDragActive && 'border-accent bg-accent/[0.06] scale-[1.01]',
          rejected && 'border-accent2/50',
          !isDragActive && !rejected && 'border-border',
          selectedFile && 'border-accent/40 bg-accent/[0.04]'
        )}
      >
        <input {...getInputProps()} aria-label={label} />
        <AnimatePresence mode="wait">
          {selectedFile ? (
            <motion.div
              key="selected"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="flex flex-col items-center gap-3"
            >
              <div className="w-12 h-12 rounded-xl bg-accent-muted flex items-center justify-center">
                <FileAudio className="w-6 h-6 text-accent" />
              </div>
              <div>
                <p className="text-sm font-semibold text-text truncate max-w-[260px]">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-muted mt-0.5">{formatFileSize(selectedFile.size)}</p>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="flex flex-col items-center gap-3"
            >
              <div className="w-12 h-12 rounded-xl bg-surface-hover flex items-center justify-center">
                {icon || <Upload className="w-6 h-6 text-muted" />}
              </div>
              <div>
                <p className="text-sm font-medium text-text-secondary">{label}</p>
                {sublabel && <p className="text-xs text-muted mt-0.5">{sublabel}</p>}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {selectedFile && onClear && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onClear();
          }}
          className="flex items-center gap-1.5 text-xs text-muted hover:text-accent2 transition-colors"
          aria-label="Clear selected file"
        >
          <X className="w-3 h-3" /> Clear
        </button>
      )}

      {rejected && (
        <p className="text-xs text-accent2">
          File rejected — check format and size (max {formatFileSize(maxSize)}).
        </p>
      )}
    </div>
  );
}

export function SyllabusDropZone(props: Omit<DropZoneProps, 'accept' | 'label' | 'sublabel' | 'icon'>) {
  return (
    <DropZone
      {...props}
      accept={{ 'application/pdf': ['.pdf'], 'text/plain': ['.txt'] }}
      label="Upload syllabus (PDF or TXT)"
      sublabel="Optional — enables coverage heatmap and syllabus grounding"
      icon={<FileText className="w-6 h-6 text-muted" />}
    />
  );
}

export function LectureDropZone(props: Omit<DropZoneProps, 'accept' | 'label' | 'sublabel' | 'icon'>) {
  return (
    <DropZone
      {...props}
      accept={{
        'audio/*': ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.webm', '.mpeg', '.mpga'],
        'video/mp4': ['.mp4'],
      }}
      label="Upload lecture recording"
      sublabel="Audio or video — MP3, MP4, WAV, M4A, OGG, FLAC, WEBM"
      icon={<FileAudio className="w-6 h-6 text-muted" />}
    />
  );
}
