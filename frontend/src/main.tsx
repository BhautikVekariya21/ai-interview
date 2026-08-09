import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ClerkProvider } from "@clerk/react";
import App from "./App.tsx";
import { appPath } from "./lib/paths";
import "./index.css";

const clerkPubKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string | undefined;

if (!clerkPubKey) {
  console.error(
    "[Clerk] Missing VITE_CLERK_PUBLISHABLE_KEY. " +
      "Add it to the repo-root .env (Vite envDir is the monorepo root, not frontend/)."
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ClerkProvider
      publishableKey={clerkPubKey}
      afterSignOutUrl={appPath("/")}
      signInUrl={appPath("/auth")}
      signUpUrl={appPath("/auth?mode=signup")}
      signInFallbackRedirectUrl={appPath("/app")}
      signUpFallbackRedirectUrl={appPath("/app")}
    >
      <App />
    </ClerkProvider>
  </StrictMode>
);
