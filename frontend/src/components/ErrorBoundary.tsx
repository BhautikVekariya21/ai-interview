import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorBoundaryProps {
  children: ReactNode;
  /** Optional custom fallback; receives the reset handler */
  fallback?: (reset: () => void) => ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * App-wide error boundary. Renders a designed, on-brand fallback instead of a
 * white-screen crash. Logic-preserving: it only catches render errors.
 */
export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Surface for logging/telemetry; keep console for local debugging.
    console.error("ErrorBoundary caught:", error, info);
  }

  reset = (): void => this.setState({ hasError: false, error: null });

  render(): ReactNode {
    if (!this.state.hasError) return this.props.children;
    if (this.props.fallback) return this.props.fallback(this.reset);

    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center px-6 text-center">
        <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl border border-border bg-destructive/10 text-destructive">
          <AlertTriangle className="h-6 w-6" />
        </div>
        <h2 className="text-h2 text-foreground">Something went wrong</h2>
        <p className="mt-2 max-w-md text-body text-muted-foreground">
          An unexpected error interrupted this view. You can retry — your session is preserved.
        </p>
        <Button onClick={this.reset} variant="brand" className="mt-6 rounded-xl">
          Try again
        </Button>
      </div>
    );
  }
}
