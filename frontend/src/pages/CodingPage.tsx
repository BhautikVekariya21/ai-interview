/**
 * CodingPage — Full-Screen Code Execution IDE Page.
 */

import CodeSandbox from "@/components/CodeSandbox";

export default function CodingPage() {
  return (
    <div className="h-screen w-screen bg-background overflow-hidden flex flex-col">
      <CodeSandbox />
    </div>
  );
}
