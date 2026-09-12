const paths = {
  arrow: "M4 12h16m-6-6 6 6-6 6",
  copy: "M9 9h11v11H9zM15 9V4H4v11h5",
  check: "m5 12 4 4L19 6",
  plus: "M12 5v14M5 12h14",
  close: "m6 6 12 12M6 18 18 6",
  shield: "m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6zM8 12l3 3 5-6",
  warning: "m12 3 10 18H2zM12 9v5m0 3v.1",
  spark: "m12 2 3 7 7 3-7 3-3 7-3-7-7-3 7-3z",
};
export function Icon({ name }: { name: keyof typeof paths }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d={paths[name]} />
    </svg>
  );
}
