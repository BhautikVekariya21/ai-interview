type LogoMarkProps = {
  className?: string;
  title?: string;
};

export default function LogoMark({ className, title = "interviewer.ai" }: LogoMarkProps) {
  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden={title ? undefined : true}
      role={title ? "img" : undefined}
    >
      {title ? <title>{title}</title> : null}
      <defs>
        <linearGradient id="logo-mark-gradient" x1="10" y1="8" x2="54" y2="56" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#7C3AED" />
          <stop offset="0.55" stopColor="#8B5CF6" />
          <stop offset="1" stopColor="#EC4899" />
        </linearGradient>
      </defs>
      <rect x="4" y="4" width="56" height="56" rx="12" fill="url(#logo-mark-gradient)" />
      <rect x="5" y="5" width="54" height="54" rx="11" stroke="rgba(255,255,255,0.16)" />
      <circle cx="32" cy="32" r="15" stroke="white" strokeWidth="4" />
      <circle cx="32" cy="32" r="8" stroke="white" strokeWidth="4" />
      <circle cx="32" cy="32" r="3.5" fill="white" />
      <path
        d="M32 12V18M32 46V52M12 32H18M46 32H52"
        stroke="white"
        strokeWidth="4"
        strokeLinecap="round"
      />
    </svg>
  );
}
