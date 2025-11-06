export function UploadIcon({ className }: { className?: string }) {
  return (
    <svg
      width="64"
      height="64"
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path
        d="M32 44V20M32 20L22 30M32 20L42 30"
        stroke="#f6339a"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M16 50H48"
        stroke="#f6339a"
        strokeWidth="4"
        strokeLinecap="round"
      />
    </svg>
  );
}
