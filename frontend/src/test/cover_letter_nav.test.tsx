import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MemoryRouter, useLocation } from "react-router-dom";

vi.mock("@/components/AuthProvider", () => ({
  useAuth: () => ({
    isAuthenticated: false,
    user: null,
    logout: vi.fn(),
  }),
}));

import Navbar from "@/components/Navbar";


function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname}</div>;
}


describe("Navbar cover letter navigation", () => {
  it("shows the cover letter tool in Prep Tools and routes to it", () => {
    const onPageChange = vi.fn();

    render(
      <MemoryRouter initialEntries={["/app"]}>
        <Navbar activePage="upload" onPageChange={onPageChange} isOnline />
        <LocationProbe />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: /prep tools/i }));

    const coverLetterButton = screen.getByRole("button", {
      name: /cover letter/i,
    });
    expect(coverLetterButton).toBeInTheDocument();

    fireEvent.click(coverLetterButton);

    expect(onPageChange).toHaveBeenCalledWith("cover-letter-generator");
    expect(screen.getByTestId("location")).toHaveTextContent("/app/cover-letter-generator");
  });
});
