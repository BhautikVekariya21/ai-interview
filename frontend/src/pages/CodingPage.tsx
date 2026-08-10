/**
 * CodingPage — Full-Screen Code Execution IDE Page.
 */

import CodeSandbox from "@/components/CodeSandbox";
import Seo from "@/components/Seo";

export default function CodingPage() {
  return (
    <div className="h-screen w-screen bg-background overflow-hidden flex flex-col">
      <Seo
        title="Coding practice"
        description="Practice coding interview problems in a full-screen editor with multi-language support and instant feedback."
        path="/coding"
        noindex
      />
      <CodeSandbox />
    </div>
  );
}
